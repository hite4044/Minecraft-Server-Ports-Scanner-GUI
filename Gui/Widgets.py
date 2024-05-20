# -*- coding: UTF-8 -*-
from math import ceil
from queue import Queue
from random import randint
from ttkbootstrap import *
from typing import Any, List
from tkinter.font import Font
from tkinter import Misc, Event
from threading import Lock, Thread
from ttkbootstrap.constants import *
from pyperclip import copy as copy_clipboard
from time import strftime, localtime, time, sleep
from copy import copy

from Libs.Vars import scale_rater, color_map_hex
from Network.Scanner import ServerInfo
from Libs.ColorLib import Color

ERROR = "error"
DEBUG = "debug"
scanbar: Any = None


def get_now_time() -> str:
    return strftime("%Y-%m-%d_%H-%M-%S", localtime())


class MOTD(Text):
    def __init__(self, master: Misc):
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
                        color = color_map_hex[extra["color"]]
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


class EntryScale(Frame):
    def __init__(self, master: Misc, _min: Any, _max: Any, value: Any, text: str, fmt: Any):
        super(EntryScale, self).__init__(master)
        self.min = _min
        self.max = _max
        self.fmt = fmt
        self.text = Label(self, text=text)
        self.entry = Entry(self, width=8)
        self.scale = Scale(self, from_=_min, to=_max, command=self.scale_set_value)

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


class TextEntry(Frame):
    def __init__(self, master: Misc, tip: str, value: str = ""):
        super(TextEntry, self).__init__(master)

        self.text = Label(self, text=tip)
        self.entry = Entry(self)

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


class TextCombobox(Frame):
    def __init__(self, master: Misc, tip: str, value: List[str] = None):
        super(TextCombobox, self).__init__(master)

        self.text = Label(self, text=tip)
        self.combobox = Combobox(self, values=value, cursor="xterm")

        if len(value) > 0:
            self.combobox.current(0)

        self.text.pack(side=LEFT)
        self.combobox.pack(side=LEFT, fill=X, expand=True)

    def get(self) -> str:
        return self.combobox.get()

    def set(self, text: str):
        self.combobox.delete(0, END)
        self.combobox.insert(0, text)


class Tabs(Notebook):
    pass


class RangeScale(Canvas):
    def __init__(self, master: Misc):
        """
        范围选择条
        使用set设置范围, 使用value获取当前值
        绑定<<RangeChanged>>事件侦测范围变化
        """
        super(RangeScale, self).__init__(master, height=int(scale_rater() * 15))
        self.bind("<Button-1>", self.mouse_down)
        self.bind("<ButtonRelease-1>", self.mouse_up)
        self.bind("<Configure>", self.redraw)
        self.bind("<Motion>", self.mouse_move)
        self.bind("<Leave>", self.mouse_move)
        self.bind("<<ThemeChanged>>", self.color_change)

        self.min_percentage: float = 0.25
        self.max_percentage: float = 0.75

        self.image = None
        self.image_tk = None

        self.bar_width = ceil(5 * scale_rater())

        self.min_highlight = False  # min滑块是否高亮
        self.max_highlight = False  # max滑块是否高亮

        self.bind_min_handle = False  # 鼠标是否绑定min滑块
        self.bind_max_handle = False  # 鼠标是否绑定max滑块

        self.bar_color = Style().colors.light  # 拖动范围条的颜色
        self.range_color = Color(Style().colors.light).set_brightness(1.5).hex  # 范围条的颜色
        self.min_handle_base_color = Style().colors.primary  # 小值滑块基础颜色
        self.max_handle_base_color = Color(Style().colors.primary).reverse().hex  # 大值滑块基础颜色
        self.min_handle_color = self.min_handle_base_color[:]  # 小值滑块颜色
        self.max_handle_color = self.max_handle_base_color[:]  # 大值滑块颜色

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
        height = self.winfo_height()
        width = self.winfo_width()

        source = Image.new("RGBA", (self.winfo_width(), height), Style().colors.bg)
        source2 = Image.new("RGBA", (self.winfo_width() * 10, height * 10), "#FFFF0000")

        draw = ImageDraw.Draw(source)
        draw2 = ImageDraw.Draw(source2)
        draw.line((0, height // 2, self.winfo_width(), height // 2),
                  fill=self.bar_color,
                  width=self.bar_width)  # 绘制范围基条
        draw.line((int(self.min_offset), height // 2, int(self.max_offset), height // 2),
                  fill=self.range_color,
                  width=self.bar_width)  # 绘制范围条
        draw2.ellipse((int(self.min_offset) * 10, 0, (int(self.min_offset) + height) * 10, height * 10),
                      fill=self.min_handle_color,
                      width=0)  # 绘制小端滑块
        draw2.ellipse((int(self.max_offset) * 10, 0, (int(self.max_offset) + height) * 10, height * 10),
                      fill=self.max_handle_color,
                      width=0)  # 绘制大端滑块

        source2 = source2.resize((width, height))
        source3 = Image.alpha_composite(source, source2)
        self.image = ImageTk.PhotoImage(source3)
        self.delete(ALL)
        self.create_image(0, 0, anchor=NW, image=self.image)

    def mouse_move(self, event: Event):
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
        else:
            self.min_handle_color = copy(self.min_handle_base_color)

        if self.max_highlight:
            self.max_handle_color = Color(self.max_handle_base_color).set_brightness(1.1).hex
        else:
            self.max_handle_color = copy(self.max_handle_base_color)
        self.redraw()

    def mouse_down(self, *_):
        if self.max_highlight:
            self.bind_max_handle = True
            return
        if self.min_highlight:
            self.bind_min_handle = True

    def mouse_up(self, *_):
        if self.bind_min_handle:
            self.bind_min_handle = False
        elif self.bind_max_handle:
            self.bind_max_handle = False

    @property
    def value(self) -> (float, float):
        return self.min_percentage, self.max_percentage

    @property
    def min_offset(self) -> float:
        return (self.winfo_width() - self.winfo_height()) * self.min_percentage

    @property
    def max_offset(self) -> float:
        return (self.winfo_width() - self.winfo_height()) * self.max_percentage


class TipEntry(Entry):
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


class ProgressBar(Canvas):
    def __init__(self, master: Misc, text: str = "0%"):
        super(ProgressBar, self).__init__(master, height=26)
        self.color = Style().colors
        self.bind("<Configure>", self.redraw)
        self.bind("<<ThemeChanged>>", self.change_color)
        self.percentage = 0
        self.text = text
        self.redraw_lock = Lock()
        self.now_elements = []
        self.last_elements = []

        self.text_id = 0
        self.redraw()

    def change_color(self, *_):
        self.color = Style().colors
        self.redraw()

    def redraw(self, *_):
        with self.redraw_lock:
            self.now_elements.clear()
            width = self.winfo_width()
            bar_x = int((width - 4) * self.percentage)
            if bar_x == 1:
                self.now_elements.append(self.create_line(1, 1, 1, 26, fill=self.color.success))
            elif bar_x > 1:
                self.now_elements.append(self.create_rectangle(1, 1, bar_x, 26 - 2, fill=self.color.success,
                                                               outline=self.color.success))

            self.now_elements.append(self.create_rectangle(0, 0, width - 1, 26 - 1, outline=self.color.border))
            self.text_id = self.create_text(width // 2, 13, text=self.text, fill=self.color.fg)
            self.now_elements.append(self.text_id)

            if self.last_elements:
                self.delete(*self.last_elements)
            self.last_elements = self.now_elements.copy()

    def set_percentage(self, percentage: float, text: str = None):
        self.percentage = percentage
        self.text = text if text is not None else self.text
        self.redraw()


class InfoProgressBar(Frame):
    def __init__(self, master: Misc, interval: float, text: str):
        super().__init__(master)
        self.value = 0
        self.last_value = 0
        self.last_update = time()
        self.speed_avg = []
        self.max_ = 0
        self.interval = interval

        self.text = Label(self, text=text)
        self.progress = ProgressBar(self)
        self.progress_text = Label(self, text="0 ports/s")
        self.text.pack(side=LEFT)
        self.progress.pack(side=LEFT, fill=X, expand=True)
        self.progress_text.pack(side=LEFT)

    def reset(self, _max: int):
        self.value = 0
        self.last_value = 0
        self.last_update = time()
        self.speed_avg.clear()
        self.max_ = _max
        self.progress_text.configure(text="0 ports/s")
        self.progress.set_percentage(0, "0%")

    def update_progress_text(self, speed: float):
        self.progress_text.configure(text=f"{speed:.2f} ports/s")

    def update_progress(self, value: float):
        if time() - self.last_update > self.interval:
            self.update_now(value)

    def update_now(self, value: float):
        speed_avg_len = len(self.speed_avg)
        if speed_avg_len > 50:
            self.speed_avg.pop(0)
            return
        elif speed_avg_len == 0:
            self.speed_avg.append(0)
            return

        percentage = value / self.max_
        self.progress.set_percentage(percentage, f"{round(percentage * 100, 2)}%")
        self.update_progress_text(sum(self.speed_avg) / speed_avg_len)

        if (time() - self.last_update) == 0:
            return

        self.speed_avg.append((value - self.last_value) / (time() - self.last_update))
        self.last_value = value
        self.last_update = time()


class PauseButton(Button):
    def __init__(self, master: Misc, start_cb: Any, pause_cb: Any, state: str = NORMAL):
        super(PauseButton, self).__init__(master, text="暂停", state=state)
        self.startCB = start_cb
        self.pauseCB = pause_cb
        self.in_pause = False
        self.configure(command=self.click)

    def click(self):
        if self.in_pause:
            self.in_pause = False
            self.startCB()
            self.configure(text="暂停")
        else:
            self.in_pause = True
            self.pauseCB()
            self.configure(text="继续")


class ThemesSelector(Frame):
    def __init__(self, master: Misc):
        super(ThemesSelector, self).__init__(master)
        self.select_text = Label(self, text="选择主题:")
        self.theme_selector = Combobox(self, values=Style().theme_names(), state=READONLY)
        self.theme_selector.set(Style().theme_use())
        self.theme_selector.bind("<<ComboboxSelected>>", self.on_theme_selected)
        self.select_text.pack(side=LEFT, padx=5, pady=5)
        self.theme_selector.pack(side=LEFT, padx=5, pady=5)

    def on_theme_selected(self, _):
        Style().theme_use(self.theme_selector.get())


class RangeSelector(Frame):
    def __init__(self, master: Misc, text: str = "范围选择:", start: int = 0, stop: int = 100):
        super(RangeSelector, self).__init__(master)
        self.start = min(start, stop)
        self.stop = max(start, stop)
        self.start_per = self.start / (self.start + self.stop)
        self.stop_per = self.stop / (self.start + self.stop)

        self.range_text = Label(self, text=text)
        self.range_selector = RangeScale(self)
        self.min_entry = Entry(self, width=8)
        self.max_entry = Entry(self, width=8)

        self.range_selector.set(0, 1)
        self.range_selector.bind("<<RangeChanged>>", self.range_changed)
        self.min_entry.bind("<Key>", lambda _: self.after(50, self.min_entry_changed))
        self.max_entry.bind("<Key>", lambda _: self.after(50, self.max_entry_changed))
        self.min_entry.bind("<FocusOut>", self.min_entry_focus_out)
        self.max_entry.bind("<FocusOut>", self.max_entry_focus_out)

        self.range_text.pack(side=LEFT)
        self.min_entry.pack(side=LEFT)
        self.range_selector.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.max_entry.pack(side=LEFT)

        self.range_changed()

    def set(self, _min: int, _max: int):
        self.range_selector.set(self.get_per(_min),
                                self.get_per(_max))
        self.min_entry.delete(0, END)
        self.min_entry.insert(0, str(_min))
        self.max_entry.delete(0, END)
        self.max_entry.insert(0, str(_max))

    def range_changed(self, *_):
        _min, _max = self.range_selector.value
        self.min_entry.delete(0, END)
        self.min_entry.insert(0, str(self.start_port))
        self.max_entry.delete(0, END)
        self.max_entry.insert(0, str(self.stop_port))

    def min_entry_changed(self, *_):
        value = self.min_entry.get()
        try:
            value = int(value)
            _min = self.get_per(value)
            _max = self.range_selector.value[1]
            if _min < 0 or _min > 1 or _min > _max:
                return
            _min = _min if _min > 0 else 0
            _max = _max if _max < 1 else 1
            self.range_selector.set(_min, _max)
        except ValueError:
            pass

    def max_entry_changed(self, *_):
        value = self.max_entry.get()
        try:
            value = int(value)
            _min = self.range_selector.value[0]
            _max = self.get_per(value)
            if _min < 0 or _min > 1 or _max < _min:
                return
            _min = _min if _min > 0 else 0
            _max = _max if _max < 1 else 1
            self.range_selector.set(_min, _max)
        except ValueError:
            pass

    def min_entry_focus_out(self, *_):
        value = self.min_entry.get()
        try:
            value = int(value)
            if value < self.start:
                value = self.start
            if value > self.stop:
                value = self.stop
            _min = self.get_per(value)
            _max = self.range_selector.value[1]
            _min, _max = min(_min, _max), max(_min, _max)
            _min = _min if _min > 0 else 0
            _max = _max if _max < 1 else 1
            self.range_selector.set(_min, _max)
            self.range_changed()
        except ValueError:
            self.min_entry.delete(0, END)
            self.min_entry.insert(0, str(self.start_port))

    def max_entry_focus_out(self, *_):
        value = self.max_entry.get()
        try:
            value = int(value)
            if value < self.start:
                value = self.start
            if value > self.stop:
                value = self.stop
            _min = self.range_selector.value[0]
            _max = self.get_per(value)
            _min, _max = min(_min, _max), max(_min, _max)
            _min = _min if _min > 0 else 0
            _max = _max if _max < 1 else 1
            self.range_selector.set(_min, _max)
            self.range_changed()

        except ValueError:
            self.max_entry.delete(0, END)
            self.max_entry.insert(0, str(self.stop_port))

    def get(self) -> (int, int):
        return self.start_port, self.stop_port

    def get_per(self, value) -> float:
        return (value - self.start) / (self.stop - self.start)

    @property
    def start_port(self) -> int:
        _min, _ = self.range_selector.value
        return int(self.start + (self.stop - self.start) * _min)

    @property
    def stop_port(self) -> int:
        _, _max = self.range_selector.value
        return int(self.start + (self.stop - self.start) * _max)


class Logger(Frame):
    def __init__(self, master: Misc):
        super(Logger, self).__init__(master)

        self.logs = []
        self.levels = {"调试": DEBUG, "信息": INFO, "警告": WARNING, "错误": ERROR}
        self.levels_res = {v: k for k, v in self.levels.items()}
        self.log_list = list(self.levels.values())
        self.log_count = 0
        self.now_level = INFO
        self.log_lock = Lock()
        self.log_queue = Queue()

        # 信息条
        self.info_bar = Frame(self)
        self.info_bar.pack(fill=X)

        # 日志等级选择框
        self.select_frame = Frame(self.info_bar)
        self.select_text = Label(self.select_frame, text="日志等级:")
        self.select_combobox = Combobox(self.select_frame, values=list(self.levels.keys()), state=READONLY)
        self.select_combobox.set("信息")
        self.select_combobox.bind("<<ComboboxSelected>>", self.on_level_change)
        self.select_text.pack(side=LEFT, padx=5)
        self.select_combobox.pack(side=LEFT, padx=5)
        self.select_frame.pack(side=LEFT, padx=5, pady=5)

        # 日志数量显示
        self.log_count_label = Label(self.info_bar, text="日志数量: 0")
        self.log_count_label.pack(side=RIGHT, padx=5, pady=5)

        # 日志显示列表
        self.list_box_bar = Scrollbar(self)
        self.list_box_bar.pack(side=RIGHT, fill=Y)
        self.list_box = Treeview(self, columns=["0", "1", "2"], show=HEADINGS, yscrollcommand=self.list_box_bar.set)
        self.list_box_bar.configure(command=self.list_box.yview)
        self.list_box.column("0", width=80, anchor=CENTER)
        self.list_box.column("1", width=21, anchor=CENTER)
        self.list_box.column("2", width=440)
        self.list_box.heading("0", text="时间")
        self.list_box.heading("1", text="等级")
        self.list_box.heading("2", text="日志", anchor=W)
        self.list_box.configure(selectmode=BROWSE)
        self.list_box.bind("<Button-3>", self.on_menu)
        self.list_box.pack(fill=BOTH, expand=True)
        def o():
            for i in range(2000):
                self.log(INFO, "日志系统已启动")
                sleep(0.1)
        Thread(target=o, daemon=True).start()

    def set_log_count(self):
        self.log_count_label.configure(text=f"日志数量: {self.log_count}")

    def log(self, level: str, *values: object, sep: str = " "):
        try:
            self.log_lock.acquire(timeout=0.4)
        except TimeoutError:
            Thread(target=self.log_task, args=(level, values, sep))
            return

        now_time = strftime("%H:%M:%S.") + str(time()).split(".")[-1][:3]
        log = {"id": self.log_count, "time": now_time, "level": level, "message": sep.join(map(str, values))}

        if self.log_count in [i["id"] for i in self.logs]:  # 修复了Item n already exists的报错
            log["id"] += 1
            self.log_count += 1

        self.logs.append(log)
        if self.log_list.index(level.lower()) >= self.log_list.index(self.now_level):  # 比较是否超过日志等级
            self.insert_a_log(log)
        self.log_count += 1
        self.set_log_count()

        y_view = [round(i, 1) for i in self.list_box.yview()]
        if y_view[1] == 1.0 or (all(i == 0.0 for i in y_view)) or y_view[0] == y_view[1]:
            self.list_box.yview_moveto(1.0)
        if self.log_lock.locked():
            self.log_lock.release()

    def log_task(self, level: str, *values: object, sep: str = " "):
        sleep(0.1)
        self.log(level, *values, sep=sep)

    def on_level_change(self, _):
        self.now_level = self.levels[self.select_combobox.get()]
        self.list_box.delete(*self.list_box.get_children())
        for log in self.logs:
            if self.log_list.index(log["level"]) >= self.log_list.index(self.now_level):  # 比较是否超过日志等级
                self.insert_a_log(log)

    def insert_a_log(self, log: dict):
        self.list_box.insert("",
                             END,
                             id=log["id"],
                             values=(log["time"],
                                     self.levels_res[log["level"]],
                                     log["message"]))

    def on_menu(self, event: Event):
        """弹出右键菜单"""
        self.list_box.event_generate("<Button-1>")
        try:
            select = self.list_box.selection()[0]
        except IndexError:
            return
        log_text = self.list_box.item(select)["values"][2]
        menu = Menu()
        menu.add_command(label="复制", command=lambda: copy_clipboard(log_text))
        menu.post(event.x_root, event.y_root)
