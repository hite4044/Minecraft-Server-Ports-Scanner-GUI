# -*- coding: UTF-8 -*-
import sys
from base64 import b64decode, b64encode
from json import load as json_load, JSONDecodeError, dump as json_dump
from pickle import loads as pickle_loads, dumps as pickle_dumps
from re import match, error
from tkinter import filedialog
from tkinter.messagebox import askyesnocancel, showerror
from typing import Dict

from pyperclip import copy
from ttkbootstrap.scrolled import ScrolledFrame

from Gui.InfoGui import InfoWindow
from Gui.Widgets import *
from Libs.WinLib import override_msg_window_buttons


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
                return bool(match(self.version_keywords, version_name))
            except error:
                raise ValueError("正则表达式错误")
        else:
            return self.version_keywords in version_name


class ServerFilter(Frame):
    def __init__(self, master: Misc):
        super(ServerFilter, self).__init__(master)
        self.version_frame = Frame(self)
        self.version_entry = TextEntryFrame(self.version_frame, tip="版本名: ")
        self.version_re_var = BooleanVar(self.version_frame, value=False)
        self.version_re_check = Checkbutton(self.version_frame,
                                            text="正则匹配",
                                            style="round-toggle",
                                            variable=self.version_re_var)

        self.sep = Separator(self, orient=VERTICAL)

        self.buttons = Frame(self)
        self.reset_button = Button(self.buttons, text="重置", style="outline")
        self.filter_button = Button(self.buttons, text="筛选", style="outline")

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

    def get_filter(self):
        version = self.version_entry.get()
        enable_re = self.version_re_var.get()
        return ServersFilter(version, enable_re)

    def filtration(self, *_):
        # noinspection PyUnresolvedReferences
        self.master.reload_server(self.get_filter())


class ServerCounter(Label):
    def __init__(self, master: Misc):
        super(ServerCounter, self).__init__(master, text="0/0")

    def update_count(self, show_servers: int, all_servers: int):
        self.configure(text=f"{show_servers}/{all_servers}")


class ServerInfoFrame(Frame):
    def __init__(self, master: Misc):
        super(ServerInfoFrame, self).__init__(master)

        self.server_counter = ServerCounter(self)
        self.server_counter.pack_configure(side=RIGHT, padx=4, pady=4)

    def update_counter(self, show_servers: int, all_servers: int):
        self.server_counter.update_count(show_servers, all_servers)


class RecordBar(Frame):
    def __init__(self, master: Misc, server_list: Any):
        super(RecordBar, self).__init__(master)
        self.server_list = server_list

        self.load_button = Button(self, text="加载", command=self.load_record, style="success-outline")
        self.save_button = Button(self, text="保存", command=self.save_record, style="success-outline")

        self.pack_weights()

    def pack_weights(self):
        self.load_button.pack_configure(side=LEFT)
        self.save_button.pack_configure(side=RIGHT)

    def load_record(self):
        # noinspection PyUnresolvedReferences
        scan_bar = self.master.master.master.master.scan_bar
        fp = filedialog.askopenfilename(title="选择扫描记录文件",
                                        filetypes=[("Server Scan Record", "*.scrd"),
                                                   ("JSON", "*.json"),
                                                   ("All Files", "*.*")])
        if not fp:
            return
        try:
            # 读取数据
            with open(fp, "r", encoding="utf-8") as f:
                data = json_load(f)
            if isinstance(data, list):  # 旧版支持
                data = {"servers": data}
            elif not isinstance(data, dict):
                showerror("扫描记录加载错误", "无法解析文件内容，请检查文件格式", parent=self)
                return
            if not (isinstance(data, dict) and data.get("servers") and data.get("configs")):
                if not isinstance(data, list):
                    showerror("扫描记录加载错误", "无法解析文件内容，请检查文件格式", parent=self)
                    return
                data = {"servers": data}

            # 询问加载方式
            Thread(target=override_msg_window_buttons, args=("追加", "覆盖"), daemon=True).start()
            ret = askyesnocancel("加载方式 ⠀", "怎样加载扫描记录?", parent=self)
            # ret = None  取消
            # ret = False 覆盖
            # ret = True  追加
            if ret is None:  # ret = None
                return
            if not ret:  # ret = False
                self.server_list.delete_all_servers()
            self.load_scan_record(data)

            # 加载配置
            config = data.get("configs")
            if config:
                scan_bar.set_config(config)

        except JSONDecodeError:
            showerror("扫描记录加载错误", "非JSON文本", parent=self)
        except UnicodeDecodeError:
            showerror("扫描记录加载错误", "文件内容解码错误", parent=self)

    def load_scan_record(self, data: Dict):
        """
        加载服务器记录

        Args:
            data: 服务器信息
        """
        # 检查数据中是否存在必需的键
        if "servers" not in data:
            showerror("扫描记录加载错误", "数据加载错误", parent=self)
            return
        for server_obj_bytes in data["servers"]:
            try:
                server_info: ServerInfo = pickle_loads(b64decode(server_obj_bytes))
                server_info.load_favicon_photo()
                self.server_list.add_server(server_info)
            except ModuleNotFoundError:
                import Network.Scanner
                sys.modules['scanner'] = Network.Scanner
                server_info: ServerInfo = pickle_loads(b64decode(server_obj_bytes))
                server_info.load_favicon_photo()
                self.server_list.add_server(server_info)
        if "scanner" in sys.modules:
            del sys.modules["scanner"]  # 删除先前为了修复问题而引入的 scanner

    def save_record(self):
        # noinspection PyUnresolvedReferences
        scan_bar = self.master.master.master.master.scan_bar
        fp = filedialog.asksaveasfilename(confirmoverwrite=True,
                                          title="选择扫描记录文件",
                                          defaultextension=".scrd",
                                          initialfile="扫描记录_" + get_now_time(),
                                          filetypes=[("Server Scan Record", "*.scrd"),
                                                     ("JSON", "*.json"),
                                                     ("All Files", "*.*")])
        if not fp:
            return

        servers = []
        for server_info in self.server_list.server_map.keys():
            copied_info: ServerInfo = copy(server_info)
            copied_info.favicon_photo = None
            servers.append(b64encode(pickle_dumps(copied_info)).decode("utf-8"))
        data = {"servers": servers, "configs": scan_bar.get_config()}

        with open(file=fp, mode="w+", encoding="utf-8") as f:
            json_dump(data, f)


class ServerList(LabelFrame):
    def __init__(self, master: Misc, logger: Logger):
        super(ServerList, self).__init__(master, text="服务器列表")
        self.add_lock = Lock()  # 服务器添加锁
        self.logger = logger  # 日志对象

        self.server_map: Dict[ServerInfo, ServerFrame] = {}  # 服务器映射
        self.show_serverC = 0  # 显示服务器数量
        self.all_serverC = 0  # 总服务器数量

        self.bind("<Configure>", self.update_info_pos)  # 本体设置

        self.server_filter = ServerFilter(self)  # 服务器筛选器
        self.sep = Separator(self, orient=HORIZONTAL)  # 分割线
        self.servers_frame = ScrolledFrame(self, autohide=True, height=300)  # 装服务器的容器
        self.empty_tip = Label(self, text="没有服务器", font=(Vars.user_settings_loader.configs['global_font'], 25))  # 提示
        self.record_bar = RecordBar(self, self)  # 保存加载功能
        self.servers_info = ServerInfoFrame(self.record_bar)  # 服务器数量信息

        self.pack_weights()  # 放置组件

    def pack_weights(self):
        self.server_filter.pack(fill=X, padx=3, pady=3)
        self.sep.pack(fill=X, padx=3, pady=3)
        self.servers_frame.pack(fill=BOTH, expand=True)
        self.record_bar.pack_configure(side=BOTTOM, fill=X)
        self.servers_info.pack_configure(side=RIGHT, padx=5)
        self.update_info_pos()

    def add_server(self, info: ServerInfo, _filter: ServersFilter = None):
        with self.add_lock:
            server_frame = ServerFrame(self.servers_frame, info)
            server_frame.bind("<<Delete>>", self.on_delete_server)
            server_frame.bind("<<DeleteAll>>", self.delete_all_servers)
            can_show, _ = self.can_show(info, _filter)
            if can_show:
                server_frame.grid_configure(pady=4)
                self.show_serverC += 1
            self.server_map[info] = server_frame

            self.all_serverC += 1
            self.empty_tip.place_forget()
            self.servers_info.update_counter(self.show_serverC, self.all_serverC)

    def reload_server(self, server_filter: ServersFilter):
        self.add_lock.acquire(blocking=True)  # 获得锁
        timer = time()
        self.logger.log(DEBUG, "开始重新加载服务器")
        self.show_serverC = 0  # 重置计数器

        for info, server_frame in self.server_map.items():
            can_show, state = self.can_show(info, server_filter)
            if can_show:
                if server_frame.grid_info() == {}:
                    server_frame.grid_configure(pady=4)
                    self.server_map[info] = server_frame
                self.show_serverC += 1  # 增加计数器

            else:
                server_frame.grid_remove()
                if state == 1:
                    self.add_lock.release()
                    self.logger.log(DEBUG, "过滤正则表达式错误")
                    showerror("服务器过滤错误", "不规范的正则表达式", parent=self)
                    return

        self.update_info_pos()  # 更新提示
        self.servers_info.update_counter(self.show_serverC, self.all_serverC)  # 更新计数器
        self.add_lock.release()  # 释放锁
        self.logger.log(DEBUG, f"重载服务器完毕, 用时: {round(time() - timer, 2)}s")

    def can_show(self, info: ServerInfo, _filter: ServersFilter = None) -> (bool, int):
        if _filter is None:
            _filter = self.servers_filter
        try:
            return _filter.filter(info), 0
        except ValueError:
            return False, 1

    def update_info_pos(self, *_):
        if self.show_serverC > 0:
            self.empty_tip.place_forget()
        else:
            self.empty_tip.place(relx=0.5, rely=0.5, anchor=CENTER)

    def on_delete_server(self, event: Event):
        server_frame: ServerFrame = event.widget
        self.server_map.pop(server_frame.data)
        self.all_serverC -= 1
        self.show_serverC -= 1
        self.servers_info.update_counter(self.show_serverC, self.all_serverC)  # 更新计数器

    def delete_all_servers(self, *_):
        ret = askyesnocancel("删除所有服务器", "确定要删除所有服务器吗？", parent=self)
        if not ret:
            return
        try:
            for child in self.server_map.values():
                child.destroy()
            self.server_map.clear()
            self.show_serverC = 0
            self.all_serverC = 0
            self.servers_info.update_counter(0, 0)
        except Exception as e:
            print(e.args)
        self.update_info_pos()

    @property
    def servers_filter(self) -> ServersFilter:
        return self.server_filter.get_filter()


class ServerFrame(Frame):
    def __init__(self, master: Misc, data: ServerInfo):
        super().__init__(master)
        self.default_favicon = None
        self.data = data
        self.info_window = None

        self.favicon = Label(self)
        self.MOTD = MOTD(self)
        self.base_info = Label(self, font=(Vars.user_settings_loader.configs['global_font'], 9))

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
            self.default_favicon = PhotoImage(master=self, file=r"assets/server_icon.png")
            self.favicon.configure(image=self.default_favicon)

        self.MOTD.load_motd(self.data)
        base_info = f"人数:{self.data.player_online}/{self.data.player_max}, " \
                    f"版本: {self.data.version_name}"
        if len(base_info) > 80:
            base_info = base_info[:80] + "..."
        self.base_info.configure(text=base_info)

    def pack_weights(self):
        self.MOTD.configure(spacing1=-5, spacing3=1)
        self.favicon.pack(side=LEFT)
        self.MOTD.pack(anchor=NW, fill=BOTH, expand=True)
        self.base_info.pack(anchor=NW, ipady=0, ipadx=0)

    def load_window(self, *_):
        if isinstance(self.info_window, Toplevel):
            if self.info_window.winfo_exists():
                self.info_window.focus_set()
                return
        self.info_window: InfoWindow = InfoWindow(self, self.data)

    def load_motd_text(self) -> str:
        """
        将一串 MOTD 信息转换为纯文本

        Returns:
            str: 连接后的 MOTD 文本字符串。
        """
        text_list = [extra["text"] for extra in self.data.description_json]
        return ''.join(text_list)

    def pop_menu(self, event: Event):
        menu = Menu()
        menu.add_command(label="复制地址", command=self.copy_ip)
        menu.add_command(label="复制MOTD", command=self.copy_motd)
        menu.add_separator()
        menu.add_command(label="删除服务器", command=self.delete_server)
        menu.add_command(label="删除所有服务器", command=lambda: self.event_generate("<<DeleteAll>>"))
        menu.post(event.x_root, event.y_root)

    def delete_server(self):
        self.event_generate("<<Delete>>")
        self.destroy()

    def copy_ip(self):
        copy_clipboard(f"{self.data.host}:{self.data.port}")

    def copy_motd(self):
        copy_clipboard(self.load_motd_text())
