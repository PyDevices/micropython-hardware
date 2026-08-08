"""SDL2 queued-audio backend for :mod:`audiodev`."""

try:
    import asyncio
except ImportError:  # pragma: no cover
    import uasyncio as asyncio

import sys
import time

from audiodev import AudioFormat, PCMInput, PCMOutput
import usdl2 as sdl


def _android_session():
    """Attach Android media focus/FGS session on first PCM open (lazy).

    Non-Android hosts get ``session=None`` (unchanged PCMOutput behavior).
    On Android the module must be present; acquire/release stay lazy until
    ``open()`` / ``write()`` via :class:`audiodev.PCMOutput`.
    """
    if sys.platform != "android":
        return None
    from androidaudio_session import get_session

    return get_session()


def _sleep_ms(milliseconds):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(milliseconds)
    else:
        time.sleep(milliseconds / 1000)


async def _asleep_ms(milliseconds):
    if hasattr(asyncio, "sleep_ms"):
        await asyncio.sleep_ms(milliseconds)
    else:
        await asyncio.sleep(milliseconds / 1000)


def _sdl_format(fmt):
    if fmt.bits == 8:
        return sdl.AUDIO_S8 if fmt.signed else sdl.AUDIO_U8
    suffix = "LSB" if fmt.byteorder == "little" else "MSB"
    name = "AUDIO_%s%d%s" % ("S" if fmt.signed else "U", fmt.bits, suffix)
    value = getattr(sdl, name, None)
    if value is None:
        raise ValueError("SDL does not support %r" % fmt)
    return value


def list_audio_devices(capture=False):
    """Return SDL playback or capture device names."""
    count = sdl.SDL_GetNumAudioDevices(bool(capture))
    if count < 0:
        raise OSError(sdl.SDL_GetError())
    return tuple(sdl.SDL_GetAudioDeviceName(index, bool(capture)) for index in range(count))


class _SDLStream:
    def __init__(
        self,
        fmt,
        *,
        capture,
        device=None,
        samples=512,
        queue_ms=250,
        poll_ms=2,
    ):
        self.format = fmt
        self.capture = bool(capture)
        self.device_name = device
        self.samples = int(samples)
        self.queue_ms = int(queue_ms)
        self.poll_ms = int(poll_ms)
        self.device = 0
        self._bytes_per_second = fmt.rate * fmt.frame_size
        self._queue_limit = max(fmt.frame_size, self._bytes_per_second * queue_ms // 1000)

    def open(self):
        if self.device:
            return self
        if sdl.SDL_InitSubSystem(sdl.SDL_INIT_AUDIO) != 0:
            raise OSError(sdl.SDL_GetError())
        spec = sdl.SDL_AudioSpec(
            self.format.rate,
            _sdl_format(self.format),
            self.format.channels,
            self.samples,
        )
        self.device = sdl.SDL_OpenAudioDevice(
            self.device_name,
            self.capture,
            spec,
            None,
            0,
        )
        if not self.device:
            raise OSError(sdl.SDL_GetError())
        sdl.SDL_PauseAudioDevice(self.device, 0)
        return self

    def close(self):
        if self.device:
            sdl.SDL_CloseAudioDevice(self.device)
            self.device = 0


class SDLOutputStream(_SDLStream):
    def __init__(self, fmt, **kwargs):
        super().__init__(fmt, capture=False, **kwargs)

    def write(self, buf):
        self.open()
        while sdl.SDL_GetQueuedAudioSize(self.device) >= self._queue_limit:
            _sleep_ms(self.poll_ms)
        rc = sdl.SDL_QueueAudio(self.device, buf, len(buf))
        if rc != 0:
            raise OSError(sdl.SDL_GetError())
        return len(buf)

    async def awrite(self, buf):
        self.open()
        while sdl.SDL_GetQueuedAudioSize(self.device) >= self._queue_limit:
            await _asleep_ms(self.poll_ms)
        rc = sdl.SDL_QueueAudio(self.device, buf, len(buf))
        if rc != 0:
            raise OSError(sdl.SDL_GetError())
        return len(buf)

    def drain(self):
        self.open()
        while sdl.SDL_GetQueuedAudioSize(self.device):
            _sleep_ms(self.poll_ms)

    async def adrain(self):
        self.open()
        while sdl.SDL_GetQueuedAudioSize(self.device):
            await _asleep_ms(self.poll_ms)


class SDLInputStream(_SDLStream):
    def __init__(self, fmt, **kwargs):
        super().__init__(fmt, capture=True, **kwargs)

    def readinto(self, buf):
        self.open()
        needed = len(buf)
        while sdl.SDL_GetQueuedAudioSize(self.device) < self.format.frame_size:
            _sleep_ms(self.poll_ms)
        available = min(needed, sdl.SDL_GetQueuedAudioSize(self.device))
        available -= available % self.format.frame_size
        return sdl.SDL_DequeueAudio(self.device, buf, available)

    async def areadinto(self, buf):
        self.open()
        needed = len(buf)
        while sdl.SDL_GetQueuedAudioSize(self.device) < self.format.frame_size:
            await _asleep_ms(self.poll_ms)
        available = min(needed, sdl.SDL_GetQueuedAudioSize(self.device))
        available -= available % self.format.frame_size
        return sdl.SDL_DequeueAudio(self.device, buf, available)


def audio_out(
    format=None,
    *,
    device=None,
    samples=512,
    queue_ms=250,
    poll_ms=2,
):
    """Create an SDL-backed :class:`PCMOutput`."""
    fmt = format or AudioFormat(16000, 2, 16)
    return PCMOutput(
        lambda: SDLOutputStream(
            fmt,
            device=device,
            samples=samples,
            queue_ms=queue_ms,
            poll_ms=poll_ms,
        ),
        fmt,
        session=_android_session(),
    )


def audio_in(
    format=None,
    *,
    device=None,
    samples=512,
    queue_ms=250,
    poll_ms=2,
):
    """Create an SDL-backed :class:`PCMInput` using real host capture."""
    fmt = format or AudioFormat(16000, 1, 16)
    return PCMInput(
        lambda: SDLInputStream(
            fmt,
            device=device,
            samples=samples,
            queue_ms=queue_ms,
            poll_ms=poll_ms,
        ),
        fmt,
    )
