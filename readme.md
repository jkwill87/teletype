[![pypi](https://img.shields.io/pypi/v/teletype.svg?style=for-the-badge)](https://pypi.python.org/pypi/teletype)
[![licence](https://img.shields.io/github/license/jkwill87/teletype.svg?style=for-the-badge)](https://en.wikipedia.org/wiki/MIT_License)
[![code style black](https://img.shields.io/badge/Code%20Style-Black-black.svg?style=for-the-badge)](https://github.com/ambv/black)


# teletype

**teletype** is a high-level cross platform tty library compatible with Python 2.7 and 3+. It provides a consistent interface between the terminal and cmd.exe by building on top of [terminfo](https://invisible-island.net/ncurses/terminfo.src.html) and [msvcrt](https://msdn.microsoft.com/en-us/library/abx4dbyh.aspx) and has no dependancies.


# Installation

`$ pip install teletype`


# I/O Utilities (teletype.io)

## Reading Key Strokes

You can read keystrokes from stdin using `get_key`. Regular keys get returned as a string with a single character, e.g. `"a"`, `"1"`, `"&"`, etc., while special keys and key combinations are returned as a string description, e.g. `"space"`, `"f12"`, `"page-up"`, `"ctrl-c"`, etc. A listing of the supported key combinations are listed in the [`codes`](https://github.com/jkwill87/teletype/blob/master/teletype/codes/common.py) module.

```python
from teletype.io import get_key

print("Delete C:/ Drive? [y/n]")
selection = ""
while selection.lower() not in ("y", "n"):
    selection = get_key()
    if selection in ("ctrl-c", "ctrl-z", "escape"):
        selection = "n"
if selection == "y":
    print("Deleting C:/ drive...")
    delete_c_drive()
else:
    print("Leaving C:/ drive alone")
```

## Styling Output

You can style strings with COLOURS and effects using `style_format`. Styles can be passed in either as a space delimited string or in a collection (e.g. a tuple, set, list, etc.). The passed `text` string is then wrapped in the appropriate ASCII escape sequences and returned. When `print`ed the appropriate styles will be applied.

Alternatively you can you just pass these same parameters to `style_print` and accomplish this in one fell swoop. `style_print` takes the same parameters as the regular print function and can be used in place. In python3 you can even import style_print as print and use it in place. In order to pull this compatibility off for python2, the `style` argument must be specified explitly when calling, however, e.g. `style_print("yolo", style="yellow")`.

Lastly, you can use `strip_format` to clear a string of any escape sequences that have been previously applied.

```python
from teletype.io import style_format, style_print, strip_format

# All of these will do the same thing, that is print the message in red and bold
print(style_format("I want to stand out!", "bold red"))
print(style_format("I want to stand out!", ("red", "bold")))
style_print("I want to stand out!", style=["red", "bold"])

# Styles are cleared afterwards so everything else gets printed normally
print("I want to be boring")

# If for whatever reason you want to unstyle text, thats a thing too
text = style_format("I don't actually want too be styled", ("red", "bold"))
print(strip_format(text))
```

## Cursor manipulation

The package includes quite a few helper functions to move the CURSOR around the screen. These include `erase_lines`, `erase_screen`, `hide_cursor`, `show_cursor`, and `move_cursor`; all of which are fairly self explanitory. The only word of caution is to remember to reset CURSOR visibility as its state will persist after the python interpreter has exited.


# Components (teletype.components)

The package also includes components, higher level UI classes that are composed from the I/O functions and can be easily incorporated to any CLI application.

## SelectOne

```python
from teletype.components import Select

picker = Select(
    header="Your Favourite Animal?",
    choices=["dog", "bird", "cat", "monkey", "gorilla"],
)
choice = picker.prompt()
print("Your choice: " + choice)
```

![Output](https://github.com/jkwill87/teletype/blob/master/_assets/select_one.gif)

## SelectMany

```python
from teletype.components import SelectMany

picker = SelectMany(
    header="Your Favourite Animals?",
    choices=["dog", "bird", "cat", "monkey", "gorilla"],
)
choices = picker.prompt()
print("Your choices: " + ", ".join(choices))
```

![Output](https://github.com/jkwill87/teletype/blob/master/_assets/select_many.gif)

## ProgressBar

```python
from time import sleep
from teletype.components import ProgressBar

iterations = 15

def iterable():
    for _ in range(iterations):
        sleep(0.2)
        yield

ProgressBar().process(iterable(), iterations)
```

![Output](https://github.com/jkwill87/teletype/blob/master/_assets/progress_bar.gif)

## Styling Components (teletype.components.config)

You can set component primary and secondary styles using `set_style`.

```python
from teletype.components import ProgressBar, SelectMany

config = {"style_primary": "yellow", "style_secondary": "magenta"}
iterable = range(25)
choices = (1, 2, 3)

ProgressBar(header="Progress Bar", **config).process(iterable)
SelectMany(choices, header="Select Many", **config).prompt()
```

![Output](https://github.com/jkwill87/teletype/blob/master/_assets/style.png)

You can also change character sets using `set_char(key, value)` where value is the unicode character you want to use and key is one of:

- selected
- unselected
- arrow
- block
- left-edge
- right-edge

Lastly, you can also use **ascii_mode(enabled=True)** to quickly disable colour stylings and swap to a ascii-only character set.


# License

MIT. See license.txt for details.
