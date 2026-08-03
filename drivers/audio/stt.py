"""Portable speech-to-text clients for MicroPython and CPython."""

import json
import struct
import time

from audiodev import AudioFormat


PCM_16000 = AudioFormat(16000, 1, 16)


class Recording:
    """Captured raw PCM and its format."""

    def __init__(self, pcm, audio_format=PCM_16000):
        self.pcm = pcm
        self.format = audio_format

    def wav(self):
        return wav_bytes(self.pcm, self.format)


class Transcript:
    """Normalized transcription result."""

    def __init__(self, text, *, language=None, duration=None, segments=None, words=None):
        self.text = (text or "").strip()
        self.language = language
        self.duration = duration
        self.segments = segments
        self.words = words


class STTRequest:
    """Provider-neutral HTTP request description."""

    def __init__(self, url, headers, body):
        self.url, self.headers, self.body = url, headers, body


def _pack_u16(value):
    return struct.pack("<H", value)


def _pack_u32(value):
    return struct.pack("<I", value)


def wav_header(audio_format, data_length):
    """Return a canonical 44-byte PCM WAV header."""
    if not audio_format.signed or audio_format.byteorder != "little":
        raise ValueError("WAV capture requires signed little-endian PCM")
    if data_length % audio_format.frame_size:
        raise ValueError("PCM data must contain complete frames")
    byte_rate = audio_format.rate * audio_format.frame_size
    return (
        b"RIFF"
        + _pack_u32(36 + data_length)
        + b"WAVEfmt "
        + _pack_u32(16)
        + _pack_u16(1)
        + _pack_u16(audio_format.channels)
        + _pack_u32(audio_format.rate)
        + _pack_u32(byte_rate)
        + _pack_u16(audio_format.frame_size)
        + _pack_u16(audio_format.bits)
        + b"data"
        + _pack_u32(data_length)
    )


def wav_bytes(pcm, audio_format):
    pcm = bytes(pcm)
    return wav_header(audio_format, len(pcm)) + pcm


def _field(boundary, name, value):
    return (
        b"--" + boundary + b"\r\n"
        + ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode()
        + str(value).encode() + b"\r\n"
    )


def multipart_form(fields, filename, content, *, content_type="audio/wav", boundary=None):
    """Build a fixed-length multipart body accepted by MicroPython requests."""
    boundary = (boundary or "pydevices-stt-7MA4YWxkTrZu0gW").encode()
    parts = [_field(boundary, name, value) for name, value in fields]
    parts.append(
        b"--" + boundary + b"\r\n"
        + ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode()
        + ("Content-Type: %s\r\n\r\n" % content_type).encode()
        + content + b"\r\n"
    )
    parts.append(b"--" + boundary + b"--\r\n")
    return b"".join(parts), boundary.decode()


class GroqSTT:
    """Groq Whisper transcription adapter."""

    def __init__(self, api_key, *, model="whisper-large-v3-turbo", base_url="https://api.groq.com/openai/v1"):
        self.api_key, self.model = api_key, model
        self.base_url = base_url.rstrip("/")

    def request(self, recording, *, language=None, prompt=None, temperature=None, response_format="verbose_json"):
        if not isinstance(recording, Recording):
            recording = Recording(recording)
        fields = [("model", self.model), ("response_format", response_format)]
        if language:
            fields.append(("language", language))
        if prompt:
            fields.append(("prompt", prompt))
        if temperature is not None:
            fields.append(("temperature", temperature))
        body, boundary = multipart_form(fields, "recording.wav", recording.wav())
        return STTRequest(
            self.base_url + "/audio/transcriptions",
            {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "multipart/form-data; boundary=" + boundary,
                "Content-Length": str(len(body)),
            },
            body,
        )

    def parse(self, value):
        if isinstance(value, str):
            return Transcript(value)
        return Transcript(
            value.get("text", ""),
            language=value.get("language"),
            duration=value.get("duration"),
            segments=value.get("segments"),
            words=value.get("words"),
        )


class RequestsTransport:
    def __init__(self, module=None):
        if module is None:
            try:
                import requests as module
            except ImportError:
                import urequests as module
        self.module = module

    def post(self, request):
        response = self.module.post(request.url, headers=request.headers, data=request.body)
        status = getattr(response, "status_code", 200)
        if status < 200 or status >= 300:
            detail = getattr(response, "text", "")
            response.close()
            raise OSError("STT HTTP %d: %s" % (status, detail))
        return response


class STTClient:
    """Record PCM input and transcribe it through a provider adapter."""

    def __init__(self, provider, *, transport=None, chunk_size=4096):
        self.provider = provider
        self.transport = transport or RequestsTransport()
        self.chunk_size = int(chunk_size)

    def record(self, audio_input, *, duration_ms=None, while_pressed=None, max_ms=30000):
        if duration_ms is None and while_pressed is None:
            raise ValueError("duration_ms or while_pressed is required")
        fmt = audio_input.format
        size = self.chunk_size - self.chunk_size % fmt.frame_size
        buf, chunks = bytearray(size), []
        target_bytes = None
        if duration_ms is not None:
            target_bytes = fmt.rate * fmt.frame_size * int(duration_ms) // 1000
            target_bytes -= target_bytes % fmt.frame_size
        try:
            audio_input.open()
            start = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.monotonic() * 1000)
            total = 0
            while True:
                elapsed = (time.ticks_diff(time.ticks_ms(), start) if hasattr(time, "ticks_diff") else int(time.monotonic() * 1000) - start)
                if elapsed >= max_ms or (target_bytes is not None and total >= target_bytes):
                    break
                if while_pressed is not None and not while_pressed():
                    break
                view = buf
                if target_bytes is not None:
                    view = memoryview(buf)[: min(len(buf), target_bytes - total)]
                count = audio_input.readinto(view)
                if count:
                    chunks.append(bytes(memoryview(buf)[:count]))
                    total += count
        finally:
            audio_input.close()
        return Recording(b"".join(chunks), fmt)

    def transcribe(self, recording, **options):
        request = self.provider.request(recording, **options)
        response = self.transport.post(request)
        try:
            if hasattr(response, "json"):
                value = response.json()
            else:
                raw = response.read()
                value = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
        finally:
            response.close()
        result = self.provider.parse(value)
        if not result.text:
            raise ValueError("STT response contained no transcript")
        return result

    def listen(self, audio_input, **options):
        record_options = {}
        for name in ("duration_ms", "while_pressed", "max_ms"):
            if name in options:
                record_options[name] = options.pop(name)
        return self.transcribe(self.record(audio_input, **record_options), **options)
