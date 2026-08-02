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

# 24 kHz mono matches Gemini TTS. Firmware has no I2S mck= — PWM supplies MCLK.
# Bring-up (ear-verified): MCLK before ES8311 init; unmute + volume before I2S; MONO.
_RATE = 24000
_FORMAT = AudioFormat(_RATE, 1, 16)
_DEFAULT_VOLUME = 50
_SESSION = AudioSession(codec_factory=lambda: _codec(), duplex=False)
_pa = None
_mclk = None


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _ensure_mclk():
    """ES8311 needs MCLK = sample_rate × 256 on GPIO13 before codec init."""
    global _mclk
    from machine import PWM, Pin

    freq = _RATE * 256
    if _mclk is None:
        _mclk = PWM(Pin(_MCLK), freq=freq, duty_u16=32768)
    else:
        _mclk.freq(freq)
    return _mclk


def _stop_mclk():
    global _mclk
    if _mclk is None:
        return
    try:
        _mclk.deinit()
    except Exception:
        pass
    _mclk = None


def _codec():
    import board_config as bc
    from es8311 import ES8311

    _ensure_mclk()
    codec = ES8311(bc.i2c)
    # Enable path before I2S starts (PCMOutput opens the stream next).
    codec.enable_output(True)
    codec.dac_mute(False)
    codec.set_dac_volume(_DEFAULT_VOLUME)
    return codec


def _output_stream():
    from machine import I2S, Pin

    _ensure_mclk()
    return I2S(
        0,
        sck=Pin(_SCLK),
        ws=Pin(_LRCK),
        sd=Pin(_DSDIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=_RATE,
        ibuf=20000,
    )


def _input_stream():
    from machine import I2S, Pin

    _ensure_mclk()
    return I2S(
        0,
        sck=Pin(_SCLK),
        ws=Pin(_LRCK),
        sd=Pin(_ASDOUT),
        mode=I2S.RX,
        bits=16,
        format=I2S.MONO,
        rate=_RATE,
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
        _ensure_mclk()
        _codec_call("enable_output", True)
        _pa.value(1)
    else:
        _pa.value(0)
        _codec_call("enable_output", False)


def audio_out():
    """Portable ES8311 PCM playback device with hardware volume and mute."""
    out = PCMOutput(
        _output_stream,
        _FORMAT,
        session=_SESSION,
        set_hardware_volume=lambda value: _codec_call("set_dac_volume", value),
        set_hardware_mute=lambda value: _codec_call("dac_mute", value),
        power=_output_power,
    )
    out.set_volume(_DEFAULT_VOLUME)
    return out


def _input_power(enable):
    if enable:
        _ensure_mclk()
        _codec_call("enable_input", True)
    else:
        _codec_call("enable_input", False)


def audio_in():
    """Portable ES8311 PCM capture device with hardware ADC gain."""
    return PCMInput(
        _input_stream,
        _FORMAT,
        session=_SESSION,
        set_hardware_gain=lambda value: _codec_call("set_adc_volume", value),
        power=_input_power,
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
