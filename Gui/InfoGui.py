# -*- coding: UTF-8 -*-
from tkinter import Listbox

from PIL.ImageTk import PhotoImage
from ttkbootstrap.tooltip import ToolTip
from win32con import MB_ICONINFORMATION

from Gui.Widgets import *
from Network.Scanner import DescriptionParser, Port, ServerInfo


class Infer:
    """一个信息组件，必须含有load_data方法"""

    def load_data(self, data: ServerInfo):
        pass


class InfoWindow(Toplevel, Infer):
    """信息主窗口"""

    def __init__(self, master: Misc, data: ServerInfo):
        from Gui.Widgets import MOTD, Tabs

        super(InfoWindow, self).__init__(master=master)
        self.favicon_image = None
        self.default_favicon = None
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

        self.load_data(data)
        self.pack_widgets()

    # FIXME: 这是为什么？没人碰了他！
    def load_data(self, data: ServerInfo):
        self.data = data
        if data.has_favicon:
            self.favicon_image = self.data.favicon
        else:
            self.favicon_image = Image.open(r"assets\server_icon.png")
        self.favicon_image = self.favicon_image.resize((128, 128))
        self.default_favicon = PhotoImage(self.favicon_image)
        self.favicon.configure(image=self.default_favicon)

        self.MOTD.load_motd(self.data)
        self.base_info.load_data(self.data)
        self.version_info.load_data(self.data)

        self.load_icon()

    def reget_info(self):
        server_status = Port(self.data.host, self.data.port).get_server_info()
        if server_status["status"] == "offline":
            MessageBox(self.winfo_id(),
                       "服务器已经死了，都是你害的辣 (doge",
                       "服务器已离线",
                       MB_OK | MB_ICONINFORMATION)
        elif server_status["status"] == "error":
            MessageBox(self.winfo_id(),
                       "服务器有点问题：" + server_status["msg"],
                       "服务器：?",
                       MB_OK | MB_ICONINFORMATION)
        elif server_status["status"] == "online":
            self.load_data(ServerInfo(server_status["info"]))

    def load_icon(self):
        self.iconphoto(False, self.default_favicon)

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

        self.version_name_frame = Frame(self)
        self.version_name_text = Label(self.version_name_frame, anchor=CENTER)
        self.version_name_MOTD = MOTD(self.version_name_frame)
        self.minecraft_version = Label(self, anchor=CENTER)
        self.protocol_version = Label(self, anchor=CENTER)
        self.major_name = Label(self, anchor=CENTER)
        self.version_type = Label(self, anchor=CENTER)

        self.bind_tip()
        self.pack_widgets()

    def bind_tip(self):
        tips = [(self.version_name_text, "服务器版本名 (服务器返回结果)"),
                (self.version_name_MOTD, "服务器版本名 (服务器返回结果)"),
                (self.minecraft_version, "服务器版本名 (就是大家平时的叫法)"),
                (self.protocol_version, "服务器协议版本号 (几乎每个MC版本都有不同版本的协议版本号)"),
                (self.major_name, "大版本 (该服务器是属于哪个大版本的)"),
                (self.version_type, "服务器版本的类型")]
        for tip in tips:
            ToolTip(tip[0], tip[1], delay=2000)

    def pack_widgets(self):
        self.version_name_frame.pack()
        self.version_name_text.pack(side=LEFT)
        self.version_name_MOTD.configure(height=1, width=20)
        self.version_name_MOTD.pack(side=LEFT)
        self.minecraft_version.pack()
        self.protocol_version.pack()
        self.major_name.pack()
        self.version_type.pack()

    def load_data(self, data: ServerInfo):
        self.data = data

        self.version_name_text.configure(text="版本名：")
        temp_data = data
        if "§" in data.version_name:
            temp_data.description_json = DescriptionParser.format_chars_to_extras(temp_data.version_name)
        else:
            temp_data.description_json = [{"text": temp_data.version_name}]
        self.version_name_MOTD.load_motd(temp_data)
        self.minecraft_version.configure(text=f"正式版本名：{data.protocol_name}")
        self.protocol_version.configure(text=f"协议版本号：{data.protocol_version}")
        self.major_name.configure(text=f"大版本：{data.protocol_major_name}")

        if data.version_type == "release":
            self.version_type.configure(text="版本类型：正式版")
        elif data.version_type == "release":
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
        self.data = data

        if data.mod_pack_server:
            print("Mod Pack Server Info:", data.mod_pack_info)
        self.mod_list.delete(*self.mod_list.get_children())
        for mod in data.mod_list.items():
            self.mod_list.insert("", END, values=mod)

    def select_mod(self, event: Event):
        item_id = self.identify(event.x, event.y)
        if item_id == "border":
            return
        print("PASS ITEM:", item_id)
        name, version = self.mod_list.get_children(item_id)
        print("Mod Name:", name, "  ", "Version:", version)
