import sys

from ttkbootstrap.scrolled import ScrolledFrame
from Gui.Widgets import *


class SettingFrame(Frame):
    def __init__(self, master: Misc, text: str, name: str, value: Any, use_sizer: bool = True):
        if use_sizer:
            super().__init__(master)
            parent = self
        else:
            parent = master
        self.name = name
        self.label = Label(parent, text=text)
        if isinstance(value, bool):
            self.variable = BooleanVar(parent, value=value, name=name)
            self.widget = Checkbutton(parent, variable=self.variable, onvalue=True, offvalue=False)
        elif isinstance(value, str):
            self.variable = StringVar(parent, value=value, name=name)
            self.widget = Entry(parent, textvariable=self.variable)
        elif isinstance(value, int):
            self.variable = IntVar(parent, value=value, name=name)
            self.widget = Spinbox(parent, textvariable=self.variable, to=sys.maxsize)
        if use_sizer:
            self.label.pack(side=LEFT)
            self.widget.pack(side=LEFT, padx=5)

    def get(self):
        return self.variable.get()

    def set(self, value: Any):
        self.variable.set(value)


class SettingsFrame(Frame):
    def __init__(self, master: Misc):
        super().__init__(master)

        self.language_support = {
            "if_version_name_shown_as_label": "将 VersionName 显示为纯文本格式",
            "theme_name": "主题 ( 不建议在此处修改 )",
            "ping_before_scan": "扫描之前先检测连通性",
            "global_font": "字体",
            "max_thread_number": "扫描时允许的最大线程数",
            "MOTD_use_unicode_font": "MOTD全部使用Unifont字体显示",
            "players_all": "服务器玩家累积并去重",
            "allow_hor_resize": "允许水平调整窗口 ( 很卡 )",
            "use_proxy": "使用代理",
            "proxy_kind": "代理类型 (sock5, sock4)",
            "proxy_host": "代理服务器的地址",
            "proxy_port": "代理服务器的端口"
        }

        self.config_frame = ScrolledFrame(self)
        self.configs = {}
        for name, value in user_settings_loader.configs.items():
            self.configs[name] = SettingFrame(self.config_frame, self.language_support.get(name, name + ' ( 不生效 ) '),
                                              name, value, use_sizer=False)

        self.confirm_button = Button(self, text="保存更改", command=self.confirm)
        self.update_button = Button(self, text="更新", command=self.update_settings)

        self.pack_widgets()

    def pack_widgets(self):
        self.config_frame.pack(fill=BOTH, expand=True)
        row = 0
        for sitting_frame in self.configs.values():
            sitting_frame.label.grid(row=row, column=0, sticky=W)
            sitting_frame.widget.grid(row=row, column=1, sticky=W, pady=2)
            row += 1
        self.confirm_button.pack(anchor=SE, side=RIGHT)
        self.update_button.pack(anchor=SE, side=RIGHT, padx=5)

    def confirm(self):
        for name, widget in self.configs.items():
            user_settings_loader.configs[name] = widget.get()

    def update_settings(self):
        for name, widget in self.configs.items():
            widget.set(user_settings_loader.configs[name])
