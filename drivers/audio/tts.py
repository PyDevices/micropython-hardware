"""Portable streaming text-to-speech clients for MicroPython and CPython.

The module deliberately depends only on ``json`` and an HTTP client.  A
requests-compatible transport may be injected for constrained ports and tests.
All provider defaults produce signed, little-endian, 16-bit mono PCM.
"""

import binascii
import json

try:
    from urllib.parse import quote
except ImportError:  # MicroPython
    def quote(value, safe=""):
        out = []
        for byte in value.encode():
            char = chr(byte)
            if char.isalnum() or char in "-_.~" or char in safe:
                out.append(char)
            else:
                out.append("%%%02X" % byte)
        return "".join(out)

from audiodev import AudioFormat


PCM_24000 = AudioFormat(24000, 1, 16)


class TTSRequest:
    """Provider-neutral HTTP request description."""

    def __init__(self, url, headers, body, *, response="audio", audio_format=PCM_24000):
        self.url = url
        self.headers = headers
        self.body = body
        self.response = response
        self.audio_format = audio_format


class SpeechStream:
    """Iterable speech bytes with their decoded PCM format."""

    def __init__(self, chunks, audio_format, close=None):
        self._chunks = chunks
        self.format = audio_format
        self._close = close

    def __iter__(self):
        return iter(self._chunks)

    def close(self):
        if self._close is not None:
            close, self._close = self._close, None
            close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class _Provider:
    def _json_request(self, url, headers, value, **kwargs):
        headers = dict(headers)
        headers["Content-Type"] = "application/json"
        return TTSRequest(url, headers, json.dumps(value).encode(), **kwargs)


class OpenAITTS(_Provider):
    """OpenAI ``/v1/audio/speech`` adapter (raw 24 kHz PCM by default)."""

    def __init__(self, api_key, *, model="gpt-4o-mini-tts", voice="alloy", base_url="https://api.openai.com/v1"):
        self.api_key, self.model, self.voice = api_key, model, voice
        self.base_url = base_url.rstrip("/")

    def request(self, text, *, voice=None, instructions=None, speed=None, **unused):
        body = {"model": self.model, "voice": voice or self.voice, "input": text, "response_format": "pcm"}
        if instructions is not None:
            body["instructions"] = instructions
        if speed is not None:
            body["speed"] = speed
        return self._json_request(self.base_url + "/audio/speech", {"Authorization": "Bearer " + self.api_key}, body)


class ElevenLabsTTS(_Provider):
    """ElevenLabs streaming TTS adapter."""

    def __init__(self, api_key, voice, *, model="eleven_multilingual_v2", sample_rate=24000, base_url="https://api.elevenlabs.io/v1"):
        if sample_rate not in (16000, 22050, 24000, 44100):
            raise ValueError("unsupported ElevenLabs PCM sample rate")
        self.api_key, self.voice, self.model = api_key, voice, model
        self.sample_rate, self.base_url = sample_rate, base_url.rstrip("/")

    def request(self, text, *, voice=None, voice_settings=None, **unused):
        voice = quote(voice or self.voice, safe="")
        url = "%s/text-to-speech/%s/stream?output_format=pcm_%d" % (self.base_url, voice, self.sample_rate)
        body = {"text": text, "model_id": self.model}
        if voice_settings is not None:
            body["voice_settings"] = voice_settings
        fmt = AudioFormat(self.sample_rate, 1, 16)
        return self._json_request(url, {"xi-api-key": self.api_key}, body, audio_format=fmt)


def _xml(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")


class AzureTTS(_Provider):
    """Azure Speech REST adapter using raw mono PCM."""

    def __init__(self, api_key, region, *, voice="en-US-AvaMultilingualNeural", language="en-US", sample_rate=24000, endpoint=None):
        if sample_rate not in (8000, 16000, 22050, 24000, 44100, 48000):
            raise ValueError("unsupported Azure PCM sample rate")
        self.api_key, self.voice, self.language, self.sample_rate = api_key, voice, language, sample_rate
        self.endpoint = endpoint or "https://%s.tts.speech.microsoft.com/cognitiveservices/v1" % region

    def request(self, text, *, voice=None, language=None, ssml=False, **unused):
        language, voice = language or self.language, voice or self.voice
        body = text if ssml else '<speak version="1.0" xml:lang="%s"><voice name="%s">%s</voice></speak>' % (_xml(language), _xml(voice), _xml(text))
        headers = {"Ocp-Apim-Subscription-Key": self.api_key, "Content-Type": "application/ssml+xml", "User-Agent": "micropython-hardware", "X-Microsoft-OutputFormat": "raw-%dkhz-16bit-mono-pcm" % (self.sample_rate // 1000)}
        # Azure spells the 22.05/44.1 kHz values without a decimal point.
        if self.sample_rate in (22050, 44100):
            headers["X-Microsoft-OutputFormat"] = "raw-%dhz-16bit-mono-pcm" % self.sample_rate
        return TTSRequest(self.endpoint, headers, body.encode(), audio_format=AudioFormat(self.sample_rate, 1, 16))


class GoogleCloudTTS(_Provider):
    """Google Cloud Text-to-Speech REST adapter.

    LINEAR16 is returned inside JSON as a base64 WAV stream.  The small WAV
    header is removed by :class:`TTSClient`, yielding raw PCM to callers.
    """

    def __init__(self, api_key, *, voice="en-US-Chirp3-HD-Achernar", language="en-US", sample_rate=24000, endpoint="https://texttospeech.googleapis.com/v1/text:synthesize"):
        self.api_key, self.voice, self.language = api_key, voice, language
        self.sample_rate, self.endpoint = sample_rate, endpoint

    def request(self, text, *, voice=None, language=None, **unused):
        body = {"input": {"text": text}, "voice": {"languageCode": language or self.language, "name": voice or self.voice}, "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": self.sample_rate}}
        url = self.endpoint + ("&" if "?" in self.endpoint else "?") + "key=" + quote(self.api_key)
        return self._json_request(url, {}, body, response="google-wav", audio_format=AudioFormat(self.sample_rate, 1, 16))


class GeminiTTS(_Provider):
    """Gemini native TTS adapter (base64 raw 24 kHz PCM response)."""

    def __init__(self, api_key, *, model="gemini-2.5-flash-preview-tts", voice="Kore", base_url="https://generativelanguage.googleapis.com/v1beta"):
        self.api_key, self.model, self.voice, self.base_url = api_key, model, voice, base_url.rstrip("/")

    def request(self, text, *, voice=None, instructions=None, **unused):
        prompt = (instructions + "\n" + text) if instructions else text
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice or self.voice}}}}}
        url = "%s/models/%s:generateContent?key=%s" % (self.base_url, quote(self.model, safe=""), quote(self.api_key, safe=""))
        return self._json_request(url, {}, body, response="gemini-pcm")


class RequestsTransport:
    """Minimal adapter for CPython requests or MicroPython requests/urequests."""

    def __init__(self, module=None):
        if module is None:
            try:
                import requests as module
            except ImportError:
                import urequests as module
        self.module = module

    def post(self, request):
        try:
            response = self.module.post(request.url, headers=request.headers, data=request.body, stream=True)
        except TypeError:  # urequests has no stream keyword
            response = self.module.post(request.url, headers=request.headers, data=request.body)
        status = getattr(response, "status_code", 200)
        if status < 200 or status >= 300:
            detail = getattr(response, "text", "")
            response.close()
            raise OSError("TTS HTTP %d: %s" % (status, detail))
        return response


def _read_chunks(response, size):
    raw = getattr(response, "raw", response)
    while True:
        chunk = raw.read(size)
        if not chunk:
            break
        yield chunk


def _wav_pcm(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Google LINEAR16 response is not WAV")
    offset = 12
    while offset + 8 <= len(data):
        size = int.from_bytes(data[offset + 4:offset + 8], "little")
        if data[offset:offset + 4] == b"data":
            return data[offset + 8:offset + 8 + size]
        offset += 8 + size + (size & 1)
    raise ValueError("WAV data chunk is missing")


class TTSClient:
    """Universal synthesize/stream/play facade around a provider adapter."""

    def __init__(self, provider, *, transport=None, chunk_size=2048):
        self.provider = provider
        self.transport = transport or RequestsTransport()
        self.chunk_size = int(chunk_size)

    def stream(self, text, **options):
        request = self.provider.request(text, **options)
        response = self.transport.post(request)
        if request.response == "audio":
            return SpeechStream(_read_chunks(response, self.chunk_size), request.audio_format, response.close)
        try:
            value = response.json() if hasattr(response, "json") else json.loads(response.read())
            if request.response == "google-wav":
                data = _wav_pcm(binascii.a2b_base64(value["audioContent"]))
            else:
                data = binascii.a2b_base64(value["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        finally:
            response.close()
        chunks = (data[i:i + self.chunk_size] for i in range(0, len(data), self.chunk_size))
        return SpeechStream(chunks, request.audio_format)

    def synthesize(self, text, **options):
        stream = self.stream(text, **options)
        try:
            return b"".join(stream)
        finally:
            stream.close()

    def speak(self, text, output, **options):
        stream = self.stream(text, **options)
        if getattr(output, "format", stream.format) != stream.format:
            stream.close()
            raise ValueError("audio output format does not match TTS format")
        try:
            total = 0
            for chunk in stream:
                total += output.write(chunk)
            drain = getattr(output, "drain", None)
            if drain is not None:
                drain()
            return total
        finally:
            stream.close()
