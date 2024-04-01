import re
import pyglet
import tkinter
from widgets import *
from typing import Dict
from tkinter import font
from ttkbootstrap import Style
from win32gui import MessageBox
from info_gui import InfoWindow
from subprocess import getoutput
from scanner import ServerScanner
from threading import Thread, Lock
from pyperclip import copy as copy_clipboard
from ttkbootstrap.scrolled import ScrolledFrame
from time import perf_counter, sleep, time, strftime
from win32con import MB_ICONWARNING, MB_YESNOCANCEL, IDYES, MB_ICONERROR, MB_OK, MB_YESNO


def set_default_font():
    font.nametofont("TkDefaultFont").config(family="微软雅黑", size=10)


def load_unifont():
    pyglet.options['win32_gdi_font'] = True
    pyglet.font.add_file("assets/Unifont.otf")


class GUI(ttk.Window):
    def __init__(self):
        super(GUI, self).__init__()

        timer = perf_counter()

        set_default_font()
        self.config_root_window()

        self.title_bar = TitleBar(self)
        self.sep = ttk.Separator()
        self.tabs = Tabs(self)
        self.logger = Logger(self.tabs)
        self.server_scanF = ttk.Frame(self.tabs)
        self.servers = ServerList(self.server_scanF)
        self.scan_bar = ScanBar(self.server_scanF, self.logger, self.servers)

        self.pack_widgets()
        print(f"GUI构建时间: {perf_counter() - timer:.3f}秒")
        Thread(target=load_unifont).start()  # 加载字体

    def config_root_window(self):  # 设置窗体
        self.wm_title("MC服务器扫描器")
        self.style.theme_use("solar")
        self.wm_geometry("754x730")
        self.place_window_center()

    def pack_widgets(self):
        self.title_bar.pack(fill=X, padx=10)
        self.sep.pack(fill=X, padx=10, pady=3)
        self.tabs.pack(fill=BOTH, expand=True, pady=0)
        self.servers.pack(fill=BOTH, expand=True, padx=3, pady=3)
        self.scan_bar.pack(side=BOTTOM, fill=X, padx=3, pady=3)
        self.tabs.add(self.server_scanF, text="控制面板")
        self.tabs.add(self.logger, text="日志")


class ServersFilter:
    def __init__(self, version: str, enable_re: bool):
        self.version_keywords = version
        self.enable_re = enable_re

    def filter(self, data: ServerInfo) -> bool:
        return self.version_match(data)

    def version_match(self, data: ServerInfo):
        version_name = data.version_name
        if self.enable_re:
            try:
                return bool(re.match(self.version_keywords, version_name))
            except re.error:
                raise ValueError("正则表达式错误")
        else:
            return self.version_keywords in version_name


class ServerFilter(ttk.Frame):
    def __init__(self, master: Misc):
        super(ServerFilter, self).__init__(master)
        self.version_frame = ttk.Frame(self)
        self.version_entry = TextEntry(self.version_frame, tip="版本名: ")
        self.version_re_var = tk.BooleanVar(self.version_frame, value=False)
        self.version_re_check = ttk.Checkbutton(self.version_frame,
                                                text="正则匹配",
                                                style="round-toggle",
                                                variable=self.version_re_var)

        self.sep = ttk.Separator(self, orient=VERTICAL)

        self.buttons = ttk.Frame(self)
        self.reset_button = ttk.Button(self.buttons, text="重置", style="outline")
        self.filter_button = ttk.Button(self.buttons, text="筛选", style="outline")

        self.version_entry.entry.bind("<Return>", self.filtration)
        self.filter_button.bind("<Button-1>", self.filtration)
        self.reset_button.bind("<Button-1>", self.reset)

        self.pack_weights()

    def pack_weights(self):
        self.version_frame.pack_configure(side=LEFT, fill=X, expand=True)
        self.version_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.version_re_check.pack(side=LEFT, padx=5)

        self.sep.pack(side=LEFT, fill=Y, padx=5)

        self.buttons.pack(side=LEFT)
        self.reset_button.pack(side=LEFT, padx=5)
        self.filter_button.pack(side=LEFT, padx=5)

    def reset(self, *_):
        self.version_entry.delete(0, END)
        self.version_re_var.set(False)
        self.filtration()

    def filtration(self, *_):
        version = self.version_entry.get()
        enable_re = self.version_re_var.get()
        _filter = ServersFilter(version, enable_re)
        self.master.reload_server(_filter)


class ServerList(ttk.LabelFrame):
    def __init__(self, master: Misc):
        super(ServerList, self).__init__(master, text="服务器列表")
        self.server_px = 72
        self.add_lock = Lock()
        self.bind("<Configure>", self.on_resize)

        self.server_filter = ServerFilter(self)
        self.sep = ttk.Separator(self, orient=HORIZONTAL)
        self.servers_frame = ScrolledFrame(self, autohide=True)
        self.empty_tip = ttk.Label(self, text="没有服务器", font=("微软雅黑", 25))

        self.server_filter.pack(fill=X, padx=3, pady=3)
        self.sep.pack(fill=X, padx=3, pady=3)
        self.servers_frame.pack(fill=BOTH, expand=True)
        self.empty_tip.place(relx=0.5, rely=0.5, anchor=CENTER)

        self.servers: list[ServerInfo] = []
        self.server_frames: list[ttk.Frame] = []

    def add_server(self, info: ServerInfo):
        with self.add_lock:
            self.servers.append(info)
            server_frame = ServerFrame(self.servers_frame, info)
            server_frame.pack(fill=X, expand=True, pady=4)
            self.server_frames.append(server_frame)
            self.empty_tip.place_forget()

    def reload_server(self, server_filter: ServersFilter):
        for child in self.server_frames:
            child.destroy()
        self.server_frames.clear()

        for info in self.servers:
            try:
                if server_filter.filter(info):
                    server_frame = ServerFrame(self.servers_frame, info)
                    server_frame.pack(fill=X, expand=True, pady=4)
                    self.server_frames.append(server_frame)
            except ValueError:
                MessageBox(self.winfo_id(), "不规范的正则表达式", "服务器过滤错误", MB_ICONERROR | MB_OK)
                return

        self.on_resize()

    def on_resize(self, *_):
        if len(self.server_frames) > 0:
            try:
                self.empty_tip.place_forget()
            except tkinter.TclError:
                pass
        else:
            self.empty_tip.place(relx=0.5, rely=0.5, anchor=CENTER)


class ServerFrame(ttk.Frame):
    def __init__(self, master: Misc, data: ServerInfo):
        super().__init__(master)
        self.default_favicon = None
        self.data = data
        self.info_window = None

        self.favicon = ttk.Label(self)
        self.MOTD = MOTD(self)
        self.base_info = ttk.Label(self, font=("微软雅黑", 9))

        self.events_add()
        self.pack_weights()
        self.load_data()

    def events_add(self):
        self.keep_text_top()
        self.MOTD.configure(yscrollcommand=self.keep_text_top)
        self.favicon.bind("<MouseWheel>", lambda e: self.event_generate("<MouseWheel>", delta=e.delta))
        self.MOTD.bind("<MouseWheel>", lambda e: self.event_generate("<MouseWheel>", delta=e.delta))

        self.favicon.bind("<Double-Button-1>", self.load_window)
        self.MOTD.bind("<Double-Button-1>", self.load_window)
        self.bind("<Double-Button-1>", self.load_window)

        self.favicon.bind("<Button-3>", self.pop_menu)
        self.MOTD.bind("<Button-3>", self.pop_menu)
        self.bind("<Button-3>", self.pop_menu)

    def keep_text_top(self, *_):
        self.MOTD.yview_moveto(0.02)

    def load_data(self):
        if self.data.has_favicon:
            self.favicon.configure(image=self.data.favicon_photo)
        else:
            self.default_favicon = tk.PhotoImage(master=self, file=r"assets/server_icon.png")
            self.favicon.configure(image=self.default_favicon)

        self.MOTD.load_motd(self.data)
        self.base_info.configure(text=f"人数:{self.data.player_online}/{self.data.player_max}, "
                                      f"版本: {self.data.version_name}")

    def pack_weights(self):
        self.MOTD.configure(spacing1=-5, spacing3=1)
        self.favicon.pack(side=LEFT)
        self.MOTD.pack(anchor=NW, fill=BOTH, expand=True)
        self.base_info.pack(anchor=NW, ipady=0, ipadx=0)

    def load_window(self, *_):
        if isinstance(self.info_window, ttk.Toplevel):
            if self.info_window.winfo_exists():
                self.info_window.focus_set()
                return
        self.info_window: InfoWindow = InfoWindow(self, self.data)

    def load_motd_text(self):
        text = ""
        for extra in self.data.description_json:
            text += extra["text"]
        return text

    def pop_menu(self, event: tk.Event):
        menu = ttk.Menu()
        menu.add_command(label="复制地址", command=self.copy_ip)
        menu.add_command(label="复制MOTD", command=self.copy_motd)
        menu.add_separator()
        menu.add_command(label="删除服务器", command=self.delete_server)
        menu.add_command(label="删除所有服务器", command=self.delete_all_servers)
        menu.post(event.x_root, event.y_root)

    def delete_server(self):
        self.destroy()

    def delete_all_servers(self):
        ret = MessageBox(self.winfo_id(), "确定要删除所有服务器吗？", "删除所有服务器", MB_YESNOCANCEL | MB_ICONWARNING)
        if ret == IDYES:
            try:
                for child in self.master.winfo_children():
                    if child is not self:
                        child.destroy()
                self.destroy()
            except Exception as e:
                print(e.args)

    def copy_ip(self):
        copy_clipboard(f"{self.data.host}:{self.data.port}")

    def copy_motd(self):
        copy_clipboard(self.load_motd_text())


class InfoProgressBar(ttk.Frame):
    def __init__(self, master: Misc, interval: float, text: str):
        super().__init__(master)
        self.value = 0
        self.last_value = 0
        self.last_update = time()
        self.speed_avg = []
        self._max = 0
        self.interval = interval

        self.text = ttk.Label(self, text=text)
        self.progress = ProgressBar(self)
        self.progress_text = ttk.Label(self, text="0 ports/s")
        self.text.pack(side=LEFT)
        self.progress.pack(side=LEFT, fill=X, expand=True)
        self.progress_text.pack(side=LEFT)

    def reset(self, _max: int):
        self.value = 0
        self.last_value = 0
        self.last_update = time()
        self.speed_avg.clear()
        self._max = _max
        self.progress_text.configure(text="0 ports/s")
        self.progress.set_percentage(0, "0%")

    def update_progress_text(self, speed: float):
        self.progress_text.configure(text=f"{speed:.2f} ports/s")

    def update_progress(self, value: float):
        if time() - self.last_update > self.interval:
            self.update_now(value)

    def update_now(self, value: float):
        if len(self.speed_avg) > 50:
            self.speed_avg.pop(0)
        elif len(self.speed_avg) == 0:
            self.speed_avg.append(0)

        percentage = value / self._max
        self.progress.set_percentage(percentage, f"{round(percentage * 100, 2)}%")
        self.update_progress_text(sum(self.speed_avg) / len(self.speed_avg))

        self.speed_avg.append((value - self.last_value) / (time() - self.last_update))
        self.last_value = value
        self.last_update = time()

    def finish(self):
        self.update_progress_text(0)


class ProgressBar(ttk.Canvas):
    def __init__(self, master: Misc, text: str = "0%"):
        super(ProgressBar, self).__init__(master, height=26)
        self.color = Style().colors
        self.bind("<Configure>", self.redraw)
        self.bind("<<ThemeChanged>>", self.change_color)
        self.percentage = 0
        self.text = text
        self.redraw()

    def change_color(self, *_):
        self.color = Style().colors
        self.redraw()

    def redraw(self, *_):
        self.delete(ALL)
        width = self.winfo_width()
        bar_x = int((width - 4) * self.percentage)
        if bar_x == 1:
            self.create_line(1, 1, 1, 26, fill=self.color.success)
        elif bar_x > 1:
            self.create_rectangle(1, 1, bar_x, 26 - 2, fill=self.color.success, outline=self.color.success)  # 06B025

        self.create_rectangle(0, 0, width - 1, 26 - 1, outline=self.color.border)
        self.create_text(width // 2, 13, text=self.text, fill=self.color.fg)

    def set_percentage(self, percentage: float, text: str = None):
        self.percentage = percentage
        self.text = text if text is not None else self.text
        self.redraw()


class PauseButton(ttk.Button):
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


class Title(ttk.Label):
    def __init__(self, master: Misc):
        super(Title, self).__init__(master)
        self.configure(text="Minecraft服务器扫描器")
        self.configure(font=("微软雅黑", 24))


class Logger(ttk.Frame):
    def __init__(self, master: Misc):
        super(Logger, self).__init__(master)

        self.logs = []
        self.levels = {"信息": INFO, "警告": WARNING, "错误": ERROR}
        self.levels_res = {v: k for k, v in self.levels.items()}
        self.log_list = list(self.levels.values())
        self.log_count = 0
        self.now_level = INFO

        # 信息条
        self.info_bar = ttk.Frame(self)
        self.info_bar.pack(fill=X)

        # 日志等级选择框
        self.select_frame = ttk.Frame(self.info_bar)
        self.select_text = ttk.Label(self.select_frame, text="日志等级:")
        self.select_combobox = ttk.Combobox(self.select_frame, values=["信息", "警告", "错误"], state=READONLY)
        self.select_combobox.set("信息")
        self.select_combobox.bind("<<ComboboxSelected>>", self.on_level_change)
        self.select_text.pack(side=LEFT, padx=5)
        self.select_combobox.pack(side=LEFT, padx=5)
        self.select_frame.pack(side=LEFT, padx=5, pady=5)

        # 日志数量显示
        self.log_count_label = ttk.Label(self.info_bar, text="日志数量: 0")
        self.log_count_label.pack(side=RIGHT, padx=5, pady=5)

        # 日志显示列表
        self.list_box = ttk.Treeview(self, columns=["0", "1", "2"], show=HEADINGS)
        self.list_box.column("0", width=80, anchor=CENTER)
        self.list_box.column("1", width=21, anchor=CENTER)
        self.list_box.column("2", width=440)
        self.list_box.heading("0", text="时间")
        self.list_box.heading("1", text="等级")
        self.list_box.heading("2", text="日志", anchor=W)
        self.list_box.configure(selectmode=BROWSE)
        self.list_box.bind("<Button-3>", self.on_menu)
        self.list_box.pack(fill=BOTH, expand=True)

    def set_log_count(self):
        self.log_count_label.configure(text=f"日志数量: {self.log_count}")

    def log(self, level: str, *values: object, sep: str = " "):
        now_time = strftime("%H:%M:%S.") + str(time()).split(".")[-1][:3]
        log = {"id": self.log_count, "time": now_time, "level": level, "message": sep.join(map(str, values))}
        self.logs.append(log)
        if self.log_list.index(level.lower()) >= self.log_list.index(self.now_level):  # 比较是否超过日志等级
            self.insert_a_log(log)
        self.log_count += 1
        self.set_log_count()

    def on_level_change(self, _):
        self.now_level = self.levels[self.select_combobox.get()]
        self.list_box.delete(*self.list_box.get_children())
        for log in self.logs:
            if self.log_list.index(log["level"]) >= self.log_list.index(self.now_level):  # 比较是否超过日志等级
                self.insert_a_log(log)

    def insert_a_log(self, log: dict):
        self.list_box.insert("", END, id=log["id"], values=(log["time"], self.levels_res[log["level"]], log["message"]))

    def on_menu(self, event: tk.Event):
        """弹出右键菜单"""
        self.list_box.event_generate("<Button-1>")
        try:
            select = self.list_box.selection()[0]
        except IndexError:
            return
        log_text = self.list_box.item(select)["values"][2]
        menu = ttk.Menu()
        menu.add_command(label="复制", command=lambda: copy_clipboard(log_text))
        menu.post(event.x_root, event.y_root)


class TitleBar(ttk.Frame):
    def __init__(self, master: Misc):
        super(TitleBar, self).__init__(master)
        self.title_text = Title(self)
        self.theme_selector = ThemesSelector(self)
        self.title_text.pack(side=LEFT, padx=5, pady=5)
        self.theme_selector.pack(side=RIGHT, padx=5, pady=5)


class ThemesSelector(ttk.Frame):
    def __init__(self, master: Misc):
        super(ThemesSelector, self).__init__(master)
        self.select_text = ttk.Label(self, text="选择主题:")
        self.theme_selector = ttk.Combobox(self, values=Style().theme_names(), state=READONLY)
        self.theme_selector.set(Style().theme_use())
        self.theme_selector.bind("<<ComboboxSelected>>", self.on_theme_selected)
        self.select_text.pack(side=LEFT, padx=5, pady=5)
        self.theme_selector.pack(side=LEFT, padx=5, pady=5)

    def on_theme_selected(self, _):
        Style().theme_use(self.theme_selector.get())


class RangeSelector(ttk.Frame):
    def __init__(self, master: Misc, text: str = "范围选择:", start: int = 0, stop: int = 100):
        super(RangeSelector, self).__init__(master)
        self.start = min(start, stop)
        self.stop = max(start, stop)
        self.start_per = self.start / (self.start + self.stop)
        self.stop_per = self.stop / (self.start + self.stop)

        self.range_text = ttk.Label(self, text=text)
        self.range_selector = RangeScale(self)
        self.min_entry = ttk.Entry(self, width=8)
        self.max_entry = ttk.Entry(self, width=8)

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


class ScanBar(ttk.LabelFrame):
    def __init__(self, master: Misc, logger: Logger, server_list: ServerList):
        super(ScanBar, self).__init__(master, text="扫描")
        self.logger = logger
        self.server_list = server_list

        self.in_scan = False
        self.scan_obj = ServerScanner()
        self.callback_lock = Lock()
        self.progress_var = 0

        # 进度条
        self.progress_bar = InfoProgressBar(self, interval=0.05, text="扫描进度: ")
        self.progress_bar.pack(side=BOTTOM, fill=X, expand=True, padx=5, pady=5)

        # 分割线2
        self.sep2 = ttk.Separator(self)
        self.sep2.pack(side=BOTTOM, fill=X, padx=5)

        # 输入 Frame
        self.input_frame = ttk.Frame(self)
        self.host_input = TextCombobox(self.input_frame, "域名: ", vars.servers)
        self.timeout_input = EntryScaleFloat(self.input_frame, 0.1, 3.0, 0.2, "超时时间: ")
        self.thread_num_input = EntryScaleInt(self.input_frame, 1, 256, 192, "线程数: ")
        self.range_input = RangeSelector(self.input_frame, "端口选择: ", 1024, 65535)

        self.input_frame.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        self.host_input.pack(fill=X, expand=True)
        self.timeout_input.pack(fill=X, expand=True)
        self.thread_num_input.pack(fill=X, expand=True)
        self.range_input.pack(fill=X, expand=True)

        # 分割线
        self.sep = ttk.Separator(self, orient="vertical")
        self.sep.pack(side=LEFT, fill=Y)

        # 扫描控制 Frame
        self.buttons = ttk.Frame(self)
        self.start_button = ttk.Button(self.buttons, text="开始扫描", command=self.start_scan)
        self.pause_button = PauseButton(self.buttons, self.resume_scan, self.pause_scan, state=DISABLED)
        self.stop_button = ttk.Button(self.buttons, text="停止", command=self.stop_scan, state=DISABLED)

        self.buttons.pack(side=RIGHT, padx=5)
        self.start_button.pack(fill=X, expand=True, pady=2)
        self.pause_button.pack(fill=X, expand=True, pady=2)
        self.stop_button.pack(fill=X, expand=True, pady=2)

    def callback(self, info: Any):
        with self.callback_lock:
            self.progress_var += 1
            self.progress_bar.update_progress(self.progress_var)
            if isinstance(info, ServerInfo):
                self.server_list.add_server(info)
                self.logger.log(INFO, f"[{info.port}]:", "检测到MC服务器")
            elif isinstance(info, dict):
                if info["status"] != "offline":
                    self.logger.log(info["status"], f"[{info['info']['port']}]:", info["msg"])

    def start_scan(self, start: int = None, stop: int = None):  # 20500 - 25000
        if self.in_scan:
            return

        host = self.host_input.get()
        thread_num = self.thread_num_input.get_value()
        timeout = self.timeout_input.get_value()
        if not (start and stop):
            start, stop = self.range_input.get()

        if not self.check_host(host):
            return

        self.in_scan = True
        self.start_button.configure(state=DISABLED)
        self.pause_button.configure(state=NORMAL)
        self.stop_button.configure(state=NORMAL)

        self.progress_var = 0
        self.progress_bar.reset(stop - start)
        self.scan_obj.config(host, timeout, thread_num)
        Thread(target=self.scan_obj.run, args=(range(start, stop), self.callback)).start()
        Thread(target=self.check_over_thread, daemon=True).start()

    def pause_scan(self):
        def task():
            sleep(0.1)
            self.pause_button.configure(state=DISABLED)
            self.scan_obj.pause()
            self.logger.log(INFO, "暂停扫描")
            while self.scan_obj.working_worker > 0:
                self.logger.log(INFO, "等待所有线程暂停工作, 工作中线程数量:", self.scan_obj.working_worker)
                sleep(0.1)
            self.pause_button.configure(state=NORMAL)

        Thread(target=task, daemon=True).start()

    def resume_scan(self):
        def task():
            self.pause_button.configure(state=DISABLED)
            self.scan_obj.resume()
            self.logger.log(INFO, "恢复扫描")
            while self.scan_obj.working_worker != self.scan_obj.thread_num:
                self.logger.log(INFO, "等待所有线程开始工作, 工作中线程数量:", self.scan_obj.working_worker)
                sleep(0.1)
            self.pause_button.configure(state=NORMAL)

        Thread(target=task, daemon=True).start()

    def stop_scan(self):
        if not self.in_scan:
            return
        self.in_scan = False
        self.pause_button.configure(state=DISABLED)
        self.stop_button.configure(state=DISABLED)

        def stop_task():
            self.in_scan = False
            self.scan_obj.stop()
            while self.scan_obj.worker_count != 0:
                sleep(0.1)
                self.logger.log(INFO, "等待线程结束, 剩余工作线程线程数量:", self.scan_obj.worker_count)
            self.logger.log(INFO, "线程已全部结束")
            self.start_button.configure(state=NORMAL)
            self.progress_stop()

        Thread(target=stop_task).start()

    def check_over_thread(self):
        if not self.in_scan:
            return
        while self.scan_obj.in_scan:
            sleep(0.1)

        if self.in_scan:
            self.in_scan = False
            self.stop_button.configure(state=DISABLED)
            self.pause_button.configure(state=DISABLED)
            self.start_button.configure(state=NORMAL)
            self.progress_stop()

    def progress_stop(self):
        self.progress_bar.speed_avg.clear()
        self.progress_bar.update_now(self.progress_var)

    def check_host(self, host: str) -> bool:
        self.logger.log(INFO, f"检测域名 [{host}] ...")
        self.logger.log(INFO, "樱花穿透域名检测...")
        if host.startswith("frp.") and host.endswith(".top"):
            self.logger.log(WARNING, f"疑似检测到Sakura Frp域名 ({host})")
            ret = MessageBox(self.winfo_id(),
                             f"域名 [{host}] 疑似为Sakura Frp域名, 扫描会封禁你的IP, 请问是否继续?",
                             "域名警告",
                             MB_YESNO | MB_ICONWARNING)
            if ret != IDYES:
                return False

        self.logger.log(INFO, "开始ping测试...")
        if ScanBar.ping_host(host):
            self.logger.log(INFO, "域名存活")
            return True
        else:
            self.logger.log(ERROR, "域名无法连接")
            MessageBox(self.winfo_id(),
                       f"域名 [{host}] ping测试不通过",
                       "域名错误",
                       MB_OK | MB_ICONERROR)
            return False

    @staticmethod
    def ping_host(host: str) -> bool:
        cmd = f"ping -n 1 {host}"
        output = getoutput(cmd)
        return "丢失 = 0" in output
