# -*- coding: UTF-8 -*-
from copy import deepcopy
from tkinter import Listbox
from tkinter.messagebox import showinfo

from ttkbootstrap.tooltip import ToolTip
from io import BytesIO

from Gui.Widgets import *
from Libs.Vars import user_settings_loader, debug
from Network.Scanner import DescriptionParser, Port, ServerInfo


class InfoWindow(Toplevel, Infer):
    """信息主窗口"""

    def __init__(self, master: Misc, data: ServerInfo):
        from Gui.Widgets import MOTD, Tabs

        super(InfoWindow, self).__init__(master=master)
        self.data = data
        self.load_window_title()
        self.wm_resizable(True, True)

        self.favicon = Label(self)
        self.MOTD = MOTD(self)
        self.tab = Tabs(self)
        self.base_info = BaseInfo(self)
        self.reload_button = Button(self.base_info, text="重新获取信息", command=self.reget_info, style="success")
        self.version_info = VersionInfo(self)

        if self.data.mod_server:
            self.mod_info = ModInfo(self)
            self.mod_info.load_data(self.data)

        self.load_data(data)
        self.pack_widgets()

    def load_data(self, data: ServerInfo):
        if data.has_favicon:
            self.favicon.image_io = BytesIO(data.favicon_data)
        else:
            with open(r"assets\server_icon.png", "rb") as f:
                self.favicon.image_io = BytesIO(f.read())
        self.favicon.image = Image.open(self.favicon.image_io, formats=["PNG"])
        self.favicon.image = self.favicon.image.resize((128, 128))
        self.favicon.favicon = ImageTk.PhotoImage(self.favicon.image)
        self.favicon.configure(image=self.favicon.favicon)
        # 将 favicon 引用传递给 self.favicon.image, 使其变成 self.favicon 的属性, 防止其被 gc 回收
        self.load_icon(self.favicon.favicon)

        self.data = data
        self.MOTD.load_data(self.data)
        self.base_info.load_data(self.data)
        self.version_info.load_data(self.data)

    def reget_info(self):
        server_status = Port(self.data.host, self.data.port).get_server_info()
        if server_status["status"] == "offline":
            showinfo("服务器已经死了，都是你害的辣 (doge", "服务器已离线", parent=self)
        elif server_status["status"] == "error":
            showinfo("服务器有点问题：" + server_status["msg"], "服务器：?", parent=self)
        elif server_status["status"] == "online":
            self.load_data(ServerInfo(server_status["info"]))

    def load_icon(self, favicon: PhotoImage):
        """
        将一个 PIL.ImageTK.PhotoImage 加载为 GUI 图标

        Args:
            favicon: 一个 PIL.ImageTK.PhotoImage 实例化对象
        """
        self.iconphoto(False, favicon)

    def pack_widgets(self):
        self.favicon.pack_configure()
        self.MOTD.configure(height=2)
        self.MOTD.pack_configure(fill=X)

        self.tab.pack(fill=BOTH, expand=True)
        self.tab.add(self.base_info, text="基本信息")
        self.reload_button.pack_configure(pady=5)
        self.tab.add(self.version_info, text="版本信息")
        if self.data.mod_server:
            self.tab.add(self.mod_info, text="模组信息")

    def load_window_title(self):
        text = ""
        for extra in self.data.description_json:
            text += extra["text"]
        self.title(text)


class PlayersInfo(Frame, Infer):
    """玩家信息组件"""

    def __init__(self, master: Misc):
        super(PlayersInfo, self).__init__(master)

        self.leave_id = None
        self.motion_id = None
        self.text = Label(self, anchor=CENTER)
        self.player_list = Listbox(self, width=15)
        self.tip = ToolTip(self.player_list, "在这个服务器里我们找不到人 :-(", delay=0, alpha=0.8)
        self.text.pack(side=TOP, fill=X)
        self.player_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.data = None
        self.now_item = None

    def load_data(self, data: ServerInfo):
        self.data = data

        self.text.configure(text=f"人数：{data.player_online}/{data.player_max}")
        self.player_list.delete(0, END)
        for player in data.players:
            self.player_list.insert(END, player["name"])
        if len(data.players) > 0:
            self.player_list.unbind_all("<Enter>")
            self.player_list.bind("<Enter>", self.enter)
            self.player_list.bind("<Enter>", self.tip.enter, "+")
        else:
            self.tip.hide_tip()

        self.now_item = None

    def enter(self, event: Event):
        item = self.player_list.nearest(event.y)
        if item == -1:
            return
        self.tip.show_tip()
        uuid = self.data.players[item]['id']
        self.tip.toplevel.winfo_children()[0].configure(text="UUID: " + uuid)
        self.now_item = item
        self.leave_id = self.player_list.bind("<Leave>", self.leave, "+")
        self.motion_id = self.player_list.bind("<Motion>", self.update_tip, "+")

    def leave(self, _):
        self.player_list.unbind("<Motion>", self.motion_id)
        self.player_list.bind("<Motion>", self.tip.move_tip)
        self.player_list.unbind("<Leave>", self.leave_id)
        self.player_list.bind("<Leave>", self.tip.leave)

    def update_tip(self, event: Event):
        if self.tip.toplevel is not None:
            item = self.player_list.nearest(event.y)
            if item == -1 or item == self.now_item:
                return
            self.tip.toplevel.winfo_children()[0].configure(text="UUID: " + self.data.players[item]['id'])
            self.now_item = item


class BaseInfo(Frame, Infer):
    """服务器基本信息组件"""

    def __init__(self, master: Misc):
        super(BaseInfo, self).__init__(master)
        self.data = None

        self.player_list = PlayersInfo(self)
        self.host = Label(self, anchor=CENTER)
        self.ping = Label(self, anchor=CENTER)
        self.version = Label(self, anchor=CENTER)
        self.host_copy_b = Button(self, text="复制地址")

        self.pack_widgets()
        if debug:
            self.print_data = Button(self, text="打印数据", command=lambda: print(self.data.parsed_data))
            self.print_data.pack(pady=5)

    def load_data(self, data: ServerInfo):
        self.data = data

        self.player_list.load_data(data)
        self.host.configure(text=f"地址：{data.host}:{data.port}")
        self.ping.configure(text=f"延迟：{data.ping}ms")
        self.version.configure(text=f"版本：{data.version_name}")
        self.host_copy_b.configure(command=lambda: copy_clipboard(f"{data.host}:{data.port}"))

    def pack_widgets(self):
        self.player_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.host.pack()
        self.ping.pack()
        self.version.pack()
        self.host_copy_b.pack()


class VersionInfo(Frame, Infer):
    """版本信息组件"""

    def __init__(self, master: Misc):
        from Gui.Widgets import MOTD

        super(VersionInfo, self).__init__(master)
        self.data = None
        self.if_version_name_shown_as_label: bool = user_settings_loader.configs['if_version_name_shown_as_label']

        self.version_name_frame = Frame(self)
        self.version_name_label = Label(self.version_name_frame, anchor=CENTER)
        self.version_name_text = MOTD(self.version_name_frame)
        self.minecraft_version = Label(self, anchor=CENTER)
        self.protocol_version = Label(self, anchor=CENTER)
        self.major_name = Label(self, anchor=CENTER)
        self.version_type = Label(self, anchor=CENTER)

        self.bind_tip()
        self.pack_widgets()

    def bind_tip(self):
        tips = [(self.version_name_label, "服务器版本名 (服务器返回结果)\n部分服务器会修改此部分"),
                (self.version_name_text, "服务器版本名 (服务器返回结果)\n部分服务器会修改此部分"),
                (self.minecraft_version, "服务器版本名 (就是大家平时的叫法)"),
                (self.protocol_version, "服务器协议版本号 (几乎每个MC版本都有不同版本的协议版本号)"),
                (self.major_name, "大版本 (该服务器是属于哪个大版本的)"),
                (self.version_type, "服务器版本的类型")]
        for tip in tips:
            ToolTip(tip[0], tip[1], delay=0, alpha=0.8)

    def pack_widgets(self):
        self.version_name_frame.pack()
        self.version_name_label.pack(side=LEFT)
        if not self.if_version_name_shown_as_label:
            self.version_name_text.configure(height=1, width=20)
            self.version_name_text.pack(side=LEFT)
        self.minecraft_version.pack()
        self.protocol_version.pack()
        self.major_name.pack()
        self.version_type.pack()

    def load_data(self, data: ServerInfo):
        self.data = data

        if "§" in data.version_name:
            description_json = DescriptionParser.format_chars_to_extras(data.version_name)
        else:
            description_json = [{"text": data.version_name}]
        self.version_name_label.configure(text="版本名：")
        if self.if_version_name_shown_as_label:
            self.version_name_label.configure(text=f"版本名：{data.version_name}")
        self.version_name_text.load_motd(description_json)
        self.minecraft_version.configure(text=f"正式版本名：{data.protocol_name}")
        self.protocol_version.configure(text=f"协议版本号：{data.protocol_version}")
        self.major_name.configure(text=f"大版本：{data.protocol_major_name}")

        if data.version_type == "release":
            self.version_type.configure(text="版本类型：正式版")
        elif data.version_type == "snapshot":
            self.version_type.configure(text=f"版本类型：快照版")
        else:
            self.version_type.configure(text=f"版本类型(未检测)：{data.version_type}")


class ModInfo(Frame, Infer):
    """模组信息组件"""

    def __init__(self, master: Misc):
        super(ModInfo, self).__init__(master)

        self.data = None
        self.mod_pack_info = Label(self)
        self.mod_list = Treeview(self, show=HEADINGS, columns=["mod", "version"])
        self.mod_info = Frame(self)

        self.pack_widgets()

    def pack_widgets(self):
        self.mod_list.heading("mod", text="模组名")
        self.mod_list.heading("version", text="版本")
        self.mod_list.bind("<Button-1>", self.select_mod)

        self.mod_pack_info.pack_configure(fill=X)
        self.mod_list.pack_configure(fill=BOTH, expand=True, side=LEFT)
        self.mod_info.pack_configure(fill=BOTH, expand=True, side=LEFT)

    def load_data(self, data: ServerInfo):
        print("Mod Pack Server Info:", data.mod_pack_info)
        self.data = data
        self.mod_list.delete(*self.mod_list.get_children())
        for mod in data.mod_list.items():
            if "OHNOES" in mod[1]:
                mod = (mod[0], "未知")  # 已修复在加载旧扫描记录时的鬼脸小人
            self.mod_list.insert("", END, values=mod)

    def select_mod(self, event: Event):
        item_id = self.identify(event.x, event.y)
        if item_id == "border":
            return
        print("PASS ITEM:", item_id)
        name, version = self.mod_list.get_children(item_id)
        print("Mod Name:", name, "  ", "Version:", version)
