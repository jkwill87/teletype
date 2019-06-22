#!/usr/bin/env python

"""USAGE: python -m teletype [codes|components|io]

This file is only included for testing terminal capabilities. Teletype is
intended to be imported as a library, not run as a module."""

from __future__ import print_function

from sys import argv

from teletype import codes, components, io

try:
    input = raw_input
except NameError:
    pass


# CODES ------------------------------------------------------------------------


def demo_codes_chars_ascii():
    for key, value in codes.CHARS_ASCII.items():
        print("'{}' .. {}".format(value, key))


def demo_codes_chars_default():
    for key, value in codes.CHARS_DEFAULT.items():
        print("'{}' .. {}".format(value, key))


def demo_codes_colours():
    RESET = codes.MODES["reset"]
    for key, value in codes.COLOURS.items():
        print("{}{}{} .. {}".format(value, "/" * 10, RESET, key))


def demo_codes_highlights():
    RESET = codes.MODES["reset"]
    for key, value in codes.HIGHLIGHTS.items():
        print("{}{}{} .. {}".format(value, "/" * 10, RESET, key))


def demo_codes_modes():
    modes_copy = codes.MODES.copy()
    RESET = modes_copy.pop("reset")
    for key, value in modes_copy.items():
        print("{}{}{} .. {}".format(value, "/" * 10, RESET, key))


# IO ---------------------------------------------------------------------------


def demo_io_erase_lines():
    print("press [ENTER] to erase line")
    input("/" * 80)
    io.erase_lines()


def demo_io_erase_screen():
    print("press [ENTER] to erase screen")
    for _ in range(10):
        print("/" * 80)
    input()
    io.erase_screen()


def demo_io_show__hide_cursor():
    input("press [ENTER] to hide cursor")
    io.hide_cursor()
    input("press [ENTER] to show cursor")
    io.show_cursor()


def demo_io_get_key():
    print("press a key to get code. will continue after 5 keypresses.")
    count = 0
    while count < 5:
        count += 1
        print(io.get_key())


# COMPONENTS--------------------------------------------------------------------


def demo_components_selectone():
    choices = (1, 2, 3, 4, 5)

    print("No Choices")
    choice = components.SelectOne([]).prompt()
    print("choice = {}\n".format(choice))

    print("Basic")
    choice = components.SelectOne(choices).prompt()
    print("choice = {}\n".format(choice))

    print("ASCII Chars")
    choice = components.SelectOne(choices, **codes.CHARS_ASCII).prompt()
    print("choice = {}\n".format(choice))

    print("Styled Chars")
    arrow = io.style_format(codes.CHARS_DEFAULT["arrow"], "blue")
    choice = components.SelectOne(choices, arrow=arrow).prompt()
    print("choice = {}\n".format(choice))

    print("ChoiceHelper")
    five = components.ChoiceHelper(5, "five", "red bold", "f")
    six = components.ChoiceHelper(6, "six", "yellow italic", "[s]")
    choice = components.SelectOne((five, six)).prompt()
    print("choice = {}\n".format(choice))


def demo_components_selectapproval():
    choice = components.SelectApproval()
    print("choice = {}".format(choice))


def demo_components_selectmany():
    choices = (1, 2, 3, 4, 5)

    print("No Choices")
    choice = components.SelectMany([]).prompt()
    print("choice = {}\n".format(choice))

    print("Basic")
    choice = components.SelectMany(choices).prompt()
    print("choice = {}\n".format(choice))

    print("ASCII Chars")
    choice = components.SelectMany(choices, **codes.CHARS_ASCII).prompt()
    print("choice = {}\n".format(choice))

    print("Styled Chars")
    arrow = io.style_format(codes.CHARS_DEFAULT["arrow"], "blue")
    choice = components.SelectMany(choices, arrow=arrow).prompt()
    print("choice = {}\n".format(choice))

    print("ChoiceHelper")
    five = components.ChoiceHelper(5, "five", "red bold", "f")
    six = components.ChoiceHelper(6, "six", "yellow italic", "[s]")
    choice = components.SelectMany((five, six)).prompt()
    print("choice = {}\n".format(choice))


def demo_components_progressbar():
    print("Press any key to progress\n")

    progressbar = components.ProgressBar("Basic ProgressBar")
    for i in range(0, 6):
        progressbar.update(i, 5)
        io.get_key()
    print()

    progressbar = components.ProgressBar("Fixed Width ProgressBar", width=25)
    for i in range(0, 6):
        progressbar.update(i, 5)
        io.get_key()
    print()

    progressbar = components.ProgressBar(
        "ASCII ProgressBar", **codes.CHARS_ASCII
    )
    for i in range(0, 6):
        progressbar.update(i, 5)
        io.get_key()
    print()

    style = codes.CHARS_DEFAULT.copy()
    style["block"] = io.style_format(style["block"], "yellow")
    style["left-edge"] = io.style_format(style["left-edge"], "green")
    style["right-edge"] = io.style_format(style["right-edge"], "green")
    title = io.style_format("Styled ProgressBar", "bold green")
    progressbar = components.ProgressBar(title, **style)
    for i in range(0, 6):
        progressbar.update(i, 5)
        io.get_key()


# ENTRYPOINT -------------------------------------------------------------------


def demo():
    print(__doc__)
    tests_codes = {
        demo_codes_chars_ascii,
        demo_codes_chars_default,
        demo_codes_colours,
        demo_codes_highlights,
        demo_codes_modes,
    }
    tests_io = {
        demo_io_erase_lines,
        demo_io_erase_screen,
        demo_io_get_key,
        demo_io_show__hide_cursor,
    }
    tests_components = {
        demo_components_selectone,
        demo_components_selectapproval,
        demo_components_selectmany,
        demo_components_progressbar,
    }

    suite = set()
    if "codes" in argv:
        suite |= tests_codes
    if "io" in argv:
        suite |= tests_io
    if "components" in argv:
        suite |= tests_components
    if "all" in argv:
        suite = tests_codes | tests_components | tests_io
    for i, fn in enumerate(suite, 1):
        prefix = "== RUNNING TEST {}: {} ".format(i, fn.__name__)
        suffix = "=" * (80 - len(prefix))
        print("\n{}{}\n".format(prefix, suffix))
        fn()
        print()


if __name__ == "__main__":
    demo()
