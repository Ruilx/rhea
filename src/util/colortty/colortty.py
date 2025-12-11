# -*- coding: utf-8 -*-
import enum
from typing import Optional, Any, Callable, Self


class ColorTTY(object):
    """
    A class to generate colored text for TTY (terminal) output using ANSI escape codes.
    # Example usage:
    ## import
        from colortty import colortty, ColorTTY
    ## Usage1:
        colortty("Any_string").set(ColorTTY.Color.red()).set(ColorTTY.BackgroundColor.blue()).make() -> "\033[31;44mAny_string\033[0m"
    ## Usage2:
        red_string = colortty().set(ColorTTY.Color.red())
        red_string.make("Hello, world!") -> "\033[31mHello, world!\033[0m"
    """

    Reset = "[0m"
    EscapeChar = "\033"

    class Statement(object):
        def __init__(self, color_obj: "ColorTTY"):
            self.color_obj = color_obj

        def set(self, method: Callable[["ColorTTY"], None]) -> Self:
            if not callable(method):
                raise RuntimeError("method is not callable")
            method(self.color_obj)
            return self

        def make(self, s: Optional[str] = None):
            return self.color_obj.make(s)

    class Mode(enum.Enum):
        Color = enum.auto()
        BackgroundColor = enum.auto()
        Lighter = enum.auto()
        BackgroundLighter = enum.auto()
        Bold = enum.auto()
        Underline = enum.auto()
        Sparking = enum.auto()
        Inverse = enum.auto()
        Invisible = enum.auto()

    Color = None
    BackgroundColor = None

    def __init__(self, s: Optional[str] = None):
        self.s = s
        self.attr: dict[ColorTTY.Mode, Optional[int]] = {
            self.Mode.Color: None,
            self.Mode.BackgroundColor: None,
            self.Mode.Lighter: None,
            self.Mode.BackgroundLighter: None,
            self.Mode.Bold: None,
            self.Mode.Underline: None,
            self.Mode.Sparking: None,
            self.Mode.Inverse: None,
            self.Mode.Invisible: None,
        }

    def set_attr(self, mode: Mode, val: Any):
        self.attr[mode] = val

    def statement(self):
        return ColorTTY.Statement(self)

    @staticmethod
    def _build_color(base: int, color: int, lighter: int, parts: list) -> None:
        if color & 0x0F < 8:
            parts.append(base + color + (60 if lighter else 0))
        elif color & 0x0F == 8:
            parts.append(base + 8)
            if color & 0xF0 == 0x10:
                # 24 bits true colors
                parts.append(2)
                parts.append((color & 0xFF000000) >> 0x18)
                parts.append((color & 0x00FF0000) >> 0x10)
                parts.append((color & 0x0000FF00) >> 0x08)
            elif color & 0xF0 == 0x20:
                # 256 colors
                parts.append(5)
                parts.append((color & 0x0000FF00) >> 0x08)
            else:
                raise ValueError(f"Color mode: '{hex(color & 0xF0)}' is not supported.")
        else:
            raise ValueError(f"Color value: '{hex(color & 0x08)}' is not valid.")

    def make(self, s: Optional[str]):
        string = self.s
        if isinstance(s, str):
            string = s
        parts = []
        if isinstance(self.attr[self.Mode.Color], int):
            ColorTTY._build_color(30, self.attr[self.Mode.Color], self.attr[self.Mode.Lighter], parts)
        if isinstance(self.attr[self.Mode.BackgroundColor], int):
            ColorTTY._build_color(40, self.attr[self.Mode.BackgroundColor], self.attr[self.Mode.BackgroundLighter], parts)
        if isinstance(self.attr[self.Mode.Bold], int) and self.attr[self.Mode.Bold]:
            parts.append(1)
        if isinstance(self.attr[self.Mode.Underline], int) and self.attr[self.Mode.Underline]:
            parts.append(4)
        if isinstance(self.attr[self.Mode.Sparking], int) and self.attr[self.Mode.Sparking]:
            parts.append(5)
        if isinstance(self.attr[self.Mode.Inverse], int) and self.attr[self.Mode.Inverse]:
            parts.append(7)
        if isinstance(self.attr[self.Mode.Invisible], int) and self.attr[self.Mode.Invisible]:
            parts.append(8)
        return f"{ColorTTY.EscapeChar}[{';'.join(map(lambda x: str(x), parts))}m{string}{ColorTTY.EscapeChar}{ColorTTY.Reset}"

    def __str__(self):
        return self.make(self.s)


def colortty(s: Optional[str] = None):
    return ColorTTY(s).statement()


class _Color(object):
    ColorTarget = ColorTTY.Mode.Color
    LighterTarget = ColorTTY.Mode.Lighter

    def black(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 0)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def red(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 1)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def green(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 2)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def yellow(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 3)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def blue(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 4)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def magenta(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 5)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def cyan(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 6)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def white(self, lighter: bool = False):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 7)
            color_obj.set_attr(self.LighterTarget, int(lighter))

        return _

    def color_256(self, index: int):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 0x28 | ((index & 0xFF) << 8))

        return _

    def color(self, r: int, g: int, b: int):
        def _(color_obj: ColorTTY):
            color_obj.set_attr(self.ColorTarget, 0x18 | ((r & 0xFF) << 24) | (g & 0xFF) << 16 | (b & 0xFF) << 8)

        return _


color = ColorTTY.Color = _Color()


class _BackgroundColor(_Color):
    ColorTarget = ColorTTY.Mode.BackgroundColor
    LighterTarget = ColorTTY.Mode.BackgroundLighter


background_color = ColorTTY.BackgroundColor = _BackgroundColor()


def bold(enable: bool = True):
    def _(color_obj: ColorTTY):
        color_obj.set_attr(ColorTTY.Mode.Bold, 1 and enable)

    return _


def underline(enable: bool = True):
    def _(color_obj: ColorTTY):
        color_obj.set_attr(ColorTTY.Mode.Underline, 4 and enable)

    return _


def sparking(enable: bool = True):
    def _(color_obj: ColorTTY):
        color_obj.set_attr(ColorTTY.Mode.Sparking, 5 and enable)

    return _


def inverse(enable: bool = True):
    def _(color_obj: ColorTTY):
        color_obj.set_attr(ColorTTY.Mode.Inverse, 7 and enable)

    return _


def invisible(enable: bool = True):
    def _(color_obj: ColorTTY):
        color_obj.set_attr(ColorTTY.Mode.Invisible, 8 and enable)

    return _


if __name__ == "__main__":
    p = colortty()
    for i in range(0, 256, 16):
        for j in range(0, 256, 16):
            for k in range(0, 256, 16):
                p.set(color.color(i, j, k))
                p.set(sparking(j & 0x10 and True))
                p.set(bold(k & 0x10 and True))
                p.set(underline(i & 0x10 and True))
                print(p.make(f"#{i:02x}{j:02x}{k:02x}"), end=" ")
