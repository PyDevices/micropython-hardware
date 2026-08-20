# Input drivers

Helpers for wiring physical buttons and encoders into `appdev`.

## `keypad_gpio.py`

Maps GPIO buttons to `appdev.KEYPAD` key codes.

```python
import appdev
import keys
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS

buttons = GPIOButtons({
    "a": (board.BUTTON_A, keys.K_a),
    "b": (board.BUTTON_B, keys.K_b),
})

app = appdev.App(display=display_drv)
app.add_keypad(read=buttons.read)
```

Used by MagTag, PyBadge, and similar boards with front-panel buttons.
