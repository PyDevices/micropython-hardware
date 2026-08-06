"""pygame-ce playback and capture backend for the portable :mod:`audiodev` contract."""

import asyncio
import collections
import threading
import time

from audiodev import AudioFormat, PCMInput, PCMOutput


def _sleep_ms(milliseconds):
    time.sleep(milliseconds / 1000)


async def _asleep_ms(milliseconds):
    await asyncio.sleep(milliseconds / 1000)


def _ensure_pygame():
    import pygame

    if not pygame.get_init():
        pygame.init()
    return pygame


class PygameOutputStream:
    """Small queued PCM stream using pygame-ce's SDL mixer."""

    def __init__(self, fmt, *, buffer=512, poll_ms=2):
        self.format = fmt
        self.buffer = int(buffer)
        self.poll_ms = int(poll_ms)
        self.channel = None
        self._pygame = None

    def open(self):
        if self.channel is not None:
            return self
        pygame = _ensure_pygame()

        size = -self.format.bits if self.format.signed else self.format.bits
        current = pygame.mixer.get_init()
        wanted = (self.format.rate, size, self.format.channels)
        if current is None:
            pygame.mixer.init(*wanted, buffer=self.buffer)
        elif current[:3] != wanted:
            # pygame.init() may have opened the mixer at a default rate/layout.
            pygame.mixer.quit()
            pygame.mixer.init(*wanted, buffer=self.buffer)
        self._pygame = pygame
        self.channel = pygame.mixer.find_channel(force=True)
        return self

    def _sound(self, buf):
        return self._pygame.mixer.Sound(buffer=bytes(buf))

    def write(self, buf):
        self.open()
        sound = self._sound(buf)
        if not self.channel.get_busy():
            self.channel.play(sound)
        else:
            while self.channel.get_queue() is not None:
                _sleep_ms(self.poll_ms)
            self.channel.queue(sound)
        return len(buf)

    async def awrite(self, buf):
        self.open()
        sound = self._sound(buf)
        if not self.channel.get_busy():
            self.channel.play(sound)
        else:
            while self.channel.get_queue() is not None:
                await _asleep_ms(self.poll_ms)
            self.channel.queue(sound)
        return len(buf)

    def drain(self):
        while self.channel is not None and self.channel.get_busy():
            _sleep_ms(self.poll_ms)

    async def adrain(self):
        while self.channel is not None and self.channel.get_busy():
            await _asleep_ms(self.poll_ms)

    def close(self):
        if self.channel is not None:
            self.channel.stop()
            self.channel = None


def _pygame_audio_format(fmt):
    """Map :class:`AudioFormat` to a ``pygame._sdl2.audio`` format constant."""
    from pygame._sdl2 import audio as sdl_audio

    if fmt.bits == 8:
        return sdl_audio.AUDIO_S8 if fmt.signed else sdl_audio.AUDIO_U8
    if fmt.bits == 16:
        if fmt.byteorder == "little":
            return sdl_audio.AUDIO_S16LSB if fmt.signed else sdl_audio.AUDIO_U16LSB
        return sdl_audio.AUDIO_S16MSB if fmt.signed else sdl_audio.AUDIO_U16MSB
    if fmt.bits == 32:
        if fmt.byteorder == "little":
            return sdl_audio.AUDIO_S32LSB if fmt.signed else sdl_audio.AUDIO_U32LSB
        return sdl_audio.AUDIO_S32MSB if fmt.signed else sdl_audio.AUDIO_U32MSB
    raise ValueError("unsupported pygame audio format %r" % (fmt,))


class PygameInputStream:
    """Microphone capture via ``pygame._sdl2.AudioDevice``."""

    def __init__(self, fmt, *, device=None, chunksize=512, poll_ms=2, queue_ms=500):
        self.format = fmt
        self.device_name = device
        self.chunksize = int(chunksize)
        self.poll_ms = int(poll_ms)
        self._queue_limit = max(
            fmt.frame_size,
            fmt.rate * fmt.frame_size * int(queue_ms) // 1000,
        )
        self._device = None
        self._lock = threading.Lock()
        self._chunks = collections.deque()
        self._pending = bytearray()

    def _callback(self, audiodevice, audiomemoryview):
        chunk = bytes(audiomemoryview)
        with self._lock:
            self._chunks.append(chunk)
            total = sum(len(item) for item in self._chunks) + len(self._pending)
            while total > self._queue_limit and self._chunks:
                dropped = self._chunks.popleft()
                total -= len(dropped)

    def open(self):
        if self._device is not None:
            return self
        _ensure_pygame()
        from pygame._sdl2 import audio as sdl_audio

        names = sdl_audio.get_audio_device_names(True)
        if self.device_name is None and not names:
            raise OSError("no pygame capture devices available")
        self._device = sdl_audio.AudioDevice(
            devicename=self.device_name,
            iscapture=True,
            frequency=self.format.rate,
            audioformat=_pygame_audio_format(self.format),
            numchannels=self.format.channels,
            chunksize=self.chunksize,
            allowed_changes=0,
            callback=self._callback,
        )
        self._device.pause(0)
        return self

    def _take(self, needed):
        with self._lock:
            while len(self._pending) < needed and self._chunks:
                self._pending.extend(self._chunks.popleft())
            count = min(needed, len(self._pending))
            count -= count % self.format.frame_size
            if count <= 0:
                return b""
            data = bytes(self._pending[:count])
            del self._pending[:count]
            return data

    def readinto(self, buf):
        self.open()
        needed = len(buf)
        while True:
            data = self._take(needed)
            if data:
                buf[: len(data)] = data
                return len(data)
            _sleep_ms(self.poll_ms)

    async def areadinto(self, buf):
        self.open()
        needed = len(buf)
        while True:
            data = self._take(needed)
            if data:
                buf[: len(data)] = data
                return len(data)
            await _asleep_ms(self.poll_ms)

    def close(self):
        if self._device is not None:
            try:
                self._device.pause(1)
                self._device.close()
            except Exception:
                pass
            self._device = None
        with self._lock:
            self._chunks.clear()
            self._pending = bytearray()


def audio_out(format=None, *, buffer=512, poll_ms=2):
    """Create a pygame-ce-backed PCM playback device."""
    fmt = format or AudioFormat(16000, 2, 16)
    return PCMOutput(
        lambda: PygameOutputStream(fmt, buffer=buffer, poll_ms=poll_ms),
        fmt,
    )


def audio_in(format=None, *, device=None, chunksize=512, poll_ms=2, queue_ms=500):
    """Create a pygame-ce-backed PCM capture device via ``_sdl2.AudioDevice``."""
    fmt = format or AudioFormat(16000, 1, 16)
    return PCMInput(
        lambda: PygameInputStream(
            fmt,
            device=device,
            chunksize=chunksize,
            poll_ms=poll_ms,
            queue_ms=queue_ms,
        ),
        fmt,
    )
