import ctypes
from ctypes import wintypes

# 加载GDI库
gdi32 = ctypes.WinDLL("gdi32")
FR_PRIVATE = ctypes.c_int(1)


def add_font(font_path: str) -> None:
    gdi32.AddFontResourceExW(font_path, FR_PRIVATE, None)
