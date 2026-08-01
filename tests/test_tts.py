from pathlib import Path
import base64
import json
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))

from audiodev import AudioFormat  # noqa: E402
from tts import AzureTTS, ElevenLabsTTS, GeminiTTS, GoogleCloudTTS, OpenAITTS, TTSClient  # noqa: E402


class Response:
    def __init__(self, data, as_json=False):
        self.data, self.offset, self.closed, self.as_json = data, 0, False, as_json
        self.raw = self
        self.status_code = 200

    def read(self, size=-1):
        if size < 0:
            size = len(self.data) - self.offset
        value = self.data[self.offset:self.offset + size]
        self.offset += len(value)
        return value

    def json(self):
        return self.data if self.as_json else json.loads(self.data)

    def close(self):
        self.closed = True


class Transport:
    def __init__(self, response):
        self.response, self.request = response, None

    def post(self, request):
        self.request = request
        return self.response


class ProviderTests(unittest.TestCase):
    def test_openai_stream_and_play(self):
        transport = Transport(Response(b"abcdefgh"))
        client = TTSClient(OpenAITTS("secret"), transport=transport, chunk_size=3)
        self.assertEqual(client.synthesize("hello"), b"abcdefgh")
        body = json.loads(transport.request.body)
        self.assertEqual((body["response_format"], body["voice"]), ("pcm", "alloy"))
        self.assertEqual(transport.request.headers["Authorization"], "Bearer secret")

    def test_elevenlabs_request(self):
        request = ElevenLabsTTS("key", "voice/id", sample_rate=16000).request("hello")
        self.assertIn("voice%2Fid/stream?output_format=pcm_16000", request.url)
        self.assertEqual(request.audio_format, AudioFormat(16000, 1, 16))

    def test_azure_escapes_ssml_and_selects_raw(self):
        request = AzureTTS("key", "westus", sample_rate=48000).request("a < b")
        self.assertIn(b"a &lt; b", request.body)
        self.assertEqual(request.headers["X-Microsoft-OutputFormat"], "raw-48khz-16bit-mono-pcm")

    def test_google_decodes_base64_and_removes_wav(self):
        pcm = b"\x01\x00\x02\x00"
        wav = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 24000, 48000, 2, 16) + b"data" + struct.pack("<I", len(pcm)) + pcm
        response = Response({"audioContent": base64.b64encode(wav).decode()}, as_json=True)
        transport = Transport(response)
        self.assertEqual(TTSClient(GoogleCloudTTS("key"), transport=transport).synthesize("hi"), pcm)
        self.assertTrue(response.closed)

    def test_gemini_decodes_inline_pcm(self):
        value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": base64.b64encode(b"pcm").decode()}}]}}]}
        client = TTSClient(GeminiTTS("key"), transport=Transport(Response(value, as_json=True)))
        self.assertEqual(client.synthesize("hi", instructions="cheerful"), b"pcm")

    def test_speak_checks_format(self):
        class Output:
            format = AudioFormat(16000, 1, 16)
        client = TTSClient(OpenAITTS("key"), transport=Transport(Response(b"pcm")))
        with self.assertRaises(ValueError):
            client.speak("hi", Output())


if __name__ == "__main__":
    unittest.main()
