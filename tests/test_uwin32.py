import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401


class Uwin32ImportTests(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "uwin32 loads on Windows")
    def test_import_fails_off_windows(self):
        with self.assertRaises(ImportError):
            import uwin32  # noqa: F401

    @unittest.skipUnless(sys.platform == "win32", "uwin32 is Windows only")
    def test_import_on_windows(self):
        import uwin32

        self.assertTrue(hasattr(uwin32, "CreateWindowExW"))
        self.assertTrue(hasattr(uwin32, "CreateWaitableTimerExW"))
        self.assertTrue(hasattr(uwin32, "IAudioClient_Initialize_shared_pcm"))
        self.assertTrue(hasattr(uwin32, "RegisterClassExW"))
        self.assertTrue(hasattr(uwin32, "StretchDIBits"))
        self.assertTrue(hasattr(uwin32, "DefWindowProcW"))
        self.assertTrue(hasattr(uwin32, "WNDCLASSEXW"))
        self.assertTrue(hasattr(uwin32, "PAINTSTRUCT"))
        self.assertTrue(hasattr(uwin32, "RECT"))
        for name in ("bmi_rgb565", "dib_bits", "buffer_at", "VirtualAlloc", "VirtualFree", "GetPixel"):
            self.assertTrue(hasattr(uwin32, name), name)


@unittest.skipUnless(sys.platform == "win32", "uwin32 is Windows only")
class Uwin32RGB565Tests(unittest.TestCase):
    """The 16-bit BI_BITFIELDS header WinDisplay presents its framebuffer with."""

    def _header(self, bmi):
        import struct

        buf = bmi._buf if hasattr(bmi, "_buf") else memoryview(bmi).cast("B")
        return bytes(buf)

    def test_header_is_top_down_rgb565(self):
        import struct

        import uwin32

        raw = self._header(uwin32.bmi_rgb565(320, 240))
        size, width, height, planes, bits, compression, image = struct.unpack_from(
            "<IiiHHII", raw, 0
        )
        self.assertEqual(size, 40)
        self.assertEqual(width, 320)
        self.assertEqual(height, -240, "must be top-down")
        self.assertEqual(planes, 1)
        self.assertEqual(bits, 16)
        self.assertEqual(compression, uwin32.BI_BITFIELDS)
        self.assertEqual(image, 320 * 240 * 2)

    def test_channel_masks_follow_the_header(self):
        import struct

        import uwin32

        raw = self._header(uwin32.bmi_rgb565(320, 240))
        self.assertEqual(struct.unpack_from("<III", raw, 40), (0xF800, 0x07E0, 0x001F))

    def test_odd_width_rejected(self):
        import uwin32

        # RGB565 scanlines are only DWORD-aligned at even widths.
        with self.assertRaises(ValueError):
            uwin32.bmi_rgb565(321, 240)

    def test_virtual_alloc_roundtrip(self):
        import uwin32

        ptr = uwin32.VirtualAlloc(4096)
        self.assertTrue(ptr)
        try:
            view = uwin32.buffer_at(ptr, 16)
            self.assertEqual(bytes(view[:4]), b"\x00\x00\x00\x00", "pages arrive zeroed")
            view[0:4] = b"\xde\xad\xbe\xef"
            self.assertEqual(bytes(uwin32.buffer_at(ptr, 4)), b"\xde\xad\xbe\xef")
            del view
        finally:
            self.assertTrue(uwin32.VirtualFree(ptr))

    def test_dib_bits_is_an_address(self):
        import uwin32

        buf = bytearray(64)
        addr = uwin32.dib_bits(buf)
        self.assertIsInstance(addr, int)
        self.assertTrue(addr)
        # Stable across calls, so a cached base plus a scanline offset is valid.
        self.assertEqual(addr, uwin32.dib_bits(buf))


if __name__ == "__main__":
    unittest.main()
