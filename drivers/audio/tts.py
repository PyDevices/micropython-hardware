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
            if (
                "a" <= char <= "z"
                or "A" <= char <= "Z"
                or "0" <= char <= "9"
                or char in "-_.~"
                or char in safe
            ):
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

    def __init__(
        self,
        api_key="not-needed",
        *,
        model="gpt-4o-mini-tts",
        voice="alloy",
        base_url="https://api.openai.com/v1",
        response_format="pcm",
        audio_format=PCM_24000,
        response="audio",
    ):
        self.api_key, self.model, self.voice = api_key, model, voice
        self.base_url = base_url.rstrip("/")
        self.response_format = response_format
        self.audio_format = audio_format
        self.response = response

    def request(self, text, *, voice=None, instructions=None, speed=None, **unused):
        body = {
            "model": self.model,
            "voice": voice or self.voice,
            "input": text,
            "response_format": self.response_format,
        }
        if instructions is not None:
            body["instructions"] = instructions
        if speed is not None:
            body["speed"] = speed
        return self._json_request(
            self.base_url + "/audio/speech",
            {"Authorization": "Bearer " + self.api_key},
            body,
            response=self.response,
            audio_format=self.audio_format,
        )


# Kokoro-82M local OpenAI-compatible server (:8880, raw PCM 24 kHz).
# https://huggingface.co/hexgrad/Kokoro-82M
# Host setup + MicroPython streaming notes:
#   https://pydevices.github.io/micropython-hardware/audio.html#local-kokoro-tts
# Default: http://127.0.0.1:8880/v1 — on MCU set secrets.KOKORO_BASE_URL to the host LAN URL.

KOKORO_VOICES = (
    ("af_heart", "US Female Warm"),
    ("af_bella", "US Female Expressive"),
    ("af_nicole", "US Female Friendly"),
    ("af_aoede", "US Female"),
    ("af_kore", "US Female"),
    ("af_sarah", "US Female Conversational"),
    ("af_nova", "US Female Clear"),
    ("af_sky", "US Female Neutral"),
    ("af_alloy", "US Female Balanced"),
    ("af_jessica", "US Female Energetic"),
    ("af_river", "US Female Calm"),
    ("am_adam", "US Male Deep"),
    ("am_michael", "US Male Clear"),
    ("am_echo", "US Male Neutral"),
    ("am_eric", "US Male Authoritative"),
    ("am_fenrir", "US Male Distinctive"),
    ("am_liam", "US Male Conversational"),
    ("am_onyx", "US Male Rich"),
    ("am_puck", "US Male Expressive"),
    ("am_santa", "US Male Warm"),
    ("bf_emma", "UK Female"),
    ("bf_isabella", "UK Female"),
    ("bf_alice", "UK Female"),
    ("bf_lily", "UK Female"),
    ("bm_george", "UK Male"),
    ("bm_fable", "UK Male"),
    ("bm_daniel", "UK Male"),
    ("bm_lewis", "UK Male"),
)


class KokoroTTS(OpenAITTS):
    """Local Kokoro-82M via OpenAI-compatible ``/v1/audio/speech`` (PCM 24 kHz).

    Expects a host that streams raw PCM. For MicroPython play-while-generating,
    run the server with uvicorn ``--http h11`` (HTTP/1.0 clients reject chunked
    transfer). See docs/audio.md § Local Kokoro TTS.
    """

    def __init__(
        self,
        *,
        voice="af_heart",
        base_url="http://127.0.0.1:8880/v1",
        api_key="not-needed",
    ):
        super().__init__(
            api_key,
            model="kokoro",
            voice=voice,
            base_url=base_url,
            response_format="pcm",
            audio_format=PCM_24000,
            response="audio",
        )

    @staticmethod
    def voices():
        return KOKORO_VOICES

    @staticmethod
    def voice_label(name, description=None):
        if description is None:
            for voice_name, desc in KOKORO_VOICES:
                if voice_name == name:
                    description = desc
                    break
        if description:
            return "%s - %s" % (name, description)
        return name

    @staticmethod
    def voice_from_label(label):
        label = (label or "").strip()
        for sep in (" - ", " — "):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        return label

    def request(self, text, *, voice=None, speed=None, instructions=None, **unused):
        # Kokoro has no instructions field; optional style is not spoken.
        return OpenAITTS.request(self, text, voice=voice, speed=speed)


# Orpheus-3B via LM Studio + OpenAI speech bridge (default :5005).
# Model: https://huggingface.co/isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF
# Bridge e.g. https://github.com/TheLocalLab/Orpheus-FastAPI-LMStudio
# UI: pydisplay examples/tts_orpheus.py — docs/audio.md § Orpheus (LM Studio)

ORPHEUS_VOICES = (
    ("tara", "Female Conversational"),
    ("leah", "Female Warm"),
    ("jess", "Female Energetic"),
    ("leo", "Male Authoritative"),
    ("dan", "Male Friendly"),
    ("mia", "Female Professional"),
    ("zac", "Male Enthusiastic"),
    ("zoe", "Female Calm"),
)


class OrpheusTTS(OpenAITTS):
    """Orpheus-3B through the LM Studio FastAPI bridge (streaming PCM).

    Emotion tags belong in the spoken text
    (e.g. ``<laugh>``), not as a separate instructions field.
    """

    def __init__(
        self, *, voice="tara", base_url="http://127.0.0.1:5005/v1", api_key="not-needed"
    ):
        super().__init__(
            api_key,
            model="orpheus",
            voice=voice,
            base_url=base_url,
            response_format="pcm",
            audio_format=PCM_24000,
            response="audio",
        )

    @staticmethod
    def voices():
        return ORPHEUS_VOICES

    @staticmethod
    def voice_label(name, description=None):
        if description is None:
            for voice_name, desc in ORPHEUS_VOICES:
                if voice_name == name:
                    description = desc
                    break
        if description:
            return "%s - %s" % (name, description)
        return name

    @staticmethod
    def voice_from_label(label):
        label = (label or "").strip()
        for sep in (" - ", " — "):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        return label

    def request(self, text, *, voice=None, speed=None, instructions=None, **unused):
        # Optional style line is prepended so emotion tags / stage directions stay in-band.
        if instructions:
            text = instructions.strip() + "\n" + text
        return OpenAITTS.request(self, text, voice=voice, speed=speed)


GROQ_ORPHEUS_VOICES = (
    ("autumn", "Female"),
    ("diana", "Female"),
    ("hannah", "Female"),
    ("austin", "Male"),
    ("daniel", "Male"),
    ("troy", "Male"),
)


class GroqTTS(_Provider):
    """Groq-hosted Orpheus TTS adapter (24 kHz mono WAV response)."""

    def __init__(
        self,
        api_key,
        *,
        model="canopylabs/orpheus-v1-english",
        voice="autumn",
        base_url="https://api.groq.com/openai/v1",
    ):
        self.api_key, self.model, self.voice = api_key, model, voice
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def voices():
        return GROQ_ORPHEUS_VOICES

    @staticmethod
    def voice_label(name, description=None):
        if description is None:
            for voice_name, desc in GROQ_ORPHEUS_VOICES:
                if voice_name == name:
                    description = desc
                    break
        return "%s - %s" % (name, description) if description else name

    @staticmethod
    def voice_from_label(label):
        label = (label or "").strip()
        for sep in (" - ", " — "):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        return label

    def request(self, text, *, voice=None, instructions=None, **unused):
        if instructions:
            text = instructions.strip() + " " + text
        if len(text) > 200:
            raise ValueError("Groq Orpheus input is limited to 200 characters")
        return self._json_request(
            self.base_url + "/audio/speech",
            {"Authorization": "Bearer " + self.api_key},
            {
                "model": self.model,
                "input": text,
                "voice": voice or self.voice,
                "response_format": "wav",
            },
            response="wav",
            audio_format=PCM_24000,
        )


class ElevenLabsTTS(_Provider):
    """ElevenLabs streaming TTS adapter."""

    def __init__(
        self,
        api_key,
        voice,
        *,
        model="eleven_multilingual_v2",
        sample_rate=24000,
        base_url="https://api.elevenlabs.io/v1",
    ):
        if sample_rate not in (16000, 22050, 24000, 44100):
            raise ValueError("unsupported ElevenLabs PCM sample rate")
        self.api_key, self.voice, self.model = api_key, voice, model
        self.sample_rate, self.base_url = sample_rate, base_url.rstrip("/")

    def request(self, text, *, voice=None, voice_settings=None, **unused):
        voice = quote(voice or self.voice, safe="")
        url = "%s/text-to-speech/%s/stream?output_format=pcm_%d" % (
            self.base_url,
            voice,
            self.sample_rate,
        )
        body = {"text": text, "model_id": self.model}
        if voice_settings is not None:
            body["voice_settings"] = voice_settings
        fmt = AudioFormat(self.sample_rate, 1, 16)
        return self._json_request(
            url, {"xi-api-key": self.api_key}, body, audio_format=fmt
        )


DEEPGRAM_VOICES = (
    ("aura-2-thalia-en", "US Female Clear Energetic"),
    ("aura-2-andromeda-en", "US Female Casual Expressive"),
    ("aura-2-helena-en", "US Female Friendly Natural"),
    ("aura-2-apollo-en", "US Male Confident Casual"),
    ("aura-2-arcas-en", "US Male Smooth Clear"),
    ("aura-2-aries-en", "US Male Warm Energetic"),
)


class DeepgramTTS(_Provider):
    """Deepgram Aura REST adapter using streamed raw signed 16-bit PCM."""

    def __init__(
        self,
        token,
        *,
        voice="aura-2-thalia-en",
        sample_rate=24000,
        base_url="https://api.deepgram.com/v1",
    ):
        if sample_rate not in (8000, 16000, 24000, 32000, 48000):
            raise ValueError("unsupported Deepgram PCM sample rate")
        self.token, self.voice = token, voice
        self.sample_rate, self.base_url = sample_rate, base_url.rstrip("/")

    @staticmethod
    def voices():
        return DEEPGRAM_VOICES

    @staticmethod
    def voice_label(name, description=None):
        if description is None:
            for voice_name, desc in DEEPGRAM_VOICES:
                if voice_name == name:
                    description = desc
                    break
        return "%s - %s" % (name, description) if description else name

    @staticmethod
    def voice_from_label(label):
        label = (label or "").strip()
        for sep in (" - ", " — "):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        return label

    def request(self, text, *, voice=None, speed=None, **unused):
        voice = quote(voice or self.voice, safe="-")
        url = "%s/speak?model=%s&encoding=linear16&sample_rate=%d&container=none" % (
            self.base_url,
            voice,
            self.sample_rate,
        )
        if speed is not None:
            speed = float(speed)
            if speed < 0.7 or speed > 1.5:
                raise ValueError("Deepgram speed must be between 0.7 and 1.5")
            url += "&speed=%s" % speed
        return self._json_request(
            url,
            {"Authorization": "Token " + self.token},
            {"text": text},
            audio_format=AudioFormat(self.sample_rate, 1, 16),
        )


def _xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


class AzureTTS(_Provider):
    """Azure Speech REST adapter using raw mono PCM."""

    def __init__(
        self,
        api_key,
        region,
        *,
        voice="en-US-AvaMultilingualNeural",
        language="en-US",
        sample_rate=24000,
        endpoint=None,
    ):
        if sample_rate not in (8000, 16000, 22050, 24000, 44100, 48000):
            raise ValueError("unsupported Azure PCM sample rate")
        self.api_key, self.voice, self.language, self.sample_rate = (
            api_key,
            voice,
            language,
            sample_rate,
        )
        self.endpoint = (
            endpoint
            or "https://%s.tts.speech.microsoft.com/cognitiveservices/v1" % region
        )

    def request(self, text, *, voice=None, language=None, ssml=False, **unused):
        language, voice = language or self.language, voice or self.voice
        body = (
            text
            if ssml
            else '<speak version="1.0" xml:lang="%s"><voice name="%s">%s</voice></speak>'
            % (_xml(language), _xml(voice), _xml(text))
        )
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/ssml+xml",
            "User-Agent": "micropython-hardware",
            "X-Microsoft-OutputFormat": "raw-%dkhz-16bit-mono-pcm"
            % (self.sample_rate // 1000),
        }
        # Azure spells the 22.05/44.1 kHz values without a decimal point.
        if self.sample_rate in (22050, 44100):
            headers["X-Microsoft-OutputFormat"] = (
                "raw-%dhz-16bit-mono-pcm" % self.sample_rate
            )
        return TTSRequest(
            self.endpoint,
            headers,
            body.encode(),
            audio_format=AudioFormat(self.sample_rate, 1, 16),
        )


class GoogleCloudTTS(_Provider):
    """Google Cloud Text-to-Speech REST adapter.

    LINEAR16 is returned inside JSON as a base64 WAV stream.  The small WAV
    header is removed by :class:`TTSClient`, yielding raw PCM to callers.
    """

    def __init__(
        self,
        api_key,
        *,
        voice="en-US-Chirp3-HD-Achernar",
        language="en-US",
        sample_rate=24000,
        endpoint="https://texttospeech.googleapis.com/v1/text:synthesize",
    ):
        self.api_key, self.voice, self.language = api_key, voice, language
        self.sample_rate, self.endpoint = sample_rate, endpoint

    def request(self, text, *, voice=None, language=None, **unused):
        body = {
            "input": {"text": text},
            "voice": {
                "languageCode": language or self.language,
                "name": voice or self.voice,
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": self.sample_rate,
            },
        }
        url = (
            self.endpoint
            + ("&" if "?" in self.endpoint else "?")
            + "key="
            + quote(self.api_key)
        )
        return self._json_request(
            url,
            {},
            body,
            response="google-wav",
            audio_format=AudioFormat(self.sample_rate, 1, 16),
        )


# Gemini streaming TTS:
# https://ai.google.dev/gemini-api/docs/speech-generation
# Gemini Live API for interactive, bidirectional audio:
# https://ai.google.dev/gemini-api/docs/live-api
#
# There is no list-voices HTTP endpoint; the Interactions API documents a fixed
# prebuilt catalog. Expose it here so UIs can call GeminiTTS.voices().

GEMINI_TTS_MODELS = (
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
)

# (voice name, short description) — official prebuilt voices.
GEMINI_VOICES = (
    ("Zephyr", "Bright"),
    ("Puck", "Upbeat"),
    ("Charon", "Informative"),
    ("Kore", "Firm"),
    ("Fenrir", "Excitable"),
    ("Leda", "Youthful"),
    ("Orus", "Firm"),
    ("Aoede", "Breezy"),
    ("Callirrhoe", "Easy-going"),
    ("Autonoe", "Bright"),
    ("Enceladus", "Breathy"),
    ("Iapetus", "Clear"),
    ("Umbriel", "Easy-going"),
    ("Algieba", "Smooth"),
    ("Despina", "Smooth"),
    ("Erinome", "Clear"),
    ("Algenib", "Gravelly"),
    ("Rasalgethi", "Informative"),
    ("Laomedeia", "Upbeat"),
    ("Achernar", "Soft"),
    ("Alnilam", "Firm"),
    ("Schedar", "Even"),
    ("Gacrux", "Mature"),
    ("Pulcherrima", "Forward"),
    ("Achird", "Friendly"),
    ("Zubenelgenubi", "Casual"),
    ("Vindemiatrix", "Gentle"),
    ("Sadachbia", "Lively"),
    ("Sadaltager", "Knowledgeable"),
    ("Sulafat", "Warm"),
)


class GeminiTTS(_Provider):
    """Gemini streaming TTS adapter (base64 raw 24 kHz PCM deltas).

    Style / pace / accent are prompt-driven via ``instructions``.
    """

    def __init__(
        self,
        api_key,
        *,
        model=GEMINI_TTS_MODELS[0],
        voice="Kore",
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ):
        self.api_key, self.model, self.voice, self.base_url = (
            api_key,
            model,
            voice,
            base_url.rstrip("/"),
        )

    @staticmethod
    def voices():
        """Return ``((name, description), ...)`` for prebuilt Gemini TTS voices."""
        return GEMINI_VOICES

    @staticmethod
    def models():
        """Return known Gemini TTS model ids (streaming varies by model)."""
        return GEMINI_TTS_MODELS

    @staticmethod
    def voice_label(name, description=None):
        """Dropdown label: ``Name - Description`` (ASCII for LVGL fonts)."""
        if description is None:
            for voice_name, desc in GEMINI_VOICES:
                if voice_name == name:
                    description = desc
                    break
        if description:
            return "%s - %s" % (name, description)
        return name

    @staticmethod
    def voice_from_label(label):
        """Parse a ``voice_label`` string back to the voice name."""
        label = (label or "").strip()
        # Prefer ASCII separator; still accept legacy em dash labels.
        for sep in (" - ", " — "):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        return label

    def request(self, text, *, voice=None, instructions=None, model=None, **unused):
        prompt = (instructions + "\n" + text) if instructions else text
        body = {
            "model": model or self.model,
            "input": prompt,
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice or self.voice}]},
            "stream": True,
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Accept": "text/event-stream",
            "Accept-Encoding": "identity",
            "Api-Revision": "2026-05-20",
        }
        return self._json_request(
            self.base_url + "/interactions",
            headers,
            body,
            response="gemini-sse",
        )


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
            response = self.module.post(
                request.url, headers=request.headers, data=request.body, stream=True
            )
        except TypeError:  # urequests has no stream keyword
            response = self.module.post(
                request.url, headers=request.headers, data=request.body
            )
        status = getattr(response, "status_code", 200)
        if status < 200 or status >= 300:
            detail = getattr(response, "text", "")
            response.close()
            raise OSError("TTS HTTP %d: %s" % (status, detail))
        raw = getattr(response, "raw", None)
        if raw is not None and hasattr(raw, "decode_content"):
            raw.decode_content = True
        return response


def _read_chunks(response, size):
    raw = getattr(response, "raw", response)
    while True:
        chunk = raw.read(size)
        if not chunk:
            break
        yield chunk


def _sse_data(response, size):
    """Yield JSON payloads from a server-sent event response."""
    raw = getattr(response, "raw", response)
    pending = b""
    while True:
        chunk = raw.read(size)
        if not chunk:
            break
        pending += chunk.replace(b"\r\n", b"\n")
        while b"\n\n" in pending:
            event, pending = pending.split(b"\n\n", 1)
            data = b"\n".join(
                line[5:].lstrip()
                for line in event.split(b"\n")
                if line.startswith(b"data:")
            )
            if data and data != b"[DONE]":
                yield json.loads(data)


def _gemini_error(event):
    """Raise a clear error from an Interactions SSE ``error`` event."""
    err = event.get("error") or {}
    if not isinstance(err, dict):
        raise ValueError("Gemini error: %s" % (err,))
    code = err.get("code") or event.get("event_type") or "error"
    message = err.get("message") or str(err)
    raise ValueError("Gemini %s: %s" % (code, message))


def _gemini_pcm(response, size):
    received = False
    for event in _sse_data(response, size):
        if event.get("event_type") == "error" or "error" in event:
            _gemini_error(event)
        delta = event.get("delta", {})
        if event.get("event_type") == "step.delta" and delta.get("type") == "audio":
            received = True
            yield binascii.a2b_base64(delta["data"])
    if not received:
        raise ValueError("Gemini stream completed without audio")


def _wav_pcm(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Google LINEAR16 response is not WAV")
    offset = 12
    while offset + 8 <= len(data):
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        if data[offset : offset + 4] == b"data":
            return data[offset + 8 : offset + 8 + size]
        offset += 8 + size + (size & 1)
    raise ValueError("WAV data chunk is missing")


def _read_exact(raw, length):
    data = b""
    while len(data) < length:
        chunk = raw.read(length - len(data))
        if not chunk:
            raise ValueError("truncated WAV response")
        data += chunk
    return data


def _wav_pcm_chunks(response, size, audio_format):
    """Parse a WAV response incrementally and yield frame-aligned PCM."""
    raw = getattr(response, "raw", response)
    header = _read_exact(raw, 12)
    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise ValueError("TTS response is not WAV")

    found_format = False
    while True:
        chunk_header = _read_exact(raw, 8)
        chunk_id = chunk_header[:4]
        chunk_length = int.from_bytes(chunk_header[4:8], "little")
        if chunk_id == b"fmt ":
            value = _read_exact(raw, chunk_length)
            if len(value) < 16 or int.from_bytes(value[:2], "little") != 1:
                raise ValueError("unsupported WAV encoding")
            actual = AudioFormat(
                int.from_bytes(value[4:8], "little"),
                int.from_bytes(value[2:4], "little"),
                int.from_bytes(value[14:16], "little"),
            )
            if actual != audio_format:
                raise ValueError("WAV audio format does not match TTS format")
            found_format = True
        elif chunk_id == b"data":
            if not found_format:
                raise ValueError("WAV fmt chunk is missing")
            remaining = chunk_length
            open_ended = chunk_length >= 0x7FFFFFFF
            pending = b""
            while open_ended or remaining:
                chunk = raw.read(size if open_ended else min(size, remaining))
                if not chunk:
                    if open_ended:
                        break
                    raise ValueError("truncated WAV audio data")
                if not open_ended:
                    remaining -= len(chunk)
                pending += chunk
                aligned = len(pending) - len(pending) % audio_format.frame_size
                if aligned:
                    yield pending[:aligned]
                    pending = pending[aligned:]
            if pending:
                raise ValueError("WAV data contains an incomplete PCM frame")
            return
        else:
            _read_exact(raw, chunk_length)
        if chunk_length & 1:
            _read_exact(raw, 1)


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
            return SpeechStream(
                _read_chunks(response, self.chunk_size),
                request.audio_format,
                response.close,
            )
        if request.response == "gemini-sse":
            return SpeechStream(
                _gemini_pcm(response, self.chunk_size),
                request.audio_format,
                response.close,
            )
        if request.response == "wav":
            return SpeechStream(
                _wav_pcm_chunks(response, self.chunk_size, request.audio_format),
                request.audio_format,
                response.close,
            )
        try:
            value = (
                response.json()
                if hasattr(response, "json")
                else json.loads(response.read())
            )
            if request.response == "google-wav":
                data = _wav_pcm(binascii.a2b_base64(value["audioContent"]))
            else:
                data = binascii.a2b_base64(
                    value["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                )
        finally:
            response.close()
        chunks = (
            data[i : i + self.chunk_size] for i in range(0, len(data), self.chunk_size)
        )
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
