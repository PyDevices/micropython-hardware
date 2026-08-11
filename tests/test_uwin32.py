import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401


class Uwin32ImportTests(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "uwin32 loads on Windows CPython")
    def test_import_fails_off_windows(self):
        with self.assertRaises(ImportError):
            import uwin32  # noqa: F401

    @unittest.skipUnless(sys.platform == "win32", "uwin32 is Windows CPython only")
    def test_import_on_windows(self):
        import uwin32

        self.assertTrue(hasattr(uwin32, "CreateWindowExW"))
        self.assertTrue(hasattr(uwin32, "CreateWaitableTimerExW"))
        self.assertTrue(hasattr(uwin32, "IAudioClient_Initialize_shared_pcm"))


if __name__ == "__main__":
    unittest.main()
