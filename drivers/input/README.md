# Input drivers

Helpers for wiring physical buttons and encoders into `eventsys`.

## `keypad_gpio.py`

Maps GPIO buttons to `eventsys.KEYPAD` key codes.

```python
import eventsys
import keys
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS

buttons = GPIOButtons({
    "a": (board.BUTTON_A, keys.K_a),
    "b": (board.BUTTON_B, keys.K_b),
})

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
```

Used by MagTag, PyBadge, and similar boards with front-panel buttons.
