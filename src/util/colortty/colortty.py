# -*- coding: utf-8 -*-
import enum
import os
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

        def __str__(self):
            if not self.color_obj.get_string():
                return self.__repr__()
            else:
                return self.color_obj.make()

        def __repr__(self):
            return f"<{self.__class__.__name__} from {self.color_obj.__class__.__name__} {self.color_obj._dump_attrs()}>"

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

    def _dump_attrs(self, with_color: bool = False):
        attrs_desc = []
        if self.attr[self.Mode.Color] is not None:
            attrs_desc.append(f"Fore: {"light " if self.attr[self.Mode.Lighter] else ''}{_Color.get_color_name(self.attr[self.Mode.Color], with_color)}")
        if self.attr[self.Mode.BackgroundColor] is not None:
            attrs_desc.append(f"Back: {"light " if self.attr[self.Mode.Lighter] else ''}{_Color.get_color_name(self.attr[self.Mode.BackgroundColor], with_color)}")
        if self.attr[self.Mode.Bold] is not None and self.attr[self.Mode.Bold] == True:
            attrs_desc.append("Bold")
        if self.attr[self.Mode.Underline] is not None and self.attr[self.Mode.Underline] == True:
            attrs_desc.append("Underline")
        if self.attr[self.Mode.Sparking] is not None and self.attr[self.Mode.Sparking] == True:
            attrs_desc.append("Sparking")
        if self.attr[self.Mode.Inverse] is not None and self.attr[self.Mode.Inverse] == True:
            attrs_desc.append("Inverse")
        if self.attr[self.Mode.Invisible] is not None and self.attr[self.Mode.Invisible] == True:
            attrs_desc.append("Invisible")
        return ",".join(attrs_desc)

    def set_attr(self, mode: Mode, val: Any):
        self.attr[mode] = val

    def get_attr(self, mode: Mode) -> Optional[Any]:
        return self.attr[mode] if mode in self.attr else None

    def get_string(self) -> str:
        return self.s

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

    def make(self, s: Optional[str] = None):
        string = self.s
        if isinstance(s, str):
            string = s
        if string is None:
            return ""
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
        return self.make(self.s) if self.s else '<string not set>'

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._dump_attrs()}>"


def colortty(s: Optional[str] = None):
    return ColorTTY(s).statement()


class _Color(object):
    ColorTarget = ColorTTY.Mode.Color
    LighterTarget = ColorTTY.Mode.Lighter

    Color256Index = (
        ("Black", "000000", "rgb(0, 0, 0)"),
        ("Maroon", "800000", "rgb(128, 0, 0)"),
        ("Green", "008000", "rgb(0, 128, 0)"),
        ("Olive", "808000", "rgb(128, 128, 0)"),
        ("Navy", "000080", "rgb(0, 0, 128)"),
        ("Purple", "800080", "rgb(128, 0, 128)"),
        ("Teal", "008080", "rgb(0, 128, 128)"),
        ("Silver", "c0c0c0", "rgb(192, 192, 192)"),
        ("Grey", "808080", "rgb(128, 128, 128)"),
        ("Red", "ff0000", "rgb(255, 0, 0)"),
        ("Lime", "00ff00", "rgb(0, 255, 0)"),
        ("Yellow", "ffff00", "rgb(255, 255, 0)"),
        ("Blue", "0000ff", "rgb(0, 0, 255)"),
        ("Fuchsia", "ff00ff", "rgb(255, 0, 255)"),
        ("Aqua", "00ffff", "rgb(0, 255, 255)"),
        ("White", "ffffff", "rgb(255, 255, 255)"),
        ("Grey0", "000000", "rgb(0, 0, 0)"),
        ("NavyBlue", "00005f", "rgb(0, 0, 95)"),
        ("DarkBlue", "000087", "rgb(0, 0, 135)"),
        ("Blue3", "0000af", "rgb(0, 0, 175)"),
        ("Blue3", "0000d7", "rgb(0, 0, 215)"),
        ("Blue1", "0000ff", "rgb(0, 0, 255)"),
        ("DarkGreen", "005f00", "rgb(0, 95, 0)"),
        ("DeepSkyBlue4", "005f5f", "rgb(0, 95, 95)"),
        ("DeepSkyBlue4", "005f87", "rgb(0, 95, 135)"),
        ("DeepSkyBlue4", "005faf", "rgb(0, 95, 175)"),
        ("DodgerBlue3", "005fd7", "rgb(0, 95, 215)"),
        ("DodgerBlue2", "005fff", "rgb(0, 95, 255)"),
        ("Green4", "008700", "rgb(0, 135, 0)"),
        ("SpringGreen4", "00875f", "rgb(0, 135, 95)"),
        ("Turquoise4", "008787", "rgb(0, 135, 135)"),
        ("DeepSkyBlue3", "0087af", "rgb(0, 135, 175)"),
        ("DeepSkyBlue3", "0087d7", "rgb(0, 135, 215)"),
        ("DodgerBlue1", "0087ff", "rgb(0, 135, 255)"),
        ("Green3", "00af00", "rgb(0, 175, 0)"),
        ("SpringGreen3", "00af5f", "rgb(0, 175, 95)"),
        ("DarkCyan", "00af87", "rgb(0, 175, 135)"),
        ("LightSeaGreen", "00afaf", "rgb(0, 175, 175)"),
        ("DeepSkyBlue2", "00afd7", "rgb(0, 175, 215)"),
        ("DeepSkyBlue1", "00afff", "rgb(0, 175, 255)"),
        ("Green3", "00d700", "rgb(0, 215, 0)"),
        ("SpringGreen3", "00d75f", "rgb(0, 215, 95)"),
        ("SpringGreen2", "00d787", "rgb(0, 215, 135)"),
        ("Cyan3", "00d7af", "rgb(0, 215, 175)"),
        ("DarkTurquoise", "00d7d7", "rgb(0, 215, 215)"),
        ("Turquoise2", "00d7ff", "rgb(0, 215, 255)"),
        ("Green1", "00ff00", "rgb(0, 255, 0)"),
        ("SpringGreen2", "00ff5f", "rgb(0, 255, 95)"),
        ("SpringGreen1", "00ff87", "rgb(0, 255, 135)"),
        ("MediumSpringGreen", "00ffaf", "rgb(0, 255, 175)"),
        ("Cyan2", "00ffd7", "rgb(0, 255, 215)"),
        ("Cyan1", "00ffff", "rgb(0, 255, 255)"),
        ("DarkRed", "5f0000", "rgb(95, 0, 0)"),
        ("DeepPink4", "5f005f", "rgb(95, 0, 95)"),
        ("Purple4", "5f0087", "rgb(95, 0, 135)"),
        ("Purple4", "5f00af", "rgb(95, 0, 175)"),
        ("Purple3", "5f00d7", "rgb(95, 0, 215)"),
        ("BlueViolet", "5f00ff", "rgb(95, 0, 255)"),
        ("Orange4", "5f5f00", "rgb(95, 95, 0)"),
        ("Grey37", "5f5f5f", "rgb(95, 95, 95)"),
        ("MediumPurple4", "5f5f87", "rgb(95, 95, 135)"),
        ("SlateBlue3", "5f5faf", "rgb(95, 95, 175)"),
        ("SlateBlue3", "5f5fd7", "rgb(95, 95, 215)"),
        ("RoyalBlue1", "5f5fff", "rgb(95, 95, 255)"),
        ("Chartreuse4", "5f8700", "rgb(95, 135, 0)"),
        ("DarkSeaGreen4", "5f875f", "rgb(95, 135, 95)"),
        ("PaleTurquoise4", "5f8787", "rgb(95, 135, 135)"),
        ("SteelBlue", "5f87af", "rgb(95, 135, 175)"),
        ("SteelBlue3", "5f87d7", "rgb(95, 135, 215)"),
        ("CornflowerBlue", "5f87ff", "rgb(95, 135, 255)"),
        ("Chartreuse3", "5faf00", "rgb(95, 175, 0)"),
        ("DarkSeaGreen4", "5faf5f", "rgb(95, 175, 95)"),
        ("CadetBlue", "5faf87", "rgb(95, 175, 135)"),
        ("CadetBlue", "5fafaf", "rgb(95, 175, 175)"),
        ("SkyBlue3", "5fafd7", "rgb(95, 175, 215)"),
        ("SteelBlue1", "5fafff", "rgb(95, 175, 255)"),
        ("Chartreuse3", "5fd700", "rgb(95, 215, 0)"),
        ("PaleGreen3", "5fd75f", "rgb(95, 215, 95)"),
        ("SeaGreen3", "5fd787", "rgb(95, 215, 135)"),
        ("Aquamarine3", "5fd7af", "rgb(95, 215, 175)"),
        ("MediumTurquoise", "5fd7d7", "rgb(95, 215, 215)"),
        ("SteelBlue1", "5fd7ff", "rgb(95, 215, 255)"),
        ("Chartreuse2", "5fff00", "rgb(95, 255, 0)"),
        ("SeaGreen2", "5fff5f", "rgb(95, 255, 95)"),
        ("SeaGreen1", "5fff87", "rgb(95, 255, 135)"),
        ("SeaGreen1", "5fffaf", "rgb(95, 255, 175)"),
        ("Aquamarine1", "5fffd7", "rgb(95, 255, 215)"),
        ("DarkSlateGray2", "5fffff", "rgb(95, 255, 255)"),
        ("DarkRed", "870000", "rgb(135, 0, 0)"),
        ("DeepPink4", "87005f", "rgb(135, 0, 95)"),
        ("DarkMagenta", "870087", "rgb(135, 0, 135)"),
        ("DarkMagenta", "8700af", "rgb(135, 0, 175)"),
        ("DarkViolet", "8700d7", "rgb(135, 0, 215)"),
        ("Purple", "8700ff", "rgb(135, 0, 255)"),
        ("Orange4", "875f00", "rgb(135, 95, 0)"),
        ("LightPink4", "875f5f", "rgb(135, 95, 95)"),
        ("Plum4", "875f87", "rgb(135, 95, 135)"),
        ("MediumPurple3", "875faf", "rgb(135, 95, 175)"),
        ("MediumPurple3", "875fd7", "rgb(135, 95, 215)"),
        ("SlateBlue1", "875fff", "rgb(135, 95, 255)"),
        ("Yellow4", "878700", "rgb(135, 135, 0)"),
        ("Wheat4", "87875f", "rgb(135, 135, 95)"),
        ("Grey53", "878787", "rgb(135, 135, 135)"),
        ("LightSlateGrey", "8787af", "rgb(135, 135, 175)"),
        ("MediumPurple", "8787d7", "rgb(135, 135, 215)"),
        ("LightSlateBlue", "8787ff", "rgb(135, 135, 255)"),
        ("Yellow4", "87af00", "rgb(135, 175, 0)"),
        ("DarkOliveGreen3", "87af5f", "rgb(135, 175, 95)"),
        ("DarkSeaGreen", "87af87", "rgb(135, 175, 135)"),
        ("LightSkyBlue3", "87afaf", "rgb(135, 175, 175)"),
        ("LightSkyBlue3", "87afd7", "rgb(135, 175, 215)"),
        ("SkyBlue2", "87afff", "rgb(135, 175, 255)"),
        ("Chartreuse2", "87d700", "rgb(135, 215, 0)"),
        ("DarkOliveGreen3", "87d75f", "rgb(135, 215, 95)"),
        ("PaleGreen3", "87d787", "rgb(135, 215, 135)"),
        ("DarkSeaGreen3", "87d7af", "rgb(135, 215, 175)"),
        ("DarkSlateGray3", "87d7d7", "rgb(135, 215, 215)"),
        ("SkyBlue1", "87d7ff", "rgb(135, 215, 255)"),
        ("Chartreuse1", "87ff00", "rgb(135, 255, 0)"),
        ("LightGreen", "87ff5f", "rgb(135, 255, 95)"),
        ("LightGreen", "87ff87", "rgb(135, 255, 135)"),
        ("PaleGreen1", "87ffaf", "rgb(135, 255, 175)"),
        ("Aquamarine1", "87ffd7", "rgb(135, 255, 215)"),
        ("DarkSlateGray1", "87ffff", "rgb(135, 255, 255)"),
        ("Red3", "af0000", "rgb(175, 0, 0)"),
        ("DeepPink4", "af005f", "rgb(175, 0, 95)"),
        ("MediumVioletRed", "af0087", "rgb(175, 0, 135)"),
        ("Magenta3", "af00af", "rgb(175, 0, 175)"),
        ("DarkViolet", "af00d7", "rgb(175, 0, 215)"),
        ("Purple", "af00ff", "rgb(175, 0, 255)"),
        ("DarkOrange3", "af5f00", "rgb(175, 95, 0)"),
        ("IndianRed", "af5f5f", "rgb(175, 95, 95)"),
        ("HotPink3", "af5f87", "rgb(175, 95, 135)"),
        ("MediumOrchid3", "af5faf", "rgb(175, 95, 175)"),
        ("MediumOrchid", "af5fd7", "rgb(175, 95, 215)"),
        ("MediumPurple2", "af5fff", "rgb(175, 95, 255)"),
        ("DarkGoldenrod", "af8700", "rgb(175, 135, 0)"),
        ("LightSalmon3", "af875f", "rgb(175, 135, 95)"),
        ("RosyBrown", "af8787", "rgb(175, 135, 135)"),
        ("Grey63", "af87af", "rgb(175, 135, 175)"),
        ("MediumPurple2", "af87d7", "rgb(175, 135, 215)"),
        ("MediumPurple1", "af87ff", "rgb(175, 135, 255)"),
        ("Gold3", "afaf00", "rgb(175, 175, 0)"),
        ("DarkKhaki", "afaf5f", "rgb(175, 175, 95)"),
        ("NavajoWhite3", "afaf87", "rgb(175, 175, 135)"),
        ("Grey69", "afafaf", "rgb(175, 175, 175)"),
        ("LightSteelBlue3", "afafd7", "rgb(175, 175, 215)"),
        ("LightSteelBlue", "afafff", "rgb(175, 175, 255)"),
        ("Yellow3", "afd700", "rgb(175, 215, 0)"),
        ("DarkOliveGreen3", "afd75f", "rgb(175, 215, 95)"),
        ("DarkSeaGreen3", "afd787", "rgb(175, 215, 135)"),
        ("DarkSeaGreen2", "afd7af", "rgb(175, 215, 175)"),
        ("LightCyan3", "afd7d7", "rgb(175, 215, 215)"),
        ("LightSkyBlue1", "afd7ff", "rgb(175, 215, 255)"),
        ("GreenYellow", "afff00", "rgb(175, 255, 0)"),
        ("DarkOliveGreen2", "afff5f", "rgb(175, 255, 95)"),
        ("PaleGreen1", "afff87", "rgb(175, 255, 135)"),
        ("DarkSeaGreen2", "afffaf", "rgb(175, 255, 175)"),
        ("DarkSeaGreen1", "afffd7", "rgb(175, 255, 215)"),
        ("PaleTurquoise1", "afffff", "rgb(175, 255, 255)"),
        ("Red3", "d70000", "rgb(215, 0, 0)"),
        ("DeepPink3", "d7005f", "rgb(215, 0, 95)"),
        ("DeepPink3", "d70087", "rgb(215, 0, 135)"),
        ("Magenta3", "d700af", "rgb(215, 0, 175)"),
        ("Magenta3", "d700d7", "rgb(215, 0, 215)"),
        ("Magenta2", "d700ff", "rgb(215, 0, 255)"),
        ("DarkOrange3", "d75f00", "rgb(215, 95, 0)"),
        ("IndianRed", "d75f5f", "rgb(215, 95, 95)"),
        ("HotPink3", "d75f87", "rgb(215, 95, 135)"),
        ("HotPink2", "d75faf", "rgb(215, 95, 175)"),
        ("Orchid", "d75fd7", "rgb(215, 95, 215)"),
        ("MediumOrchid1", "d75fff", "rgb(215, 95, 255)"),
        ("Orange3", "d78700", "rgb(215, 135, 0)"),
        ("LightSalmon3", "d7875f", "rgb(215, 135, 95)"),
        ("LightPink3", "d78787", "rgb(215, 135, 135)"),
        ("Pink3", "d787af", "rgb(215, 135, 175)"),
        ("Plum3", "d787d7", "rgb(215, 135, 215)"),
        ("Violet", "d787ff", "rgb(215, 135, 255)"),
        ("Gold3", "d7af00", "rgb(215, 175, 0)"),
        ("LightGoldenrod3", "d7af5f", "rgb(215, 175, 95)"),
        ("Tan", "d7af87", "rgb(215, 175, 135)"),
        ("MistyRose3", "d7afaf", "rgb(215, 175, 175)"),
        ("Thistle3", "d7afd7", "rgb(215, 175, 215)"),
        ("Plum2", "d7afff", "rgb(215, 175, 255)"),
        ("Yellow3", "d7d700", "rgb(215, 215, 0)"),
        ("Khaki3", "d7d75f", "rgb(215, 215, 95)"),
        ("LightGoldenrod2", "d7d787", "rgb(215, 215, 135)"),
        ("LightYellow3", "d7d7af", "rgb(215, 215, 175)"),
        ("Grey84", "d7d7d7", "rgb(215, 215, 215)"),
        ("LightSteelBlue1", "d7d7ff", "rgb(215, 215, 255)"),
        ("Yellow2", "d7ff00", "rgb(215, 255, 0)"),
        ("DarkOliveGreen1", "d7ff5f", "rgb(215, 255, 95)"),
        ("DarkOliveGreen1", "d7ff87", "rgb(215, 255, 135)"),
        ("DarkSeaGreen1", "d7ffaf", "rgb(215, 255, 175)"),
        ("Honeydew2", "d7ffd7", "rgb(215, 255, 215)"),
        ("LightCyan1", "d7ffff", "rgb(215, 255, 255)"),
        ("Red1", "ff0000", "rgb(255, 0, 0)"),
        ("DeepPink2", "ff005f", "rgb(255, 0, 95)"),
        ("DeepPink1", "ff0087", "rgb(255, 0, 135)"),
        ("DeepPink1", "ff00af", "rgb(255, 0, 175)"),
        ("Magenta2", "ff00d7", "rgb(255, 0, 215)"),
        ("Magenta1", "ff00ff", "rgb(255, 0, 255)"),
        ("OrangeRed1", "ff5f00", "rgb(255, 95, 0)"),
        ("IndianRed1", "ff5f5f", "rgb(255, 95, 95)"),
        ("IndianRed1", "ff5f87", "rgb(255, 95, 135)"),
        ("HotPink", "ff5faf", "rgb(255, 95, 175)"),
        ("HotPink", "ff5fd7", "rgb(255, 95, 215)"),
        ("MediumOrchid1", "ff5fff", "rgb(255, 95, 255)"),
        ("DarkOrange", "ff8700", "rgb(255, 135, 0)"),
        ("Salmon1", "ff875f", "rgb(255, 135, 95)"),
        ("LightCoral", "ff8787", "rgb(255, 135, 135)"),
        ("PaleVioletRed1", "ff87af", "rgb(255, 135, 175)"),
        ("Orchid2", "ff87d7", "rgb(255, 135, 215)"),
        ("Orchid1", "ff87ff", "rgb(255, 135, 255)"),
        ("Orange1", "ffaf00", "rgb(255, 175, 0)"),
        ("SandyBrown", "ffaf5f", "rgb(255, 175, 95)"),
        ("LightSalmon1", "ffaf87", "rgb(255, 175, 135)"),
        ("LightPink1", "ffafaf", "rgb(255, 175, 175)"),
        ("Pink1", "ffafd7", "rgb(255, 175, 215)"),
        ("Plum1", "ffafff", "rgb(255, 175, 255)"),
        ("Gold1", "ffd700", "rgb(255, 215, 0)"),
        ("LightGoldenrod2", "ffd75f", "rgb(255, 215, 95)"),
        ("LightGoldenrod2", "ffd787", "rgb(255, 215, 135)"),
        ("NavajoWhite1", "ffd7af", "rgb(255, 215, 175)"),
        ("MistyRose1", "ffd7d7", "rgb(255, 215, 215)"),
        ("Thistle1", "ffd7ff", "rgb(255, 215, 255)"),
        ("Yellow1", "ffff00", "rgb(255, 255, 0)"),
        ("LightGoldenrod1", "ffff5f", "rgb(255, 255, 95)"),
        ("Khaki1", "ffff87", "rgb(255, 255, 135)"),
        ("Wheat1", "ffffaf", "rgb(255, 255, 175)"),
        ("Cornsilk1", "ffffd7", "rgb(255, 255, 215)"),
        ("Grey100", "ffffff", "rgb(255, 255, 255)"),
        ("Grey3", "080808", "rgb(8, 8, 8)"),
        ("Grey7", "121212", "rgb(18, 18, 18)"),
        ("Grey11", "1c1c1c", "rgb(28, 28, 28)"),
        ("Grey15", "262626", "rgb(38, 38, 38)"),
        ("Grey19", "303030", "rgb(48, 48, 48)"),
        ("Grey23", "3a3a3a", "rgb(58, 58, 58)"),
        ("Grey27", "444444", "rgb(68, 68, 68)"),
        ("Grey30", "4e4e4e", "rgb(78, 78, 78)"),
        ("Grey35", "585858", "rgb(88, 88, 88)"),
        ("Grey39", "626262", "rgb(98, 98, 98)"),
        ("Grey42", "6c6c6c", "rgb(108, 108, 108)"),
        ("Grey46", "767676", "rgb(118, 118, 118)"),
        ("Grey50", "808080", "rgb(128, 128, 128)"),
        ("Grey54", "8a8a8a", "rgb(138, 138, 138)"),
        ("Grey58", "949494", "rgb(148, 148, 148)"),
        ("Grey62", "9e9e9e", "rgb(158, 158, 158)"),
        ("Grey66", "a8a8a8", "rgb(168, 168, 168)"),
        ("Grey70", "b2b2b2", "rgb(178, 178, 178)"),
        ("Grey74", "bcbcbc", "rgb(188, 188, 188)"),
        ("Grey78", "c6c6c6", "rgb(198, 198, 198)"),
        ("Grey82", "d0d0d0", "rgb(208, 208, 208)"),
        ("Grey85", "dadada", "rgb(218, 218, 218)"),
        ("Grey89", "e4e4e4", "rgb(228, 228, 228)"),
        ("Grey93", "eeeeee", "rgb(238, 238, 238)"),
    )

    @staticmethod
    def get_color_name(color: int, colorful: bool = False):
        if 0 < color < 8:
            return ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"][color]
        elif color & 0xFF == 0x28:
            if 0 < (color >> 8) < 256:
                if colorful:
                    return f"256 color of index {colortty(" ".join(("".join(("'", _Color.Color256Index[color >> 8][0], ",")), "".join(("#", _Color.Color256Index[color >> 8][1]))))).set(_Color().color_256(color >> 8)).make()}"
                else:
                    return f"256 color of index {" ".join(("".join(("'", _Color.Color256Index[color >> 8][0], "'")), "".join(("#", _Color.Color256Index[color >> 8][1]))))}"
            else:
                raise ValueError(f"Not a valid 256 color index: {color >> 8} (hex=0x{color >> 8:02x})")
        elif color & 0xFF == 0x18:
            if colorful:
                return f"RGB color of {colortty("".join(("#", f"{(color >> 24) & 0xFF:02x}{(color >> 16) & 0xFF:02x}{(color >> 8) & 0xFF:02x}"))).set(_Color().color(color >> 24, color >> 16, color >> 8)).make()}"
            else:
                return f"RGB color of {"".join(("#", f"{(color >> 24) & 0xFF:02x}{(color >> 16) & 0xFF:02x}{(color >> 8) & 0xFF:02x}"))}"
        else:
            raise ValueError(f"Not a valid color type: {color} (hex=0x{color:02x})")

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
        print()
    print()
