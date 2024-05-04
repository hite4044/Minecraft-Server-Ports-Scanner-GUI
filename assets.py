# -*- coding: UTF-8 -*-
from PIL import Image
from PIL.ImageTk import PhotoImage

BG_COUNT = 20


class Assets:
    @property
    def default_favicon(self) -> PhotoImage:
        return PhotoImage(Image.open(r"assets/server_icon.png"))

    @property
    def background(self) -> PhotoImage:
        image = Image.open(r"assets/light_dirt_background.png")  # 打开图像文件
        width, height = image.size
        image = image.resize((width * 4, height * 4))
        width, height = image.size
        bg: Image.Image = Image.new("RGB", (width * BG_COUNT, height * BG_COUNT))
        for y in range(BG_COUNT):
            for x in range(BG_COUNT):
                bg.paste(image, (x * width, y * height))
        return PhotoImage(bg)
