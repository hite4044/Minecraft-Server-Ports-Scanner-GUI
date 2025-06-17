# -*- coding: UTF-8 -*-
from json import load as json_load, dump as json_dump
from sys import stderr
from time import perf_counter

from comtypes import CoInitialize, CoUninitialize
from ping3 import ping
from win32con import MB_ICONERROR, MB_OK, MB_YESNO, MB_ICONWARNING, IDYES
from win32gui import GetParent, GetWindowText, GetClassName, MessageBox

from Gui.PortsRangeGui import PortsHotView
from Gui.ServerListGui import ServerList
from Libs.TaskbarLib import *
from Gui.Widgets import *


class ScanBar(LabelFrame):
    def __init__(self, master: Misc, logger: Logger, server_list: ServerList, hot_view: PortsHotView, gui):
        super(ScanBar, self).__init__(master, text="扫描")
        self.logger = logger
        self.server_list = server_list
        import Gui.UserInterface
        self.gui: Gui.UserInterface = gui

        self.in_scan = False
        self.scan_obj = ServerScanner()
        self.hot_view = hot_view
        self.callback_lock = Lock()
        self.progress_var = 0
        self.callback_workers = 0
        self.taskbar = None
        self.config_path = path_join(config_dir, "scan_config.json")
        self.user_address_operator = UserAddressOperator()
        Thread(target=self.taskbar_create, daemon=True).start()

        # 进度条
        self.progress_bar = InfoProgressBar(self, interval=0.05, text="扫描进度: ")
        self.progress_bar.pack(side=BOTTOM, fill=X, expand=True, padx=5, pady=5)

        # 分割线2
        self.sep2 = Separator(self)
        self.sep2.pack(side=BOTTOM, fill=X, padx=5)

        # 输入 Frame
        self.input_frame = Frame(self)
        self.host_input = TextCombobox(self.input_frame, "域名: ", server_addresses)
        self.timeout_input = EntryScaleFloatFrame(self.input_frame, 0.1, 3.0, 0.2, "超时时间: ")
        self.thread_num_input = EntryScaleIntFrame(self.input_frame, 1,
                                                   Vars.user_settings_loader.configs["max_thread_number"],
                                                   1,
                                                   "线程数: ")
        self.range_input = RangeSelector(self.input_frame, "端口选择: ", 1024, 65535)

        self.input_frame.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        self.host_input.pack(fill=X, expand=True)
        self.timeout_input.pack(fill=X, expand=True)
        self.thread_num_input.pack(fill=X, expand=True)
        self.range_input.pack(fill=X, expand=True)

        # 分割线
        self.sep = Separator(self, orient="vertical")
        self.sep.pack(side=LEFT, fill=Y)

        # 扫描控制 Frame
        self.buttons = Frame(self)
        self.start_button = Button(self.buttons, text="开始扫描", command=self.start_scan, state=DISABLED)
        self.pause_button = PauseButton(self.buttons, self.resume_scan, self.pause_scan, state=DISABLED)
        self.stop_button = Button(self.buttons, text="停止", command=self.stop_scan, state=DISABLED)

        self.buttons.pack(side=RIGHT, padx=5)
        self.start_button.pack(fill=X, expand=True, pady=2)
        self.pause_button.pack(fill=X, expand=True, pady=2)
        self.stop_button.pack(fill=X, expand=True, pady=2)

        self.load_user_config()

    def close_save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json_dump(self.get_config(), f, ensure_ascii=False, indent=4)
        except OSError:
            print("main_gui.close_save_config: Failed to save config!", file=stderr)

    def load_user_config(self):
        if exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as f:
                config = json_load(f)
                self.set_config(config)

    def get_config(self) -> dict:
        return {
            "host": self.host_input.get(),
            "timeout": self.timeout_input.get_value(),
            "thread_num": self.thread_num_input.get_value(),
            "range": self.range_input.get()
        }

    def set_config(self, config: dict):
        self.host_input.set(config["host"])
        self.timeout_input.set_value(config["timeout"])
        self.thread_num_input.set_value(config["thread_num"])
        self.range_input.set(*config["range"])

    def taskbar_create(self):
        CoInitialize()
        timeout = 2.0
        timer = perf_counter()
        main_window = 0  # 默认值为0会使TaskbarApi可调用但无效
        while perf_counter() - timer < timeout:
            root_hwnd = GetParent(self.master.master.master.winfo_id())
            if GetWindowText(root_hwnd) == "MC服务器扫描器" and GetClassName(root_hwnd) == "TkTopLevel":
                main_window = root_hwnd
                break
        else:
            print("main_gui.taskbar_create: Main Window Not Found!", file=stderr)
        if main_window != 0:
            print(f"Done! Found main window, use: {round((perf_counter() - timer) * 1000, 2)} ms, hWnd: {main_window}")
        self.taskbar = TaskbarApi(main_window)
        self.start_button.configure(state=NORMAL)
        CoUninitialize()

    def callback(self, info: Any):
        with self.callback_lock:
            self.progress_var += 1
            self.progress_bar.update_progress(self.progress_var)
            self.taskbar.set_progress_value(int(self.progress_var / self.progress_bar.max_ * 100), 100)
            if isinstance(info, ServerInfo):
                self.hot_view.callback(info.port)
                self.server_list.add_server(info)
                self.logger.log(INFO, f"[{info.port}]:", "检测到MC服务器")
            elif isinstance(info, dict):
                if info["status"] != "offline":
                    self.logger.log(info["status"], f"[{info['info']['port']}]:", info["msg"])

    def start_scan(self):  # 20500 - 25000
        self.logger.log(INFO, "开始扫描")
        self.close_save_config()
        if self.in_scan:
            return

        host = self.host_input.get()
        thread_num = self.thread_num_input.get_value()
        timeout = self.timeout_input.get_value()
        start, stop = self.range_input.get()

        self.gui.servers.empty_tip.configure(text="检验连通性...")
        self.gui.update()
        if user_settings_loader.configs['ping_before_scan'] and not self.check_host(host):
            self.gui.servers.empty_tip.configure(text="没有服务器")
            return
        self.gui.servers.empty_tip.configure(text="没有服务器")

        self.in_scan = True
        self.start_button.configure(state=DISABLED)
        self.pause_button.configure(state=NORMAL)
        self.stop_button.configure(state=NORMAL)

        self.progress_var = 0
        self.progress_bar.reset(stop - start)
        self.hot_view.reset_view()
        self.scan_obj.config(timeout, thread_num, self.callback)
        Thread(target=self.scan_obj.run, args=(host, range(start, stop))).start()
        Thread(target=self.check_over_thread, daemon=True).start()
        self.taskbar.set_progress_state(TBPFLAG.TBPF_NORMAL)

        # 写入配置文件，使得下一次自动加载
        self.logger.log(INFO, f"将地址 [{host}] 写入配置文件。")
        write_result = self.user_address_operator.write_address_to_config_file(address=host)
        if write_result is False:
            self.logger.log(ERROR, f"写入地址 [{host}] 时，文件操作时发生错误！")
            MessageBox(self.winfo_id(),
                       f"对：{UserAddressOperator.user_address_json} 文件操作时发生错误！",
                       "文件操作错误",
                       MB_OK | MB_ICONERROR)

    def pause_scan(self):
        def task():
            sleep(0.1)
            self.pause_button.configure(state=DISABLED)
            self.scan_obj.pause()
            self.logger.log(DEBUG, "暂停扫描")
            while self.scan_obj.working_worker > 0:
                self.logger.log(INFO, "等待所有线程暂停工作, 工作中线程数量:", self.scan_obj.working_worker)
                sleep(0.1)
            self.pause_button.configure(state=NORMAL)

        Thread(target=task, daemon=True).start()
        self.hot_view.draw("使得能够更新画面")
        self.taskbar.set_progress_state(TBPFLAG.TBPF_PAUSED)

    def resume_scan(self):
        def task():
            self.pause_button.configure(state=DISABLED)
            self.logger.log(DEBUG, "恢复扫描")
            self.scan_obj.resume()
            while self.scan_obj.working_worker != self.scan_obj.thread_num:
                self.logger.log(DEBUG, "等待所有线程开始工作, 工作中线程数量:", self.scan_obj.working_worker)
                sleep(0.1)
            self.pause_button.configure(state=NORMAL)

        Thread(target=task, daemon=True).start()
        self.taskbar.set_progress_state(TBPFLAG.TBPF_NORMAL)

    def stop_scan(self):
        if not self.in_scan:
            return
        self.in_scan = False
        self.pause_button.configure(state=DISABLED)
        self.stop_button.configure(state=DISABLED)

        def stop_task():
            self.in_scan = False
            self.logger.log(DEBUG, "停止扫描")
            self.taskbar.set_progress_state(TBPFLAG.TBPF_ERROR)
            self.scan_obj.stop()
            while self.scan_obj.worker_count > 0 or self.scan_obj.callback_count > 0:
                sleep(0.1)
                if self.scan_obj.worker_count > 0:
                    self.logger.log(DEBUG, "等待工作线程全部结束, 剩余数量:", self.scan_obj.worker_count)
                elif self.scan_obj.callback_count > 0:
                    self.logger.log(DEBUG, "等待回调函数全部结束, 剩余数量:", self.scan_obj.callback_count)
            self.logger.log(DEBUG, "工作线程已全部结束")
            self.start_button.configure(state=NORMAL)
            self.taskbar.set_progress_state(TBPFLAG.TBPF_NOPROGRESS)
            self.progress_stop()

        Thread(target=stop_task).start()
        self.hot_view.draw("使得能够更新画面")
        self.taskbar.set_progress_state(TBPFLAG.TBPF_INDETERMINATE)

    def check_over_thread(self):
        self.logger.log(DEBUG, "检测扫描结束线程启动...")
        if not self.in_scan:
            return

        while not self.scan_obj.in_scan:
            sleep(0.05)

        while self.scan_obj.in_scan:
            sleep(0.05)

        self.logger.log(DEBUG, "检测到扫描已结束")
        self.hot_view.draw("使得能够更新画面")
        if self.in_scan:
            self.in_scan = False
            self.stop_button.configure(state=DISABLED)
            self.pause_button.configure(state=DISABLED)
            self.start_button.configure(state=NORMAL)
            self.progress_stop()
            self.progress_bar.update_progress(self.progress_bar.max_)  # 掩耳盗铃一波
            self.taskbar.flash_window()
            self.taskbar.set_progress_state(TBPFLAG.TBPF_NOPROGRESS)

    def progress_stop(self):
        self.progress_bar.update_now(self.progress_var)

    def check_host(self, host: str) -> bool:
        self.logger.log(DEBUG, f"检测域名 [{host}] ...")
        self.logger.log(DEBUG, "樱花穿透域名检测...")
        if host.startswith("frp-") and host.endswith(".top"):
            self.logger.log(WARNING, f"疑似检测到Sakura Frp域名 ({host})")
            ret = MessageBox(self.winfo_id(),
                             f"域名 [{host}] 疑似为Sakura Frp域名, 扫描会封禁你的IP, 请问是否继续?",
                             "域名警告",
                             MB_YESNO | MB_ICONWARNING)
            if ret != IDYES:
                return False

        self.logger.log(DEBUG, "开始ping测试...")
        delay = ping(host)
        if isinstance(delay, float) and float != 0.0:
            self.logger.log(INFO, f"域名存活, 延迟: {round(delay * 1000, 2)} ms")
            return True
        else:
            self.logger.log(ERROR, "域名无法连接")
            MessageBox(self.winfo_id(),
                       f"域名 [{host}] ping测试不通过",
                       "域名错误",
                       MB_OK | MB_ICONERROR)
            return False
