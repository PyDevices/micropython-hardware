"""pygame-ce playback backend for the portable :mod:`audiodev` contract."""

import asyncio
import time

from audiodev import AudioFormat, PCMOutput


def _sleep_ms(milliseconds):
    time.sleep(milliseconds / 1000)


async def _asleep_ms(milliseconds):
    await asyncio.sleep(milliseconds / 1000)


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
        import pygame

        size = -self.format.bits if self.format.signed else self.format.bits
        current = pygame.mixer.get_init()
        wanted = (self.format.rate, size, self.format.channels)
        if current is None:
            pygame.mixer.init(*wanted, buffer=self.buffer)
        elif current != wanted:
            raise OSError("pygame mixer format is %r; requested %r" % (current, wanted))
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


def audio_out(format=None, *, buffer=512, poll_ms=2):
    """Create a pygame-ce-backed PCM playback device."""
    fmt = format or AudioFormat(16000, 2, 16)
    return PCMOutput(
        lambda: PygameOutputStream(fmt, buffer=buffer, poll_ms=poll_ms),
        fmt,
    )


def audio_in(*args, **kwargs):
    """pygame-ce has no public capture API; use ``sdl2audio.audio_in``."""
    raise NotImplementedError("pygame-ce capture is unavailable; use sdl2audio.audio_in")
