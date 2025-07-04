# -*- coding: UTF-8 -*-
from sys import stderr
from time import perf_counter

load_timer = perf_counter()

from Gui.ScanBarGui import ScanBar
from Gui.ServerListGui import ServerList
from Gui.SettingsFrame import SettingsFrame
from Gui.PortsRangeGui import PortsHotView
from Gui.Widgets import *
from Libs.Vars import *

print(f"库加载时间: {perf_counter() - load_timer:.3f}秒")


def set_default_font():
    font.nametofont("TkDefaultFont").config(family=Vars.config.global_font, size=10)


class Title(Label):
    def __init__(self, master: Misc):
        super(Title, self).__init__(master,
                                    text="Minecraft服务器扫描器",
                                    font=(Vars.config.global_font, 24))


class TitleBar(Frame):
    def __init__(self, master: Misc):
        super(TitleBar, self).__init__(master)
        self.title_text = Title(self)
        self.theme_selector = ThemesSelector(self)
        self.title_text.pack(side=LEFT, padx=5, pady=5)
        self.theme_selector.pack(side=RIGHT, padx=5, pady=5)


class GUI(Window):
    def __init__(self):
        super(GUI, self).__init__(themename=config.theme_name)

        set_default_font()
        self.config_root_window()

        self.title_bar = TitleBar(self)
        self.sep = Separator()
        self.tabs = Tabs(self)
        self.logger = Logger(self.tabs)
        self.server_scanF = Frame(self.tabs)
        self.hot_view = PortsHotView(self.tabs)
        self.settings = SettingsFrame(self.tabs)
        self.servers = ServerList(self.server_scanF, self.logger)
        self.scan_bar = ScanBar(self.server_scanF, self.logger, self.servers, self.hot_view, self)

        self.pack_widgets()

    def config_root_window(self):  # 设置窗体
        self.wm_title("MC服务器扫描器")  # 设置标题
        self.protocol("WM_DELETE_WINDOW", self.on_delete_window)
        self.wm_resizable(config.configs["allow_hor_resize"], True)
        Sty.set_obj(self._style)
        Thread(target=self.set_icon).start()
        #Thread(target=self.place_window_center).start()

    def set_icon(self):
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("product")
        if exists("assets/icon.ico"):
            self._icon.icon = ImageTk.PhotoImage(file="assets/icon.ico")
            self.after(30, lambda: self.iconphoto(True, self._icon.icon))
        else:
            print("图标文件丢失", file=stderr)

    def on_delete_window(self):
        self.scan_bar.close_save_config()
        UserSettingsSaver.save_user_configs(config)
        self.destroy()

    def pack_widgets(self):
        self.title_bar.pack(fill=X, padx=10)
        self.sep.pack(fill=X, padx=10, pady=3)
        self.tabs.pack(fill=BOTH, expand=True, pady=0)
        self.servers.pack(fill=BOTH, expand=True, padx=3, pady=3)
        self.scan_bar.pack(side=BOTTOM, fill=X, padx=3, pady=3)
        self.tabs.add(self.server_scanF, text="控制面板")
        self.tabs.add(self.logger, text="日志")
        self.tabs.add(self.hot_view, text="端口热图")
        self.tabs.add(self.settings, text="设置")
