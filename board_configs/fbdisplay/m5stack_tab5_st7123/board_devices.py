"""Lazy constructors for M5Stack Tab5 (ST7123). DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"audio_in", "audio_out", "sdcard", "camera", "i2c", "wlan", "ble"})

from audiodev import AudioFormat, AudioSession, PCMInput, PCMOutput

_FORMAT = AudioFormat(16000, 2, 16)
_SESSION = AudioSession(duplex=False)

# M5Unified Tab5 I2S / codec pin map
_MCLK = 30
_BCLK = 27
_LRCK = 29
_DOUT = 26
_DIN = 28
_RATE = 16000


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    import board_config as bc

    return bc.i2c


def audio_in():
    """ES7210 ADC + I2S RX."""
    from machine import I2S, Pin

    from es7210 import ES7210

    import board_config as bc

    codec = ES7210(bc.i2c, profile="m5")

    def stream():
        return I2S(
        0,
        sck=Pin(_BCLK),
        ws=Pin(_LRCK),
        sd=Pin(_DIN),
        mck=Pin(_MCLK),
        mode=I2S.RX,
        bits=16,
        format=I2S.STEREO,
        rate=_RATE,
        ibuf=20000,
        )

    return PCMInput(
        stream, _FORMAT, session=_SESSION, codec=codec,
        set_hardware_gain=codec.set_gain, power=codec.enable_input,
    )


def audio_out():
    """ES8388 DAC + I2S TX (+ PI4IOE amp enable)."""
    from machine import I2S, Pin

    from es8388 import ES8388
    from pi4ioe5v import tab5_set_amp

    import board_config as bc

    codec = ES8388(bc.i2c)

    def stream():
        return I2S(
        0,
        sck=Pin(_BCLK),
        ws=Pin(_LRCK),
        sd=Pin(_DOUT),
        mck=Pin(_MCLK),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=_RATE,
        ibuf=20000,
        )

    def power(enable):
        codec.enable_output(enable)
        tab5_set_amp(bc.i2c, enable)

    return PCMOutput(
        stream, _FORMAT, session=_SESSION, codec=codec,
        set_hardware_volume=codec.set_dac_volume,
        set_hardware_mute=codec.dac_mute, power=power,
    )


def sdcard():
    from machine import SDCard

    return SDCard()


def camera():
    raise NotImplementedError("Tab5 camera needs native CSI support")


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()
