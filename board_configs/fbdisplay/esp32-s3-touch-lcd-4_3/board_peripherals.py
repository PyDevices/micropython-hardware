"""Lazy constructors for contract_proof board peripherals. PERIPHERALS = lazy roles only."""
import boarddev
import sys

PERIPHERALS = frozenset({"sdcard", "can", "rs485", "usb_device", "wlan", "ble"})

_SD_MOSI = 11
_SD_SCK = 12
_SD_MISO = 13
_SD_CS_EXIO = 4  # CH422G
_CAN_TX = 15
_CAN_RX = 16
_CAN_SEL_EXIO = 5  # CH422G: high = CAN mode
_RS485_TX = 44
_RS485_RX = 43


def load_peripherals(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def sdcard():
    """TF card SPI; CS on CH422G EXIO4."""
    import board_config as bc
    from machine import Pin, SoftSPI

    from sdcard import SDCard

    cs = bc.io_expander.Pin(_SD_CS_EXIO, Pin.OUT, value=1)
    spi = SoftSPI(
        baudrate=1_000_000,
        sck=Pin(_SD_SCK),
        mosi=Pin(_SD_MOSI),
        miso=Pin(_SD_MISO),
    )
    return SDCard(spi, cs)


def can():
    """TJA1051 on GPIO15/16; EXIO5 selects CAN vs USB."""
    import board_config as bc
    import canbus

    bc.io_expander.digital_write(_CAN_SEL_EXIO, 1)
    return canbus.open(_CAN_TX, _CAN_RX, baudrate=500_000)


def rs485():
    """SP3485 auto-direction UART (TX=44, RX=43 on this panel family)."""
    from rs485 import RS485

    return RS485(1, tx=_RS485_TX, rx=_RS485_RX, baudrate=115200)


def usb_device():
    from machine import USBDevice

    return USBDevice()


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()
