import vars
import socket
import varint
from io import BytesIO
from struct import pack
from copy import deepcopy
from typing import List, Any
from time import time, sleep
from base64 import b64decode
from PIL import Image, ImageTk
from queue import Queue, Empty
from threading import Thread, Lock
from json import loads as json_loads
from json.decoder import JSONDecodeError
from func_timeout import func_set_timeout


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

    def config(self, host: str, timeout: float = 0.7, thread_num: int = 256):
        self.thread_num = thread_num
        self.timeout = timeout
        self.host = host

    def run(self, port_range: range, callback: object):
        self.in_scan = True
        self.callback = callback
        for port in port_range:
            self.work_queue.put(port)

        for thread_id in range(self.thread_num):
            Thread(target=self.scan_worker, daemon=True, name=f"Worker-{thread_id}").start()
            sleep(self.timeout / self.thread_num)

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
        self.pause_lock.release()

    def resume_and_wait(self):
        self.resume()
        while self.working_worker != self.thread_num:
            sleep(0.1)

    def stop(self):
        if self.pause_lock.locked():
            self.pause_lock.release()
        self.in_scan = False

    def stop_and_wait(self):
        self.stop()
        while self.worker_count > 0:
            sleep(0.1)

    def scan_a_port(self, port: int, callback: Any):
        raw_info = Port(self.host, port, self.timeout).get_server_info()
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
                port = self.work_queue.get(block=False)
                self.scan_a_port(port, self.callback)
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
        self.in_scan = False


class Port:
    """获取服务器JSON数据"""

    def __init__(self, host: str = "", port: int = 25565, timeout: float = 0.7, protocol_version: int = 47):
        self.sock = None
        self.host = host
        self.port = port
        self.protocol = protocol_version
        self.timeout = timeout
        self.HANDSHAKE_PACKET = self.make_handshaking_packet()
        self.STATE_PACKET = self.make_state_packet()
        self.PING_PACKET = self.make_ping_packet()

    def get_server_info(self) -> dict:
        """
        获取服务器在`#Status_Response`包中的返回JSON
        https://wiki.vg/Server_List_Ping#Status_Response
        """
        try:
            self.sock = socket.socket(family=socket.AF_INET)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
        except (TimeoutError, socket.timeout):
            return {"status": "offline"}

        info = {"host": self.host, "port": self.port}
        try:
            # 获取服务端信息
            self.send_packet(self.HANDSHAKE_PACKET)
            self.send_packet(self.STATE_PACKET)
            info_data = self.receive_packet()

            # 获取服务器延迟
            ping_timer = time()
            self.send_packet(self.PING_PACKET)
            self.check_receive()
            ping_time = time() - ping_timer
            self.sock.close()

            # 处理JSON字节
            info["ping"] = round(ping_time * 1000, 2)
            info["details"] = Port.get_packet_json(info_data)
            return {"status": "online", "info": info}

        except TimeoutError:
            return {"status": "error", "msg": "建立连接后连接超时", "info": info}

        except EOFError:
            return {"status": "error", "msg": "未接收到足够数据", "info": info}

        except (ConnectionRefusedError, ConnectionResetError):
            return {"status": "error", "msg": "连接被重置", "info": info}

        except ConnectionAbortedError:
            return {"status": "error", "msg": "连接被中断", "info": info}

        except JSONDecodeError:
            return {"status": "error", "msg": "JSON解析错误", "info": info}

        except UnicodeDecodeError:
            return {"status": "error", "msg": "UTF-8解码错误", "info": info}

    def send_packet(self, packet_data: bytes) -> None:
        """给一个socket对象发点什么"""
        self.sock.sendall(packet_data)

    @func_set_timeout(3)
    def receive_packet(self) -> bytes:
        """
        接收一个遵循`Minecraft协议`的数据包
        https://wiki.vg/Protocol:zh-cn#.E6.97.A0.E5.8E.8B.E7.BC.A9
        :return:
        """
        head_data = self.sock.recv(8)
        if len(head_data) != 8:
            raise EOFError
        head_data = BytesIO(head_data)
        length = varint.decode_stream(head_data)

        packet_data = head_data.read()
        while len(packet_data) < length:
            more = self.sock.recv(length - len(packet_data))
            if not more:
                raise EOFError
            packet_data += more
        return packet_data

    def check_receive(self) -> None:
        """只是检查一下服务器有没有返回数据"""
        self.sock.recv(1)

    def make_handshaking_packet(self) -> bytes:
        """
        制作一个符合`Minecraft协议`的握手包
        https://wiki.vg/Server_List_Ping#Handshake

        协议版本  	VarInt	        MC的协议版本 (推荐 47)
        服务器地址	String	        域名或是IP, 例如： localhost 或是 127.0.0.1
        服务器端口	Unsigned Short	默认值为25565
        下一阶段 	VarInt	        0x01为状态, 0x02为登录
        """
        return Port.make_packet(0x00,
                                varint.encode(self.protocol),
                                pack(">p", self.host.encode("utf-8")),
                                pack(">H", self.port),
                                varint.encode(0x01))

    @staticmethod
    def get_packet_json(data: bytes) -> dict:
        """
        将一个遵循`Minecraft协议`的数据包分离出JSON数据
        https://wiki.vg/Protocol:zh-cn#.E6.97.A0.E5.8E.8B.E7.BC.A9

        :return:
        """

        try:
            data = data[data.index(b'{"'):]
        except (ValueError, IndexError):
            raise JSONDecodeError("没有找到JSON数据", "", 0)
        data = data.decode("utf-8")
        return json_loads(data)

    @staticmethod
    def make_ping_packet() -> bytes:
        """
        制作一个符合`Minecraft协议`的ping包
        https://wiki.vg/Server_List_Ping#Ping_Request
        :return: bytes
        """
        return Port.make_packet(0x01, pack(">q", int(time() * 1000)))

    @staticmethod
    def make_state_packet() -> bytes:
        """
        制作一个符合`Minecraft协议`的请求状态包
        https://wiki.vg/Server_List_Ping#Status_Request
        :return: bytes
        """
        return Port.make_packet(0x00)

    @staticmethod
    def make_packet(packet_id: int, *datas: bytes) -> bytes:
        """
        制作一个符合Minecraft协议的数据包
        https://wiki.vg/Protocol:zh-cn#.E6.97.A0.E5.8E.8B.E7.BC.A9

        名称   类型           注释
        长度   VarInt        数据长度+包编号长度
        包序号 VarInt        一般从0x00到0xFF
        数据   Bytes Array
        :return: bytes
        """
        id_varint = varint.encode(packet_id)
        if len(datas) != 0:
            data = b"".join(map(bytes, datas))
        else:
            data = b""
        return varint.encode(len(id_varint + data)) + id_varint + data


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
            for ver in vars.protocol_map:
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
                elif fmt_code in vars.color_map.keys():  # 颜色
                    state["color"] = vars.color_map[fmt_code]
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


def test():
    r"""obj = json_load(open(r"D:\儿子文件\资源\扫描结果.json", encoding="utf-8"))
    for info in obj:
        details: dict = eval(b64decode(info['details']).decode("utf-8"))
        # 做测试
        try:
            p_info = ServerInfo(details)
            print(p_info.online_server)
            print("-" * 50)
        except TimeoutError as e:
            print(details)
            print(e.__class__.__name__)
            print("-" * 50)"""
    port = Port()
    print(port.get_server_info())


def temp2(info):
    if isinstance(info, dict):
        if info["status"] != "offline":
            print(info)
    if isinstance(info, ServerInfo):
        print(info.__dict__)


"""print("START")
s = ServerScanner()
s.config("cn-yw-plc-1.openfrp.top", 0.7, 128)
s.run(port_range=range(20500, 24000), callback=temp2)
s.join()
print("FINISH")"""
