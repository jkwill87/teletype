[![pypi](https://img.shields.io/pypi/v/teletype.svg?style=for-the-badge)](https://pypi.python.org/pypi/teletype)
[![licence](https://img.shields.io/github/license/jkwill87/teletype.svg?style=for-the-badge)](https://en.wikipedia.org/wiki/MIT_License)
[![code style black](https://img.shields.io/badge/Code%20Style-Black-black.svg?style=for-the-badge)](https://github.com/ambv/black)


# teletype

**teletype** is a high-level cross platform tty library compatible with Python 3.7+. It provides a consistent interface between the terminal and cmd.exe by building on top of [terminfo](https://invisible-island.net/ncurses/terminfo.src.html) and [msvcrt](https://msdn.microsoft.com/en-us/library/abx4dbyh.aspx) and has no dependencies.


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
In [1]: from teletype.components import SelectOne
   ...:
   ...: picker = SelectOne(choices=["dog", "bird", "cat", "monkey", "gorilla"])
   ...: print("Your Favourite Animal?")
   ...: choice = picker.prompt()
   ...: print("Your choice: " + choice)
```

```
Your Favourite Animal?
 ❱ dog
   bird
   cat
   monkey
   gorilla
Your choice: dog
```

## SelectMany

```python
In [2]: from teletype.components import SelectMany
   ...:
   ...: picker = SelectMany(choices=["dog", "bird", "cat", "monkey", "gorilla"])
   ...: print("Your Favourite Animals?")
   ...: choices = picker.prompt()
   ...: print("Your choices: " + ", ".join(choices))
```

```
Your Favourite Animals?
❱● dog
 ○ bird
 ○ cat
 ○ monkey
 ○ gorilla
Your choices: dog
```

## ProgressBar

```python
In [3]: from time import sleep
   ...: from teletype.components import ProgressBar
   ...:
   ...: iterations = 15
   ...:
   ...: def iterable():
   ...:     for _ in range(iterations):
   ...:         sleep(0.2)
   ...:         yield
   ...:
   ...: ProgressBar("Progress Bar").process(iterable(), iterations)
```

```
Progress Bar: 15/15▐████████████████████████████████████████████████▌100%
```

## ChoiceHelper

Although not a component in and of itself, `ChoiceHelper` can help you wrap your objects to make full use of components like `SelectOne`, `SelectMany`, or `SelectApproval`. This is completely optional-- normally these just use the string representations of objects for display, e.g. just printing options which are strings or calling their underlying `__str__` methods.

### Seperate Values from Labels

Sometimes this isn't an option or you might want to seperate the label of an object from its value. `ChoiceHelper` lets you specifiy these fields explicitly. You can apply styles, too.

```python
In [4]: from teletype.components import SelectOne, ChoiceHelper
   ...:
   ...: choices = [
   ...:     ChoiceHelper(["corgi", "greyhound", "bulldog"], label="dog", style="blue"),
   ...:     ChoiceHelper(["siamese", "chartreux", "ragdoll"], label="cat", style="red"),
   ...:     ChoiceHelper(["zebra", "beta", "gold"], "fish", style="green")
   ...: ]
   ...:
   ...: print("favourite pet")
   ...: pet = SelectOne(choices).prompt()
   ...:
   ...: print("favourite breed")
   ...: breed = SelectOne(pet).prompt()
```

```
favourite pet
 ❱ dog
   cat
   fish

favourite breed
 ❱ corgi
   greyhound
   bulldog
```

### Mnemonics

Another cool thing that `ChoiceHelper`s let you do is use mneumonics. These can be specified either using a single character, in which case they are underlined, or as a single character wrapped in square brackets, in which case they will be indicated using square brackets (e.g. for compatibility with dumb terminals).

This is used under the hood for `SelectApproval` to quickly select yes by pressing `y` and no by pressing `n`.

## Styling Components (teletype.components.config)

You can set component styles using `io.style_format`.

```python
from teletype.io import style_format, style_print
from teletype.components import ProgressBar, SelectMany

style = "red bold"
arrow = io.style_format(CHARS_DEFAULT["arrow"], style)
choices = ["dogs", "cats", "fish"]

io.style_print("\nSelect One", style=style)
SelectOne(choices, arrow=arrow).prompt()
```

You can also change character sets using `set_char(key, value)` where value is the unicode character you want to use and key is one of:

- `arrow`
- `block`
- `left-edge`
- `right-edge`
- `selected`
- `unselected`


# License

MIT. See license.txt for details.
