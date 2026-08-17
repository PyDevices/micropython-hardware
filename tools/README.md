# pydevices `tools/`

Developer diagnostics and package-release smoke tests owned by the portable
PyDevices core.

| Script | Purpose |
|---|---|
| [`input_probe.py`](input_probe.py) | Core displaydev/eventsys keyboard and keypad diagnostics |
| [`test_timers.py`](test_timers.py) | Public multimer timer probe for any supported interpreter |
| [`test_testpypi_standalone.sh`](test_testpypi_standalone.sh) | Isolated TestPyPI import checks for core distributions; `--desktop` adds host backends |

From the repository root:

```bash
python tools/input_probe.py --selftest
micropython tools/input_probe.py --selftest

python tools/test_timers.py
micropython tools/test_timers.py
circuitpython tools/test_timers.py

./tools/test_testpypi_standalone.sh
./tools/test_testpypi_standalone.sh --desktop
```

The cross-runtime timer runner and LVGL-specific input diagnostics remain in
the sibling `pydevices-examples` integration repository.
