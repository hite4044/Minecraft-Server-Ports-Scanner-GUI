# -*- coding: UTF-8 -*-
class Color:
    def __init__(self, *rgb):
        if len(rgb) == 1:
            rgb = rgb[0]

        if isinstance(rgb, str):
            rgb = rgb.replace("#", "")
            self.red = int(rgb[:2], 16) / 255
            self.green = int(rgb[2:4], 16) / 255
            self.blue = int(rgb[4:], 16) / 255
        elif isinstance(rgb, (tuple, list)):
            if isinstance(rgb[0], float):
                self.red = rgb[0]
                self.green = rgb[1]
                self.blue = rgb[2]
            elif isinstance(rgb[0], int):
                self.red = rgb[0] / 255
                self.green = rgb[1] / 255
                self.blue = rgb[2] / 255

    def set_brightness(self, brightness: float):
        self.red = min(max(self.red * brightness, 0), 1)
        self.green = min(max(self.green * brightness, 0), 1)
        self.blue = min(max(self.blue * brightness, 0), 1)
        return self

    def reverse(self):
        self.red = 1 - self.red
        self.green = 1 - self.green
        self.blue = 1 - self.blue
        return self

    @property
    def hex(self) -> str:
        red = hex(int(self.red * 255))[2:].zfill(2)
        green = hex(int(self.green * 255))[2:].zfill(2)
        blue = hex(int(self.blue * 255))[2:].zfill(2)
        return "#" + red + green + blue

    @property
    def sum(self) -> float:
        return self.red + self.green + self.blue

    @property
    def sum_avg(self) -> float:
        return (self.red + self.green + self.blue) / 3

    @property
    def fsum(self) -> int:
        return int(self.sum * 255)

    @property
    def fred(self) -> int:
        return int(self.red * 255)

    @property
    def fgreen(self) -> int:
        return int(self.green * 255)

    @property
    def fblue(self) -> int:
        return int(self.blue * 255)
