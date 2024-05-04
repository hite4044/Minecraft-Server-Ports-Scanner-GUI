# -*- coding: UTF-8 -*-
from ttkbootstrap.constants import *
from tkinter.font import Font
from ttkbootstrap import Style
from scanner import ServerInfo
from typing import Any, List
from random import randint
import ttkbootstrap as ttk
from colorlib import Color
from tkinter import Misc
from copy import copy
import tkinter as tk
import vars

ERROR = "error"


class MOTD(ttk.Text):
    def __init__(self, master: tk.Misc):
        super(MOTD, self).__init__(master, state=DISABLED, height=1, width=70, relief=FLAT)

    def load_motd(self, data: ServerInfo):
        self.configure(state=NORMAL)
        try:
            self.delete("1.0", END)
        except IndexError:
            pass
        for extra in data.description_json:
            try:
                tag = hex(randint(0, 114514))
                tag_font = Font(family="Unifont", size=12)
                if extra.get("color"):
                    if "#" not in extra["color"]:
                        color = vars.color_map_hex[extra["color"]]
                    else:
                        color = extra["color"]
                    self.tag_configure(tag, foreground=color)

                if extra.get("underline") or extra.get("underlined"):
                    self.tag_configure(tag, underline=True)
                if extra.get("bold"):
                    tag_font.config(family="宋体", weight="bold")
                elif extra.get("italic"):
                    tag_font.config(slant="italic")
                elif extra.get("strikethrough"):
                    tag_font.config(overstrike=True)

                self.tag_configure(tag, font=tag_font, justify=LEFT)
                self.insert(END, extra["text"], tag)
            except TimeoutError as e:
                print("MOTD Data Extra Error:", extra, e)
        self.configure(state=DISABLED)


class EntryScale(ttk.Frame):
    def __init__(self, master: Misc, _min: Any, _max: Any, value: Any, text: str, fmt: Any):
        super(EntryScale, self).__init__(master)
        self.min = _min
        self.max = _max
        self.fmt = fmt
        self.text = ttk.Label(self, text=text)
        self.entry = ttk.Entry(self, width=8)
        self.scale = ttk.Scale(self, from_=_min, to=_max, command=self.scale_set_value)

        self.entry.bind("<KeyRelease>", self.entry_set_value)
        self.entry.insert(END, str(value))
        self.entry_set_value()

        self.text.pack(side=LEFT)
        self.scale.pack(side=LEFT, fill=X, expand=True)
        self.entry.pack(side=LEFT)

    def scale_set_value(self, _=None):
        value = self.fmt(self.scale.cget("value"))
        if isinstance(value, float):
            value = round(value, 2)
        self.scale.configure(value=value)
        self.entry.delete(0, END)
        self.entry.insert(0, str(value))

    def entry_set_value(self, _=None):
        value = self.entry.get()
        try:
            value = self.fmt(value)
            if value <= self.max:
                if value >= self.min:
                    self.scale.configure(value=value)
                else:
                    self.entry.delete(0, END)
                    self.entry.insert(0, str(self.min))
                    self.entry_set_value()
            else:
                self.entry.delete(0, END)
                self.entry.insert(0, str(self.max))
                self.entry_set_value()
        except ValueError:
            pass

    def get_value(self):
        return self.fmt(self.scale.cget("value"))

    def set_value(self, value):
        self.scale.configure(value=value)
        self.entry.delete(0, END)
        self.entry.insert(0, str(value))


class EntryScaleInt(EntryScale):
    def __init__(self, master: Misc, _min: int, _max: int, value: int, text: str):
        super(EntryScaleInt, self).__init__(master, _min, _max, value, text, int)


class EntryScaleFloat(EntryScale):
    def __init__(self, master: Misc, _min: float, _max: float, value: float, text: str):
        super(EntryScaleFloat, self).__init__(master, _min, _max, value, text, float)


class TextEntry(ttk.Frame):
    def __init__(self, master: Misc, tip: str, value: str = ""):
        super(TextEntry, self).__init__(master)

        self.text = ttk.Label(self, text=tip)
        self.entry = ttk.Entry(self)

        self.entry.insert(0, value)

        self.text.pack(side=LEFT)
        self.entry.pack(side=LEFT, fill=X, expand=True)

    def get(self):
        return self.entry.get()

    def delete(self, first, last) -> None:
        self.entry.delete(first, last)

    def set(self, text: str):
        self.entry.delete(0, END)
        self.entry.insert(0, text)


class TextCombobox(ttk.Frame):
    def __init__(self, master: Misc, tip: str, value: List[str] = None):
        super(TextCombobox, self).__init__(master)

        self.text = ttk.Label(self, text=tip)
        self.combobox = ttk.Combobox(self, values=value)

        if len(value) > 0:
            self.combobox.current(0)

        self.text.pack(side=LEFT)
        self.combobox.pack(side=LEFT, fill=X, expand=True)

    def get(self) -> str:
        return self.combobox.get()

    def set(self, text: str):
        self.combobox.delete(0, END)
        self.combobox.insert(0, text)


class Tabs(ttk.Notebook):
    pass


class RangeScale(ttk.Canvas):
    def __init__(self, master: Misc):
        """
        范围选择条
        使用set设置范围, 使用value获取当前值
        绑定<<RangeChanged>>事件侦测范围变化
        """
        super(RangeScale, self).__init__(master, height=15)
        self.bind("<Button-1>", self.mouse_down)
        self.bind("<ButtonRelease-1>", self.mouse_up)
        self.bind("<Configure>", self.redraw)
        self.bind("<Motion>", self.mouse_move)
        self.bind("<Leave>", self.mouse_move)
        self.bind("<<ThemeChanged>>", self.color_change)

        self.min_percentage: float = 0.25
        self.max_percentage: float = 0.75

        self.scale_bar = None
        self.range_bar = None
        self.min_handle = None
        self.max_handle = None

        self.min_highlight = False  # min滑块是否高亮
        self.max_highlight = False  # max滑块是否高亮

        self.bind_min_handle = False  # 鼠标是否绑定min滑块
        self.bind_max_handle = False  # 鼠标是否绑定max滑块

        self.bar_color = Style().colors.light  # 拖动范围条的颜色
        self.range_color = Color(Style().colors.light).set_brightness(1.5).hex  # 范围条的颜色
        self.min_handle_base_color = Style().colors.primary  # 小值滑块基础颜色
        self.max_handle_base_color = Color(Style().colors.primary).reverse().hex  # 大值滑块基础颜色
        self.min_handle_color = copy(self.min_handle_base_color)  # 小值滑块颜色
        self.max_handle_color = copy(self.max_handle_base_color)  # 大值滑块颜色

        self.color_change()

    def set(self, _min: float, _max: float):
        self.min_percentage = _min
        self.max_percentage = _max
        self.redraw()

    def color_change(self, *_):
        colors = Style().colors
        self.min_handle_base_color = colors.primary
        self.max_handle_base_color = Color(colors.primary).reverse().hex
        if Color(colors.bg).sum / 3 > 0.6:
            self.bar_color = colors.light
            self.range_color = Color(self.bar_color).set_brightness(1 / 1.5).hex
        else:
            self.bar_color = Color(colors.selectbg).set_brightness(0.8).hex
            self.range_color = Color(self.bar_color).set_brightness(1.5).hex

        self.update_color()
        self.redraw()

    def redraw(self, *_):
        self.delete(ALL)
        self.scale_bar = self.create_rectangle(1, 4, self.winfo_width(), 10, fill=self.bar_color, width=0)
        self.range_bar = self.create_rectangle(self.min_offset, 4, self.max_offset, 10,
                                               fill=self.range_color, width=0)

        self.redraw_min_handle()
        self.redraw_max_handle()

    def redraw_min_handle(self):
        self.min_handle = self.create_text(7 + self.min_offset, 5,
                                           text="●", font=("微软雅黑", 23),
                                           fill=self.min_handle_color)

    def redraw_max_handle(self):
        self.max_handle = self.create_text(7 + self.max_offset, 5,
                                           text="●", font=("微软雅黑", 23),
                                           fill=self.max_handle_color)

    def mouse_move(self, event: tk.Event):
        min_box = (self.min_offset, 0, self.min_offset + 15, 15)
        value = min_box[0] < event.x < min_box[2] and min_box[1] < event.y < min_box[3]
        if value != self.min_highlight:
            self.min_highlight = value
            self.update_color()

        max_box = (self.max_offset, 0, self.max_offset + 15, 15)
        value = max_box[0] < event.x < max_box[2] and max_box[1] < event.y < max_box[3]
        if value != self.max_highlight:
            self.max_highlight = value
            self.update_color()

        if self.bind_min_handle:  # min滑块移动逻辑
            self.min_percentage = (event.x - 7.5) / (self.winfo_width() - 15)
            if self.min_percentage < 0:
                self.min_percentage = 0
            if self.min_percentage > self.max_percentage:
                self.max_percentage = self.min_percentage
                if self.max_percentage > 1:
                    self.max_percentage = self.min_percentage = 1
            self.event_generate("<<RangeChanged>>")
            self.redraw()
        elif self.bind_max_handle:  # max滑块移动逻辑
            self.max_percentage = (event.x - 7.5) / (self.winfo_width() - 15)
            if self.max_percentage > 1:
                self.max_percentage = 1
            if self.max_percentage < self.min_percentage:
                self.min_percentage = self.max_percentage
                if self.min_percentage < 0:
                    self.min_percentage = self.max_percentage = 0
            self.event_generate("<<RangeChanged>>")
            self.redraw()

    def update_color(self):
        if self.min_highlight:
            self.min_handle_color = Color(self.min_handle_base_color).set_brightness(1.1).hex
            self.redraw_min_handle()
        else:
            self.min_handle_color = copy(self.min_handle_base_color)
            self.redraw_min_handle()

        if self.max_highlight:
            self.max_handle_color = Color(self.max_handle_base_color).set_brightness(1.1).hex
            self.redraw_max_handle()
        else:
            self.max_handle_color = copy(self.max_handle_base_color)
            self.redraw_max_handle()

    def mouse_down(self, *_):
        if self.max_highlight:
            self.bind_max_handle = True
            return
        if self.min_highlight:
            self.bind_min_handle = True

    def mouse_up(self, *_):
        if self.bind_min_handle:
            self.bind_min_handle = False
            return
        elif self.bind_max_handle:
            self.bind_max_handle = False

    @property
    def value(self) -> (float, float):
        return self.min_percentage, self.max_percentage

    @property
    def min_offset(self) -> float:
        return (self.winfo_width() - 15) * self.min_percentage

    @property
    def max_offset(self) -> float:
        return (self.winfo_width() - 15) * self.max_percentage


class TipEntry(ttk.Entry):
    def __init__(self, master: Misc, tip: str = "在此输入内容"):
        super(TipEntry, self).__init__(master)
        self.on_tip = False
        self.tip = tip

        self.bind("<FocusIn>", self.on_focus_get)
        self.bind("<FocusOut>", self.on_focus_out)

    def on_focus_get(self, *_):
        if self.on_tip:
            self.delete(0, END)
            self.on_tip = False

    def on_focus_out(self, *_):
        if not self.get():
            self.insert(0, self.tip)
            self.on_tip = True

    def set_tip(self, tip: str):
        self.tip = tip
