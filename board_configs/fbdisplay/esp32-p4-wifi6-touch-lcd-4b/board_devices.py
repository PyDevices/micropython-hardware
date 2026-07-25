"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset(
    {"audio", "microphone", "sdcard", "camera", "radio", "wlan", "ble", "usb_device"}
)

# Waveshare wiki I2S / ES8311 pin map (P4 panel family)
_MCLK = 13
_SCLK = 12
_ASDOUT = 11
_LRCK = 10
_DSDIN = 9
_PA_CTRL = 53


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _codec():
    import board_config as bc
    from es8311 import ES8311

    return ES8311(bc.i2c)


def audio():
    """ES8311 DAC + I2S TX (+ PA enable)."""
    from machine import I2S, Pin

    codec = _codec()
    codec.dac_mute(False)
    Pin(_PA_CTRL, Pin.OUT, value=1)
    return I2S(
        0,
        sck=Pin(_SCLK),
        ws=Pin(_LRCK),
        sd=Pin(_DSDIN),
        mck=Pin(_MCLK),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=16000,
        ibuf=20000,
    )


def microphone():
    """ES8311 ADC + I2S RX (ES7210 AEC left to firmware/apps)."""
    from machine import I2S, Pin

    _codec()
    return I2S(
        0,
        sck=Pin(_SCLK),
        ws=Pin(_LRCK),
        sd=Pin(_ASDOUT),
        mck=Pin(_MCLK),
        mode=I2S.RX,
        bits=16,
        format=I2S.STEREO,
        rate=16000,
        ibuf=20000,
    )


def sdcard():
    """TF card via SDIO 3.0 (``machine.SDCard``)."""
    from machine import SDCard

    try:
        return SDCard()
    except TypeError:
        return SDCard(slot=0)


def camera():
    raise NotImplementedError(
        "MIPI CSI camera needs a native camera module in firmware; no single-file driver"
    )


def radio():
    """ESP32-C6 SDIO co-processor — same NIC as ``wlan`` on P4 builds."""
    return wlan()


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()


def usb_device():
    from machine import USBDevice

    return USBDevice()
