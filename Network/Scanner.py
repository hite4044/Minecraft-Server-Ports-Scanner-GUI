# -*- coding: UTF-8 -*-
from base64 import b64decode
from copy import deepcopy
from io import BytesIO
from queue import Queue, Empty
from threading import Thread, Lock
from time import sleep
from typing import List, Any

from PIL import Image, ImageTk
from Libs import Vars

class ServerScanner:
    def __init__(self):
        self.callback = None
        self.host = None
        self.thread_num = None
        self.timeout = None
        self.work_queue = Queue()
        self.in_scan = False
        self.callback_count = 0
        self.callback_count_lock = Lock()
        self.pause_lock = Lock()  # 暂停锁
        self.worker_count: int = 0  # 线程数
        self.working_worker: int = 0  # 工作中的线程数
        self.thread_num_lock = Lock()

    def config(self, timeout: float = 0.7, thread_num: int = 256, callback: object = lambda x: None):
        self.thread_num = thread_num
        self.timeout = timeout
        self.callback = callback

    def run(self, host: str, port_range: range):
        while not self.work_queue.empty():
            try:
                self.work_queue.get(block=False)
            except Empty:
                break
        self.in_scan = True
        self.add_task(host, port_range)

        for thread_id in range(self.thread_num):
            Thread(target=self.scan_worker, daemon=True, name=f"Worker-{thread_id}").start()
            sleep(self.timeout / self.thread_num)

    def add_task(self, host: str, port_range: range):
        for port in port_range:
            self.work_queue.put((host, port))

    def join(self):
        while self.worker_count > 0:
            sleep(0.1)

    def pause(self):
        self.pause_lock.acquire()

    def pause_and_wait(self):
        self.pause()
        while self.working_worker > 0:
            sleep(0.1)

    def resume(self):
        try:
            self.pause_lock.release()
        except RuntimeError:
            return

    def resume_and_wait(self):
        self.resume()
        while self.working_worker != self.thread_num:
            sleep(0.1)

    def stop(self):
        self.in_scan = False
        if self.pause_lock.locked():
            self.pause_lock.release()

    def stop_and_wait(self):
        self.stop()
        while self.worker_count > 0:
            sleep(0.1)

    def scan_a_port(self, host: str, port: int, callback: Any):
        raw_info = Port(host, port, self.timeout).get_server_info()
        if raw_info["status"] == "online":
            Thread(target=callback, args=(ServerInfo(raw_info["info"]),)).start()
            return
        Thread(target=self._callback, args=(raw_info, callback)).start()

    def _callback(self, raw_info, callback: Any):
        with self.callback_count_lock:
            self.callback_count += 1
        callback(raw_info)
        with self.callback_count_lock:
            self.callback_count -= 1

    def scan_worker(self):
        with self.thread_num_lock:
            self.worker_count += 1
            self.working_worker += 1
        while self.in_scan:
            try:
                host, port = self.work_queue.get(block=False)
                self.scan_a_port(host, port, self.callback)
            except Empty:
                break

            # 暂停机制
            if self.pause_lock.locked():
                with self.thread_num_lock:
                    self.working_worker -= 1
                while self.pause_lock.locked():
                    if not self.in_scan:
                        break
                    sleep(0.1)
                sleep(self.working_worker * 0.01)
                with self.thread_num_lock:
                    self.working_worker += 1
                if not self.in_scan:
                    break
        with self.thread_num_lock:
            self.worker_count -= 1
            self.working_worker -= 1
        if self.worker_count <= 0:
            Thread(target=self.check_callback_over_thread, daemon=True).start()

    def check_callback_over_thread(self):
        while self.callback_count > 0:
            sleep(0.05)
        sleep(0.2)
        self.in_scan = False


class Port:
    """获取服务器JSON数据"""

    def __init__(self, host: str = "", port: int = 25565, timeout: float = 0.7, protocol_version: int = 47):
        self.sock = None
        self.host = host
        self.port = port
        self.protocol = protocol_version
        self.timeout = timeout

    def get_server_info(self) -> dict:
        """
        获取服务器在`#Status_Response`包中的返回JSON
        https://wiki.vg/Server_List_Ping#Status_Response
        """
        from mcstatus.address import Address
        from mcstatus.pinger import ServerPinger
        from mcstatus.protocol.connection import TCPSocketConnection

        info = {"host": self.host, "port": self.port}
        try:
            with TCPSocketConnection((self.host, self.port), self.timeout) as connection:
                pinger = ServerPinger(connection, address=Address(self.host, self.port))
                pinger.handshake()
                info_data = pinger.read_status()
                ping_time = pinger.test_ping()

            # 处理JSON字节
            info["ping"] = round(ping_time, 2)
            info["details"] = info_data.raw
            return {"status": "online", "info": info}

        except TimeoutError:
            return {"status": "offline"}

        except IOError:
            return {"status": "offline"}

        except (ConnectionRefusedError, ConnectionResetError):
            return {"status": "error", "msg": "连接被重置", "info": info}

        except ConnectionAbortedError:
            return {"status": "error", "msg": "连接被中断", "info": info}

        except UnicodeDecodeError:
            return {"status": "error", "msg": "UTF-8解码错误", "info": info}


class ServerInfo:
    """
    用于解析MC服务器的JSON数据
    """

    def __init__(self, info: dict, load_favicon: bool = True) -> None:
        data = info["details"]
        self.parsed_data = data

        # 基本信息
        self.host = info["host"]
        self.port = info["port"]
        self.ping = info["ping"]

        # 服务器版本信息
        self.version_name = data.get("version", {"name": "未知"})["name"]
        self.protocol_version = data.get("version", {"protocol": "未知"})["protocol"]

        if self.protocol_version == -1:
            self.protocol_info = {}
        else:
            for ver in Vars.protocol_map:
                if ver["version"] == self.protocol_version:
                    self.protocol_info: dict = ver
                    break
            else:
                self.protocol_info = {}

        self.protocol_name = self.protocol_info.get("minecraftVersion", "未知")
        self.protocol_major_name = self.protocol_info.get("majorVersion", "未知")

        self.version_type = "unknown"
        if self.protocol_info.get("releaseType"):
            self.version_type = self.protocol_info["releaseType"]
        elif "w" in self.protocol_name:
            self.version_type = "snapshot"
        elif "." in self.protocol_name:
            self.version_type = "release"

        # 服务器玩家信息
        self.player_max = data.get("players", {"max": "未知"})["max"]
        self.player_online = data.get("players", {"online": "未知"})["online"]
        if data.get("players", {}).get("sample"):
            self.players = data["players"]["sample"]
            for _ in range(len(self.players)):
                player = self.players.pop(0)
                if player["name"] == "Anonymous Player":
                    player["name"] = "匿名玩家"
                self.players.append(player)
        else:
            self.players = []

        # 服务器图标信息
        self.favicon_data = data.get("favicon")
        self.favicon_photo = self.favicon = None
        self.has_favicon = bool(self.favicon_data)
        if self.has_favicon:
            self.favicon_data = b64decode(self.favicon_data.replace("data:image/png;base64,", ""))
            if load_favicon:
                self.load_favicon_photo()

        # 服务器标题
        try:
            self.description_json = DescriptionParser.parse(data["description"])
        except KeyError:
            self.description_json = [{"text": "A Minecraft Server"}]

        # 服务器模组
        self.mod_server: bool = bool(data.get("modinfo")) or bool(data.get("forgeData"))
        self.mod_list: dict[str, str] = {}
        if self.mod_server:
            if data.get("modinfo"):  # 1.16.5 Forge+
                for mod in data["modinfo"]["modList"]:
                    if "OHNOES" in mod["version"]:
                        mod["version"] = "未知"
                    self.mod_list[mod["modid"]] = mod["version"]
            elif data.get("forgeData"):  # 1.12.2 Forge~
                for mod in data["forgeData"]["mods"]:
                    if "OHNOES" in mod["modmarker"]:
                        mod["version"] = "未知"
                    self.mod_list[mod["modId"]] = mod["modmarker"]

        # 服务器整合包
        self.mod_pack_server: bool = bool(data.get("modpackData"))
        self.mod_pack_info = {}
        if self.mod_pack_server:
            self.mod_pack_info = data["modpackData"]

        # 杂项
        self.enforcesSecureChat = data.get("enforcesSecureChat", False)  # 强制安全聊天
        self.preventsChatReports = data.get("preventsChatReports", False)  # 阻止聊天举报
        self.online_server: bool = bool(self.enforcesSecureChat)  # 离线服务器

    def __call__(self) -> dict:
        return self.parsed_data

    def __str__(self) -> str:
        return self.text

    def load_favicon_photo(self):
        if self.has_favicon:
            self.favicon = Image.open(BytesIO(self.favicon_data), formats=["PNG"])
            self.favicon_photo = ImageTk.PhotoImage(self.favicon)

    @property
    def text(self) -> str:
        text = ""
        for extra in self.description_json:
            text += extra["text"]
        return text


class DescriptionParser:
    """描述解析器"""

    @staticmethod
    def format_chars_to_extras(text: str) -> List[dict]:
        """格式化文本"""
        extras = []
        for extra in text.split("§"):
            if len(extra) >= 2:
                state = {"text": extra[1:]}
                fmt_code = extra[0]
                if fmt_code == "l":  # 粗体
                    state["bold"] = True
                elif fmt_code == "m":  # 斜体
                    state["italic"] = True
                elif fmt_code == "n":  # 下划线
                    state["underline"] = True
                elif fmt_code == "o":  # 删除线
                    state["strikethrough"] = True
                elif fmt_code == "k":  # 混淆处理(乱码)
                    state["obfuscated"] = True
                elif fmt_code == "r":  # 重置样式
                    pass
                elif fmt_code in Vars.color_map.keys():  # 颜色
                    state["color"] = Vars.color_map[fmt_code]
                extras.append(state)
            else:
                pass
        return extras

    @staticmethod
    def parse(description: Any) -> List[dict]:
        """解析描述"""
        if isinstance(description, str):
            if "§" in description:
                return DescriptionParser.format_chars_to_extras(description)
            return [{"text": description}]
        elif isinstance(description, list):
            extras = []
            for extra in description:
                extras.extend(DescriptionParser.parse(extra))
            return extras
        elif isinstance(description, dict):
            if "translate" in description:
                return DescriptionParser.parse(description["translate"])

            extras = []
            if "extra" in description:
                extras.extend(DescriptionParser.parse(description["extra"]))
            if "text" in description:
                sub_extras = deepcopy(description)
                if "extra" in sub_extras:
                    sub_extras.pop("extra")
                if "§" in sub_extras["text"]:
                    extras.extend(DescriptionParser.format_chars_to_extras(sub_extras["text"]))
                else:
                    extras.append(sub_extras)
            return extras
