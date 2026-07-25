"""Lazy constructors for M5Stack Tab5 (ILI9881C). DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"microphone", "audio", "sdcard", "camera", "i2c", "wlan", "ble"})

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


def microphone():
    """ES7210 ADC + I2S RX."""
    from machine import I2S, Pin

    from es7210 import ES7210

    import board_config as bc

    ES7210(bc.i2c, profile="m5")
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


def audio():
    """ES8388 DAC + I2S TX (+ PI4IOE amp enable)."""
    from machine import I2S, Pin

    from es8388 import ES8388
    from pi4ioe5v import tab5_set_amp

    import board_config as bc

    ES8388(bc.i2c)
    tab5_set_amp(bc.i2c, True)
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
