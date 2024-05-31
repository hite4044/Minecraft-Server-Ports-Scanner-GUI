import sys

from ttkbootstrap.scrolled import ScrolledFrame

from Gui.Widgets import *
from Libs.Vars import user_settings_loader


class SettingFrame(Frame):
    def __init__(self, master: Misc, text: str, name: str, value: Any):
        super().__init__(master)
        self.name = name
        self.label = Label(self, text=text)
        if isinstance(value, bool):
            self.variable = BooleanVar(self, value=value, name=name)
            self.widget = Checkbutton(self, variable=self.variable, onvalue=True, offvalue=False)
        elif isinstance(value, str):
            self.variable = StringVar(self, value=value, name=name)
            self.widget = Entry(self, textvariable=self.variable)
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
            "use_legacy_font": "使用原先的旧版字体 ( 任何渲染问题开发者没有义务修复 )",
            "font": "字体",
            "max_thread_number": "扫描时允许的最大线程数"
        }

        self.config_frame = ScrolledFrame(self)
        self.configs = {}
        for name, value in user_settings_loader.configs.items():
            self.configs[name] = SettingFrame(self.config_frame, self.language_support[name], name, value)

        self.confirm_button = Button(self, text="保存更改", command=self.confirm)
        self.update_button = Button(self, text="更新", command=self.update_settings)

        self.pack_widgets()

    def pack_widgets(self):
        self.config_frame.pack(fill=BOTH, expand=True)
        row = 0
        for sitting_frame in self.configs.values():
            sitting_frame.grid(row=row, column=0, sticky=W)
            row += 1
        for i in range(len(self.int_settings_spinbox)):
            self.int_settings_spinbox[i].grid(column=1, row=row, sticky=W)
            self.int_settings_label[i].grid(column=0, row=row, sticky=W)
            row += 1
        self.confirm_button.pack(anchor=SE, side=RIGHT)
        self.update_button.pack(anchor=SE, side=RIGHT, padx=5)

    def confirm(self):
        for name, widget in self.configs.items():
            user_settings_loader.configs[name] = widget.get()

    def update_settings(self):
        for name, widget in self.configs.items():
            widget.set(user_settings_loader.configs[name])
