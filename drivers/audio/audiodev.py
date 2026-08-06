"""Small portable PCM and tone device contracts for MicroPython and CPython."""

try:
    import asyncio
except ImportError:  # pragma: no cover - uasyncio name on older firmware
    import uasyncio as asyncio

import sys


class AudioFormat:  # noqa: PLW1641 - mutable value object is intentionally unhashable
    """Description of raw, interleaved PCM frames."""

    def __init__(self, rate, channels, bits, signed=True, byteorder="little"):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if channels <= 0:
            raise ValueError("channels must be positive")
        if bits not in (8, 16, 32):
            raise ValueError("bits must be 8, 16, or 32")
        if byteorder not in ("little", "big"):
            raise ValueError("byteorder must be 'little' or 'big'")
        self.rate = int(rate)
        self.channels = int(channels)
        self.bits = int(bits)
        self.signed = bool(signed)
        self.byteorder = byteorder
        self.frame_size = self.channels * self.bits // 8

    def __repr__(self):
        return "AudioFormat(rate=%d, channels=%d, bits=%d, signed=%r, byteorder=%r)" % (
            self.rate,
            self.channels,
            self.bits,
            self.signed,
            self.byteorder,
        )

    def __eq__(self, other):
        return isinstance(other, AudioFormat) and (
            self.rate,
            self.channels,
            self.bits,
            self.signed,
            self.byteorder,
        ) == (
            other.rate,
            other.channels,
            other.bits,
            other.signed,
            other.byteorder,
        )


class AudioSession:
    """Coordinate devices which share a codec or peripheral."""

    def __init__(self, codec_factory=None, duplex=False):
        self.codec_factory = codec_factory
        self.duplex = bool(duplex)
        self.codec = None
        self._owners = []

    def get_codec(self):
        """Return the shared codec, constructing it on first access."""
        if self.codec is None and self.codec_factory is not None:
            self.codec = self.codec_factory()
        return self.codec

    def acquire(self, owner, direction):
        if owner in self._owners:
            return self.codec
        if self._owners and not self.duplex:
            raise OSError("audio session is already active")
        self.get_codec()
        self._owners.append(owner)
        return self.codec

    def release(self, owner):
        if owner in self._owners:
            self._owners.remove(owner)


def _clamp_percent(value):
    value = int(value)
    if value < 0:
        return 0
    if value > 100:
        return 100
    return value


def _call_optional(obj, name, *args):
    method = getattr(obj, name, None)
    if method is not None:
        return method(*args)
    return None


def _scale_pcm(source, target, fmt, percent):
    """Scale PCM into target without allocating per sample."""
    src = memoryview(source)
    dst = memoryview(target)
    length = len(src)
    if len(dst) < length:
        raise ValueError("target is too small")
    if percent == 100:
        dst[:length] = src
        return length
    if percent == 0:
        dst[:length] = bytes(length)
        return length

    width = fmt.bits // 8
    order = fmt.byteorder
    signed = fmt.signed
    midpoint = 0 if signed else 1 << (fmt.bits - 1)
    sign_bit = 1 << (fmt.bits - 1)
    modulus = 1 << fmt.bits
    for offset in range(0, length, width):
        sample = int.from_bytes(src[offset : offset + width], order)
        if signed and sample & sign_bit:
            sample -= modulus
        if signed:
            sample = sample * percent // 100
        else:
            sample = midpoint + (sample - midpoint) * percent // 100
        dst[offset : offset + width] = (sample % modulus).to_bytes(width, order)
    return length


class _Device:
    direction = None

    def __init__(self, stream_factory, session=None):
        self._stream_factory = stream_factory
        self.session = session
        self.stream = None
        self.is_open = False
        self._async_stream = None
        self._codec = None

    @property
    def codec(self):
        if self._codec is None and self.session is not None:
            return self.session.get_codec()
        return self._codec

    @codec.setter
    def codec(self, value):
        self._codec = value

    def _open_stream(self):
        stream = self._stream_factory() if callable(self._stream_factory) else self._stream_factory
        _call_optional(stream, "open")
        self.stream = stream

    def open(self):
        if self.is_open:
            return self
        if self.session is not None:
            self.session.acquire(self, self.direction)
        try:
            self._open_stream()
            self.is_open = True
        except Exception:
            if self.session is not None:
                self.session.release(self)
            raise
        return self

    def close(self):
        if not self.is_open:
            return
        try:
            _call_optional(self.stream, "close")
            if not hasattr(self.stream, "close"):
                _call_optional(self.stream, "deinit")
        finally:
            self.stream = None
            self._async_stream = None
            self.is_open = False
            if self.session is not None:
                self.session.release(self)

    deinit = close

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class PCMOutput(_Device):
    """Raw PCM playback with normalized volume and async support."""

    kind = "pcm"
    direction = "out"

    def __init__(
        self,
        stream_factory,
        format,
        *,
        session=None,
        codec=None,
        amplifier=None,
        set_hardware_volume=None,
        set_hardware_mute=None,
        power=None,
    ):
        super().__init__(stream_factory, session)
        self.format = format
        self.codec = codec
        self.amplifier = amplifier
        self._set_hardware_volume = set_hardware_volume
        self._set_hardware_mute = set_hardware_mute
        self._power = power
        self._volume = 100
        self._muted = False
        self._scratch = bytearray()
        capabilities = {"pcm", "playback", "volume", "mute"}
        capabilities.add("hardware-volume" if set_hardware_volume else "software-volume")
        self.capabilities = frozenset(capabilities)

    @property
    def volume(self):
        return self._volume

    @property
    def muted(self):
        return self._muted

    def open(self):
        if self.is_open:
            return self
        super().open()
        if self.session is not None and self.codec is None:
            self.codec = self.session.codec
        if self._power is not None:
            self._power(True)
        if self._set_hardware_volume is not None:
            self._set_hardware_volume(self._volume)
        if self._set_hardware_mute is not None:
            self._set_hardware_mute(self._muted)
        return self

    def set_volume(self, percent):
        self._volume = _clamp_percent(percent)
        if self.is_open and self._set_hardware_volume is not None:
            self._set_hardware_volume(self._volume)
        return self._volume

    def mute(self, value=True):
        self._muted = bool(value)
        if self.is_open and self._set_hardware_mute is not None:
            self._set_hardware_mute(self._muted)
        return self._muted

    def _prepare(self, buf):
        view = memoryview(buf)
        if len(view) % self.format.frame_size:
            raise ValueError("PCM buffer must contain complete frames")
        if self._set_hardware_volume is not None and not (
            self._muted and self._set_hardware_mute is None
        ):
            return view
        percent = 0 if self._muted else self._volume
        if percent == 100:
            return view
        if len(self._scratch) < len(view):
            self._scratch = bytearray(len(view))
        target = memoryview(self._scratch)[: len(view)]
        _scale_pcm(view, target, self.format, percent)
        return target

    def write(self, buf):
        self.open()
        source = self._prepare(buf)
        written = 0
        while written < len(source):
            count = self.stream.write(source[written:])
            if count is None:
                count = len(source) - written
            if count <= 0:
                raise OSError("audio stream made no write progress")
            written += count
        return len(buf)

    def drain(self):
        self.open()
        return _call_optional(self.stream, "drain")

    async def awrite(self, buf):
        self.open()
        source = self._prepare(buf)
        method = getattr(self.stream, "awrite", None)
        if method is None and sys.implementation.name == "micropython":
            if self._async_stream is None:
                self._async_stream = asyncio.StreamWriter(self.stream)
            self._async_stream.write(source)
            await self._async_stream.drain()
            return len(buf)
        written = 0
        while written < len(source):
            if method is not None:
                count = await method(source[written:])
            else:
                count = self.stream.write(source[written:])
                await asyncio.sleep_ms(0) if hasattr(asyncio, "sleep_ms") else asyncio.sleep(0)
            if count is None:
                count = len(source) - written
            if count <= 0:
                raise OSError("audio stream made no write progress")
            written += count
        return len(buf)

    async def adrain(self):
        self.open()
        method = getattr(self.stream, "adrain", None)
        if method is not None:
            return await method()
        self.drain()
        await asyncio.sleep_ms(0) if hasattr(asyncio, "sleep_ms") else asyncio.sleep(0)

    def close(self):
        if not self.is_open:
            return
        try:
            if self._set_hardware_mute is not None:
                self._set_hardware_mute(True)
            if self._power is not None:
                self._power(False)
        finally:
            super().close()


class PCMInput(_Device):
    """Raw PCM capture with normalized gain and async support."""

    kind = "pcm"
    direction = "in"

    def __init__(
        self,
        stream_factory,
        format,
        *,
        session=None,
        codec=None,
        set_hardware_gain=None,
        set_hardware_mute=None,
        power=None,
    ):
        super().__init__(stream_factory, session)
        self.format = format
        self.codec = codec
        self._set_hardware_gain = set_hardware_gain
        self._set_hardware_mute = set_hardware_mute
        self._power = power
        self._gain = 100
        self._muted = False
        capabilities = {"pcm", "capture", "gain", "mute"}
        capabilities.add("hardware-gain" if set_hardware_gain else "software-gain")
        self.capabilities = frozenset(capabilities)

    @property
    def gain(self):
        return self._gain

    @property
    def muted(self):
        return self._muted

    def open(self):
        if self.is_open:
            return self
        super().open()
        if self.session is not None and self.codec is None:
            self.codec = self.session.codec
        if self._power is not None:
            self._power(True)
        if self._set_hardware_gain is not None:
            self._set_hardware_gain(self._gain)
        if self._set_hardware_mute is not None:
            self._set_hardware_mute(self._muted)
        return self

    def set_gain(self, percent):
        self._gain = _clamp_percent(percent)
        if self.is_open and self._set_hardware_gain is not None:
            self._set_hardware_gain(self._gain)
        return self._gain

    def mute(self, value=True):
        self._muted = bool(value)
        if self.is_open and self._set_hardware_mute is not None:
            self._set_hardware_mute(self._muted)
        return self._muted

    def _finish_read(self, buf, count):
        count -= count % self.format.frame_size
        view = memoryview(buf)[:count]
        if self._muted:
            view[:] = bytes(count)
        elif self._set_hardware_gain is None and self._gain != 100:
            _scale_pcm(view, view, self.format, self._gain)
        return count

    def readinto(self, buf):
        self.open()
        if len(buf) % self.format.frame_size:
            raise ValueError("PCM buffer must hold complete frames")
        return self._finish_read(buf, self.stream.readinto(buf))

    async def areadinto(self, buf):
        self.open()
        if len(buf) % self.format.frame_size:
            raise ValueError("PCM buffer must hold complete frames")
        method = getattr(self.stream, "areadinto", None)
        if method is None and sys.implementation.name == "micropython":
            if self._async_stream is None:
                self._async_stream = asyncio.StreamReader(self.stream)
            count = await self._async_stream.readinto(buf)
            return self._finish_read(buf, count)
        if method is not None:
            count = await method(buf)
        else:
            count = self.stream.readinto(buf)
            await asyncio.sleep_ms(0) if hasattr(asyncio, "sleep_ms") else asyncio.sleep(0)
        return self._finish_read(buf, count)

    def close(self):
        if not self.is_open:
            return
        try:
            if self._set_hardware_mute is not None:
                self._set_hardware_mute(True)
            if self._power is not None:
                self._power(False)
        finally:
            super().close()


class ToneOutput(_Device):
    """Frequency/duty output for PWM speakers and buzzers."""

    kind = "tone"
    direction = "out"

    def __init__(self, stream_factory, *, session=None, power=None):
        super().__init__(stream_factory, session)
        self._power = power
        self.capabilities = frozenset({"tone", "playback", "volume", "mute"})
        self._volume = 100
        self._muted = False

    def open(self):
        if self.is_open:
            return self
        super().open()
        if self._power is not None:
            self._power(True)
        return self

    @property
    def volume(self):
        return self._volume

    @property
    def muted(self):
        return self._muted

    def set_volume(self, percent):
        self._volume = _clamp_percent(percent)
        return self._volume

    def mute(self, value=True):
        self._muted = bool(value)
        if self._muted and self.is_open:
            self.stop()
        return self._muted

    def play(self, frequency, *, volume=None):
        self.open()
        level = self._volume if volume is None else _clamp_percent(volume)
        if self._muted:
            level = 0
        if hasattr(self.stream, "play"):
            self.stream.play(frequency, level)
        else:
            self.stream.freq(int(frequency))
            duty = level * 32768 // 100
            if hasattr(self.stream, "duty_u16"):
                self.stream.duty_u16(duty)
            else:
                self.stream.duty(level * 512 // 100)

    def stop(self):
        if not self.is_open:
            return
        if hasattr(self.stream, "stop"):
            self.stream.stop()
        elif hasattr(self.stream, "duty_u16"):
            self.stream.duty_u16(0)
        else:
            self.stream.duty(0)

    async def aplay(self, frequency, duration_ms):
        self.play(frequency)
        try:
            if hasattr(asyncio, "sleep_ms"):
                await asyncio.sleep_ms(duration_ms)
            else:
                await asyncio.sleep(duration_ms / 1000)
        finally:
            self.stop()

    def close(self):
        if self.is_open:
            self.stop()
            if self._power is not None:
                self._power(False)
        super().close()


def _u16(value):
    return int(value).to_bytes(2, "little")


def _u32(value):
    return int(value).to_bytes(4, "little")


def _wav_header(fmt, data_length):
    """Build a 44-byte PCM RIFF/WAVE header for *fmt* and *data_length* bytes."""
    byte_rate = fmt.rate * fmt.frame_size
    block_align = fmt.frame_size
    bits = fmt.bits
    channels = fmt.channels
    # PCM WAVEFORMATEX; unsigned 8-bit is conventional for bits==8.
    return (
        b"RIFF"
        + _u32(36 + data_length)
        + b"WAVEfmt "
        + _u32(16)
        + _u16(1)
        + _u16(channels)
        + _u32(fmt.rate)
        + _u32(byte_rate)
        + _u16(block_align)
        + _u16(bits)
        + b"data"
        + _u32(data_length)
    )


def _parse_pcm_wav(data):
    """Return ``(AudioFormat, pcm_bytes)`` from a PCM WAV buffer."""
    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Expected RIFF/WAVE data")

    pos = 12
    total = len(data)
    channels = None
    rate = None
    bits = None
    fmt_tag = None
    payload = None

    while pos + 8 <= total:
        chunk_id = data[pos : pos + 4]
        chunk_len = int.from_bytes(data[pos + 4 : pos + 8], "little")
        pos += 8
        end = pos + chunk_len
        if end > total:
            end = total

        if chunk_id == b"fmt ":
            chunk = data[pos:end]
            if len(chunk) < 16:
                raise ValueError("WAV fmt chunk is too short")
            fmt_tag = int.from_bytes(chunk[0:2], "little")
            channels = int.from_bytes(chunk[2:4], "little")
            rate = int.from_bytes(chunk[4:8], "little")
            bits = int.from_bytes(chunk[14:16], "little")
        elif chunk_id == b"data":
            payload = data[pos:end]
            break

        pos = end + (chunk_len % 2)

    if payload is None:
        raise ValueError("WAV data chunk not found")
    if fmt_tag != 1:
        raise ValueError("Only PCM WAV is supported")
    if channels is None or rate is None or bits is None:
        raise ValueError("WAV fmt metadata is incomplete")

    signed = bits != 8
    return AudioFormat(rate, channels, bits, signed=signed), bytes(payload)


class _WavOutputStream:
    """File stream that writes a PCM WAV, finalizing sizes on close."""

    def __init__(self, path, fmt):
        self.path = path
        self.format = fmt
        self._file = None
        self._data_length = 0

    def open(self):
        if self._file is not None:
            return self
        self._file = open(self.path, "wb")
        self._file.write(_wav_header(self.format, 0))
        self._data_length = 0
        return self

    def write(self, buf):
        self.open()
        view = memoryview(buf)
        self._file.write(view)
        self._data_length += len(view)
        return len(view)

    def drain(self):
        if self._file is not None:
            self._file.flush()

    def close(self):
        if self._file is None:
            return
        try:
            self._file.seek(0)
            self._file.write(_wav_header(self.format, self._data_length))
            self._file.flush()
        finally:
            self._file.close()
            self._file = None


class _WavInputStream:
    """File-backed PCM stream; ``readinto`` returns 0 at EOF."""

    def __init__(self, path):
        self.path = path
        self.format = None
        self._pcm = b""
        self._offset = 0
        self._opened = False

    def open(self):
        if self._opened:
            return self
        with open(self.path, "rb") as handle:
            data = handle.read()
        self.format, self._pcm = _parse_pcm_wav(data)
        self._offset = 0
        self._opened = True
        return self

    def readinto(self, buf):
        self.open()
        remaining = len(self._pcm) - self._offset
        if remaining <= 0:
            return 0
        count = min(len(buf), remaining)
        buf[:count] = self._pcm[self._offset : self._offset + count]
        self._offset += count
        return count

    def close(self):
        self._opened = False
        self._pcm = b""
        self._offset = 0


def wav_output(path, format):
    """Create a :class:`PCMOutput` that writes interleaved PCM into a WAV file."""
    if not isinstance(format, AudioFormat):
        raise TypeError("format must be an AudioFormat")
    return PCMOutput(lambda: _WavOutputStream(path, format), format)


def wav_input(path):
    """Create a :class:`PCMInput` that reads interleaved PCM from a WAV file."""
    stream = _WavInputStream(path)
    stream.open()
    fmt = stream.format
    # Re-open on PCMInput.open so lifecycle matches other devices.
    stream.close()
    return PCMInput(lambda: _WavInputStream(path), fmt)
