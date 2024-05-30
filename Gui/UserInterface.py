# -*- coding: UTF-8 -*-
from sys import stderr
from time import perf_counter

from Gui.ScanBarGui import ScanBar
from Gui.ServerListGui import ServerList
from Gui.SettingsFrame import SettingsFrame
from Gui.Widgets import *
from Libs.Vars import *


def set_default_font():
    font.nametofont("TkDefaultFont").config(family="微软雅黑", size=10)


def load_unifont():
    from pyglet.font import add_file

    if not exists("assets/Unifont.otf"):  # 若字体文件不存在则退出
        print("Unifont字体文件丢失", file=stderr)
        return

    add_file("assets/Unifont.otf")


class Title(Label):
    def __init__(self, master: Misc):
        super(Title, self).__init__(master)
        self.configure(text="Minecraft服务器扫描器")
        self.configure(font=("微软雅黑", 24))


class TitleBar(Frame):
    def __init__(self, master: Misc):
        super(TitleBar, self).__init__(master)
        self.title_text = Title(self)
        self.theme_selector = ThemesSelector(self)
        self.title_text.pack(side=LEFT, padx=5, pady=5)
        self.theme_selector.pack(side=RIGHT, padx=5, pady=5)


class GUI(Window):
    def __init__(self):
        super(GUI, self).__init__()

        timer = perf_counter()

        set_default_font()
        self.config_root_window()

        self.title_bar = TitleBar(self)
        self.sep = Separator()
        self.tabs = Tabs(self)
        self.logger = Logger(self.tabs)
        self.server_scanF = Frame(self.tabs)
        self.settings = SettingsFrame(self.tabs)
        self.servers = ServerList(self.server_scanF, self.logger)
        self.scan_bar = ScanBar(self.server_scanF, self.logger, self.servers, self)

        self.pack_widgets()
        print(f"GUI构建时间: {perf_counter() - timer:.3f}秒")
        Thread(target=load_unifont).start()  # 加载字体

    def config_root_window(self):  # 设置窗体
        self.wm_title("MC服务器扫描器")  # 设置标题
        Style().theme_use(user_settings_loader.configs['theme_name'])
        self.protocol("WM_DELETE_WINDOW", self.on_delete_window)
        Thread(target=self.set_icon).start()
        Thread(target=self.place_window_center).start()

    def set_icon(self):
        if exists("assets/icon.ico"):
            self.wm_iconbitmap("assets/icon.ico")
        else:
            print("图标文件丢失", file=stderr)

    def on_delete_window(self):
        # user_settings_loader.configs['theme_name'] = Style().theme_use()
        self.scan_bar.close_save_config()
        UserSettingsSaver.save_user_configs(user_settings_loader)
        self.destroy()

    def pack_widgets(self):
        self.title_bar.pack(fill=X, padx=10)
        self.sep.pack(fill=X, padx=10, pady=3)
        self.tabs.pack(fill=BOTH, expand=True, pady=0)
        self.servers.pack(fill=BOTH, expand=True, padx=3, pady=3)
        self.scan_bar.pack(side=BOTTOM, fill=X, padx=3, pady=3)
        self.tabs.add(self.server_scanF, text="控制面板")
        self.tabs.add(self.logger, text="日志")
        self.tabs.add(self.settings, text="设置")
