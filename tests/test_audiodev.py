import asyncio
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))

from audiodev import AudioFormat, AudioSession, PCMInput, PCMOutput, ToneOutput  # noqa: E402


class FakeOutput:
    def __init__(self, partial=None):
        self.data = bytearray()
        self.partial = partial
        self.open_count = 0
        self.close_count = 0
        self.drained = False

    def open(self):
        self.open_count += 1

    def write(self, buf):
        count = len(buf) if self.partial is None else min(self.partial, len(buf))
        self.data.extend(buf[:count])
        return count

    async def awrite(self, buf):
        await asyncio.sleep(0)
        return self.write(buf)

    def drain(self):
        self.drained = True

    async def adrain(self):
        await asyncio.sleep(0)
        self.drained = True

    def close(self):
        self.close_count += 1


class FakeInput:
    def __init__(self, data):
        self.data = bytes(data)
        self.closed = False

    def readinto(self, buf):
        count = min(len(buf), len(self.data))
        buf[:count] = self.data[:count]
        return count

    async def areadinto(self, buf):
        await asyncio.sleep(0)
        return self.readinto(buf)

    def close(self):
        self.closed = True


class FakeTone:
    def __init__(self):
        self.frequency = None
        self.level = None
        self.stopped = False

    def play(self, frequency, level):
        self.frequency = frequency
        self.level = level
        self.stopped = False

    def stop(self):
        self.stopped = True

    def close(self):
        pass


class AudioFormatTests(unittest.TestCase):
    def test_format(self):
        fmt = AudioFormat(16000, 2, 16)
        self.assertEqual(fmt.frame_size, 4)
        self.assertEqual(fmt, AudioFormat(16000, 2, 16))

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            AudioFormat(0, 2, 16)
        with self.assertRaises(ValueError):
            AudioFormat(16000, 2, 24)


class PCMOutputTests(unittest.TestCase):
    def setUp(self):
        self.fmt = AudioFormat(16000, 1, 16)

    def test_partial_writes_and_lifecycle(self):
        stream = FakeOutput(partial=2)
        output = PCMOutput(stream, self.fmt)
        self.assertEqual(output.write(b"\x01\x00\x02\x00"), 4)
        self.assertEqual(stream.data, b"\x01\x00\x02\x00")
        output.open()
        self.assertEqual(stream.open_count, 1)
        output.close()
        output.close()
        self.assertEqual(stream.close_count, 1)

    def test_software_volume_and_mute(self):
        stream = FakeOutput()
        output = PCMOutput(stream, self.fmt)
        output.set_volume(50)
        output.write((1000).to_bytes(2, "little", signed=True))
        self.assertEqual(int.from_bytes(stream.data, "little", signed=True), 500)
        stream.data.clear()
        output.mute()
        output.write((1000).to_bytes(2, "little", signed=True))
        self.assertEqual(stream.data, b"\0\0")
        self.assertEqual(output.volume, 50)

    def test_hardware_controls(self):
        calls = []
        output = PCMOutput(
            FakeOutput(),
            self.fmt,
            set_hardware_volume=lambda value: calls.append(("volume", value)),
            set_hardware_mute=lambda value: calls.append(("mute", value)),
        )
        output.set_volume(30)
        output.open()
        output.mute(True)
        self.assertIn(("volume", 30), calls)
        self.assertIn(("mute", True), calls)

    def test_frame_validation(self):
        with self.assertRaises(ValueError):
            PCMOutput(FakeOutput(), self.fmt).write(b"x")

    def test_async_output(self):
        async def run():
            stream = FakeOutput(partial=1)
            output = PCMOutput(stream, self.fmt)
            self.assertEqual(await output.awrite(b"\x01\x00"), 2)
            self.assertEqual(stream.data, b"\x01\x00")
            await output.adrain()
            self.assertTrue(stream.drained)

        asyncio.run(run())


class PCMInputTests(unittest.TestCase):
    def setUp(self):
        self.fmt = AudioFormat(16000, 1, 16)

    def test_capture_gain_and_mute(self):
        source = (1000).to_bytes(2, "little", signed=True)
        capture = PCMInput(FakeInput(source), self.fmt)
        capture.set_gain(50)
        buf = bytearray(2)
        self.assertEqual(capture.readinto(buf), 2)
        self.assertEqual(int.from_bytes(buf, "little", signed=True), 500)
        capture.mute()
        capture.readinto(buf)
        self.assertEqual(buf, b"\0\0")

    def test_async_capture(self):
        async def run():
            capture = PCMInput(FakeInput(b"\x01\0"), self.fmt)
            buf = bytearray(2)
            self.assertEqual(await capture.areadinto(buf), 2)
            self.assertEqual(buf, b"\x01\0")

        asyncio.run(run())


class SessionTests(unittest.TestCase):
    def test_half_duplex_conflict_and_shared_codec(self):
        codec = object()
        session = AudioSession(lambda: codec, duplex=False)
        output = PCMOutput(FakeOutput(), AudioFormat(16000, 1, 16), session=session)
        capture = PCMInput(FakeInput(b"\0\0"), AudioFormat(16000, 1, 16), session=session)
        output.open()
        self.assertIs(output.codec, codec)
        with self.assertRaises(OSError):
            capture.open()
        output.close()
        capture.open()
        self.assertIs(capture.codec, codec)


class ToneTests(unittest.TestCase):
    def test_tone_and_async_stop(self):
        async def run():
            stream = FakeTone()
            tone = ToneOutput(stream)
            tone.set_volume(25)
            tone.play(440)
            self.assertEqual((stream.frequency, stream.level), (440, 25))
            await tone.aplay(880, 1)
            self.assertTrue(stream.stopped)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
