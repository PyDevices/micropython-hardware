from pathlib import Path
import json
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))

from audiodev import AudioFormat, PCMInput  # noqa: E402
from stt import GroqSTT, Recording, STTClient, wav_bytes  # noqa: E402


class Response:
    status_code = 200

    def __init__(self, value):
        self.value, self.closed = value, False

    def json(self):
        return self.value

    def close(self):
        self.closed = True


class Transport:
    def __init__(self, response):
        self.response, self.request = response, None

    def post(self, request):
        self.request = request
        return self.response


class STTTests(unittest.TestCase):
    def test_wav_header(self):
        pcm = b"\x01\x00\x02\x00"
        wav = wav_bytes(pcm, AudioFormat(24000, 1, 16))
        self.assertEqual(wav[:4], b"RIFF")
        self.assertEqual(struct.unpack("<I", wav[24:28])[0], 24000)
        self.assertEqual(struct.unpack("<I", wav[40:44])[0], len(pcm))
        self.assertEqual(wav[44:], pcm)

    def test_groq_multipart_and_parse(self):
        response = Response({"text": " hello ", "language": "en", "duration": 1.5})
        transport = Transport(response)
        client = STTClient(GroqSTT("secret"), transport=transport)
        result = client.transcribe(Recording(b"\0\0"), language="en")
        request = transport.request
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.language, "en")
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        self.assertEqual(int(request.headers["Content-Length"]), len(request.body))
        self.assertIn(b'name="model"\r\n\r\nwhisper-large-v3-turbo', request.body)
        self.assertIn(b'name="language"\r\n\r\nen', request.body)
        self.assertIn(b"RIFF", request.body)
        self.assertTrue(response.closed)

    def test_record_closes_input(self):
        class Stream:
            def __init__(self):
                self.closed = False

            def readinto(self, buf):
                buf[:] = b"\x01\x00" * (len(buf) // 2)
                return len(buf)

            def close(self):
                self.closed = True

        stream = Stream()
        audio_input = PCMInput(stream, AudioFormat(16000, 1, 16))
        states = iter((True, False))
        recording = STTClient(GroqSTT("x"), chunk_size=32).record(
            audio_input, while_pressed=lambda: next(states)
        )
        self.assertEqual(recording.format, audio_input.format)
        self.assertEqual(len(recording.pcm), 32)
        self.assertTrue(stream.closed)

    def test_empty_transcript_is_error(self):
        client = STTClient(GroqSTT("x"), transport=Transport(Response({"text": ""})))
        with self.assertRaises(ValueError):
            client.transcribe(Recording(b"\0\0"))


if __name__ == "__main__":
    unittest.main()
