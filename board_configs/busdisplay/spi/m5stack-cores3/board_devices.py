"""Lazy constructors for M5Stack CoreS3 non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset(
    {
        "microphone",
        "audio",
        "sdcard",
        "camera",
        "accelerometer",
        "gyroscope",
        "i2c",
        "wlan",
        "ble",
    }
)


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    import board_config as bc

    return bc.i2c


def microphone():
    raise NotImplementedError("CoreS3 ES7210/PDM mic needs codec bring-up")


def audio():
    raise NotImplementedError("CoreS3 AW88298/I2S audio needs codec bring-up")


def sdcard():
    """CoreS3 microSD via SDMMC when firmware exposes machine.SDCard."""
    from machine import SDCard

    return SDCard()


def camera():
    raise NotImplementedError("CoreS3 camera needs native CSI / GC0308 support")


def accelerometer():
    raise NotImplementedError("CoreS3 BMI270/IMU driver not vendored yet")


def gyroscope():
    raise NotImplementedError("CoreS3 BMI270/IMU driver not vendored yet")


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()
