from ttkbootstrap.scrolled import ScrolledFrame

from Gui.Widgets import *
from Libs.Vars import user_settings_loader


class SettingsFrame(Frame):
    def __init__(self, master: Misc):
        super().__init__(master)

        self.language_support = {
            "if_version_name_shown_as_label": "将 VersionName 显示为纯文本格式",
            "theme_name": "主题 ( 不建议在此处修改 )",
            "ping_before_scan": "扫描之前先检测连通性",
            "use_legacy_font": "使用原先的旧版字体 ( 任何渲染问题开发者没有义务修复 )",
            "font": "字体"
        }

        self.bool_configs = {i: user_settings_loader.configs[i] for i in user_settings_loader.configs if
                             type(user_settings_loader.configs[i]) is bool}
        self.button_frame = ScrolledFrame(self)
        self.boolean_settings_vars: List[BooleanVar] = []
        self.boolean_settings_ratio_buttons: List[Checkbutton] = []
        for i in self.bool_configs:
            boolean_var = BooleanVar(name=i)
            boolean_var.set(user_settings_loader.configs[i])
            self.boolean_settings_vars.append(boolean_var)
            self.boolean_settings_ratio_buttons.append(
                Checkbutton(self.button_frame, name=i, text=self.language_support.get(i, i),  # 若无汉化则使用其原本的名字
                            variable=boolean_var,
                            onvalue=True,
                            offvalue=False))
        self.string_configs = {i: user_settings_loader.configs[i] for i in user_settings_loader.configs if
                               type(user_settings_loader.configs[i]) is str}
        self.string_settings_vars: List[StringVar] = []
        self.string_settings_label: List[Label] = []
        self.string_settings_entry: List[Entry] = []
        for i in self.string_configs:
            string_var = StringVar(name=i)
            string_var.set(user_settings_loader.configs[i])
            self.string_settings_vars.append(string_var)
            self.string_settings_label.append(
                Label(self.button_frame, text=self.language_support.get(i, i))
            )
            self.string_settings_entry.append(
                Entry(self.button_frame, textvariable=string_var)
            )
        self.confirm_button = Button(self, text="保存更改", command=self.confirm)
        self.update_button = Button(self, text="更新", command=self.update_settings)

        self.pack_widgets()

    def pack_widgets(self):
        row: int = 0
        self.button_frame.pack(side=TOP, anchor=NW, fill=X)
        for i in range(len(self.boolean_settings_ratio_buttons)):
            self.boolean_settings_ratio_buttons[i].grid(column=0, row=row, sticky=W)
            row += 1
        for i in range(len(self.string_settings_entry)):
            self.string_settings_entry[i].grid(column=1, row=row, sticky=W)
            self.string_settings_label[i].grid(column=0, row=row, sticky=W)
            row += 1
        self.confirm_button.pack(anchor=SE, side=RIGHT)
        self.update_button.pack(anchor=SE, side=RIGHT)

    def confirm(self):
        for i in self.boolean_settings_vars:
            user_settings_loader.configs[i._name] = i.get()  # 貌似只能这么解决, _name 在 BooleanVar 里是 protected
        for i in self.string_settings_vars:
            user_settings_loader.configs[i._name] = i.get()

    def update_settings(self):
        self.boolean_settings_vars = []
        self.string_settings_vars = []
        for i in self.bool_configs:
            boolean_var = BooleanVar(name=i)
            boolean_var.set(user_settings_loader.configs[i])
            self.boolean_settings_vars.append(boolean_var)
        for i in self.string_configs:
            string_var = StringVar(name=i)
            string_var.set(user_settings_loader.configs[i])
            self.string_settings_vars.append(string_var)
