import asyncio
from pathlib import Path
import sys
import unittest

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401

from audiodev import (  # noqa: E402
    AudioFormat,
    AudioSession,
    PCMInput,
    PCMOutput,
    ToneOutput,
)
from audiodev.i2s_audio import I2SPCMInput, I2SPCMOutput  # noqa: E402
from audiodev.pwm_tone import PWMToneOutput  # noqa: E402


class FakePCMOutput(PCMOutput):
    def __init__(self, fmt, *, partial=None, **kwargs):
        super().__init__(fmt, **kwargs)
        self.data = bytearray()
        self.partial = partial
        self.open_count = 0
        self.close_count = 0
        self.drained = False

    def _open(self):
        self.open_count += 1

    def _write(self, buf):
        count = len(buf) if self.partial is None else min(self.partial, len(buf))
        self.data.extend(buf[:count])
        return count

    async def _awrite(self, buf):
        await asyncio.sleep(0)
        return self._write(buf)

    def _drain(self):
        self.drained = True

    async def _adrain(self):
        await asyncio.sleep(0)
        self.drained = True

    def _close(self):
        self.close_count += 1


class FakePCMInput(PCMInput):
    def __init__(self, fmt, data, **kwargs):
        super().__init__(fmt, **kwargs)
        self._source = bytes(data)
        self.closed = False

    def _readinto(self, buf):
        count = min(len(buf), len(self._source))
        buf[:count] = self._source[:count]
        return count

    async def _areadinto(self, buf):
        await asyncio.sleep(0)
        return self._readinto(buf)

    def _close(self):
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
        output = FakePCMOutput(self.fmt, partial=2)
        self.assertEqual(output.write(b"\x01\x00\x02\x00"), 4)
        self.assertEqual(output.data, b"\x01\x00\x02\x00")
        output.open()
        self.assertEqual(output.open_count, 1)
        output.close()
        output.close()
        self.assertEqual(output.close_count, 1)

    def test_software_volume_and_mute(self):
        output = FakePCMOutput(self.fmt)
        output.set_volume(50)
        output.write((1000).to_bytes(2, "little", signed=True))
        self.assertEqual(int.from_bytes(output.data, "little", signed=True), 500)
        output.data.clear()
        output.mute()
        output.write((1000).to_bytes(2, "little", signed=True))
        self.assertEqual(output.data, b"\0\0")
        self.assertEqual(output.volume, 50)

    def test_hardware_controls(self):
        calls = []
        output = FakePCMOutput(
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
            FakePCMOutput(self.fmt).write(b"x")

    def test_queue_helpers_exist_on_the_device(self):
        output = FakePCMOutput(self.fmt)
        self.assertEqual(output.service(), None)
        self.assertEqual(output.queued_size(), 0)
        self.assertFalse(output.is_active())
        self.assertEqual(output.clear(), None)

    def test_async_output(self):
        async def run():
            output = FakePCMOutput(self.fmt, partial=1)
            self.assertEqual(await output.awrite(b"\x01\x00"), 2)
            self.assertEqual(output.data, b"\x01\x00")
            await output.adrain()
            self.assertTrue(output.drained)

        asyncio.run(run())


class PCMInputTests(unittest.TestCase):
    def setUp(self):
        self.fmt = AudioFormat(16000, 1, 16)

    def test_capture_gain_and_mute(self):
        source = (1000).to_bytes(2, "little", signed=True)
        capture = FakePCMInput(self.fmt, source)
        capture.set_gain(50)
        buf = bytearray(2)
        self.assertEqual(capture.readinto(buf), 2)
        self.assertEqual(int.from_bytes(buf, "little", signed=True), 500)
        capture.mute()
        capture.readinto(buf)
        self.assertEqual(buf, b"\0\0")

    def test_async_capture(self):
        async def run():
            capture = FakePCMInput(self.fmt, b"\x01\0")
            buf = bytearray(2)
            self.assertEqual(await capture.areadinto(buf), 2)
            self.assertEqual(buf, b"\x01\0")

        asyncio.run(run())


class SessionTests(unittest.TestCase):
    def test_half_duplex_conflict_and_shared_codec(self):
        codec = object()
        session = AudioSession(lambda: codec, duplex=False)
        output = FakePCMOutput(AudioFormat(16000, 1, 16), session=session)
        capture = FakePCMInput(AudioFormat(16000, 1, 16), b"\0\0", session=session)
        output.open()
        self.assertIs(output.codec, codec)
        with self.assertRaises(OSError):
            capture.open()
        output.close()
        capture.open()
        self.assertIs(capture.codec, codec)


class FakeI2S:
    def __init__(self):
        self.written = bytearray()
        self.closed = False

    def write(self, data):
        self.written.extend(data)
        return len(data)

    def readinto(self, buf):
        buf[:] = b"\x01\x00" * (len(buf) // 2)
        return len(buf)

    def deinit(self):
        self.closed = True


class I2SAdapterTests(unittest.TestCase):
    def test_output_and_input_wrap_machine_i2s(self):
        fmt = AudioFormat(16000, 1, 16)
        i2s = FakeI2S()
        out = I2SPCMOutput(i2s, fmt)
        self.assertIsInstance(out, PCMOutput)
        self.assertEqual(out.write(b"\x02\x00\x03\x00"), 4)
        self.assertEqual(bytes(i2s.written), b"\x02\x00\x03\x00")
        self.assertEqual(out.service(), None)
        self.assertEqual(out.queued_size(), 0)
        out.close()
        self.assertTrue(i2s.closed)

        capture = FakeI2S()
        inp = I2SPCMInput(capture, fmt)
        self.assertIsInstance(inp, PCMInput)
        buf = bytearray(2)
        self.assertEqual(inp.readinto(buf), 2)
        inp.close()
        self.assertTrue(capture.closed)


class ToneTests(unittest.TestCase):
    def test_tone_and_async_stop(self):
        async def run():
            stream = FakeTone()
            power = []
            tone = PWMToneOutput(stream, power=power.append)
            self.assertIsInstance(tone, ToneOutput)
            tone.set_volume(25)
            tone.play(440)
            self.assertEqual((stream.frequency, stream.level), (440, 25))
            await tone.aplay(880, 1)
            self.assertTrue(stream.stopped)
            tone.close()
            self.assertEqual(power, [True, False])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
