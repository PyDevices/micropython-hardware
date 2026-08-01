"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset(
    {"audio_out", "audio_in", "sdcard", "camera", "radio", "wlan", "ble", "usb_device"}
)

# Waveshare wiki I2S / ES8311 pin map (P4 panel family)
_MCLK = 13
_SCLK = 12
_ASDOUT = 11
_LRCK = 10
_DSDIN = 9
_PA_CTRL = 53

from audiodev import AudioFormat, AudioSession, PCMInput, PCMOutput

_FORMAT = AudioFormat(16000, 2, 16)
_SESSION = AudioSession(codec_factory=lambda: _codec(), duplex=False)
_pa = None


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _codec():
    import board_config as bc
    from es8311 import ES8311

    return ES8311(bc.i2c)


def _output_stream():
    from machine import I2S, Pin

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


def _input_stream():
    from machine import I2S, Pin

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


def _codec_call(name, value):
    return getattr(_SESSION.get_codec(), name)(value)


def _output_power(enable):
    global _pa
    from machine import Pin

    if _pa is None:
        _pa = Pin(_PA_CTRL, Pin.OUT, value=0)
    if enable:
        _codec_call("enable_output", True)
        _pa.value(1)
    else:
        _pa.value(0)
        _codec_call("enable_output", False)


def audio_out():
    """Portable ES8311 PCM playback device with hardware volume and mute."""
    return PCMOutput(
        _output_stream,
        _FORMAT,
        session=_SESSION,
        set_hardware_volume=lambda value: _codec_call("set_dac_volume", value),
        set_hardware_mute=lambda value: _codec_call("dac_mute", value),
        power=_output_power,
    )


def audio_in():
    """Portable ES8311 PCM capture device with hardware ADC gain."""
    return PCMInput(
        _input_stream,
        _FORMAT,
        session=_SESSION,
        set_hardware_gain=lambda value: _codec_call("set_adc_volume", value),
        power=lambda enable: _codec_call("enable_input", enable),
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
