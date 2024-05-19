# -*- coding: UTF-8 -*-
import json
from os import mkdir
from typing import List, Dict
from win32print import GetDeviceCaps
from win32api import GetSystemMetrics
from win32gui import GetDC, ReleaseDC
from win32con import SM_CXSCREEN, DESKTOPHORZRES
from os.path import join as path_join, isfile, exists

# 默认域名
default_server_hosts: List[str] = [
    "s2.wemc.cc",
    "m6.ctymc.cn",
    "mc20.rhymc.com",
    "s8.singsi.cn",
    "mc13.ytonidc.com",
    "cn-hk-bgp-4.openfrp.top",  # 141.11.125.121
    "ganzhou-eb7c59a5.of-7af93c01.shop",  # 59.55.0.37
    "ningbo-3689d402.of-7af93c01.shop",  # 110.42.14.112
    "----------------",
    "ipyingshe.com",
    "xiaomy.net",
    "yuming.net",
    "dongtaiyuming.net",
    "dx.wdsj.net",
    "hiaxn.cn",
    "kazer.team",
    "lolita.bgp.originera.cn",
    "lt.wdsj.net",
    "magicalserver.tpddns.cn",
    "magicmc.cn",
    "mc.163mc.cn",
    "mc.ariacraft.net",
    "mc.kilor.cn",
    "mc.remiaft.com",
    "mc20.rhymc.com",
    "mc3.rhymc.com",
    "mcyc.win",
    "mhxj.club",
    "play.cloudegg.cloud",
    "play.simpfun.cn",
    "sa1.mc164.cn",
    "server.hpnetwork.top",
    "cn-yw-plc-1.openfrp.top-我想你了",
    "frp-can.top-想被BanIP的扫它-只能扫一次",  # 61.139.65.143
]

# 颜色对照表
color_map: Dict[str, str] = {
    "0": "black",
    "1": "dark_blue",
    "2": "dark_green",
    "3": "dark_aqua",
    "4": "dark_red",
    "5": "dark_purple",
    "6": "gold",
    "7": "gray",
    "8": "dark_gray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "light_purple",
    "e": "yellow",
    "f": "white",
}
color_map_hex: Dict[str, str] = {
    "black": "#000000",
    "dark_blue": "#0000AA",
    "dark_green": "#00AA00",
    "dark_aqua": "#00AAAA",
    "dark_red": "#AA0000",
    "dark_purple": "#AA00AA",
    "gold": "#FFAA00",
    "gray": "#AAAAAA",
    "dark_gray": "#555555",
    "blue": "#5555FF",
    "green": "#55FF55",
    "aqua": "#55FFFF",
    "red": "#FF5555",
    "light_purple": "#FF55FF",
    "yellow": "#FFFF55",
    "white": "#FFFFFF",
}

# 加载协议映射表
protocol_map: List[Dict[str, str]] = []
json_file_path = path_join("assets", "protocol_map.json")
if exists(json_file_path):
    with open(json_file_path, "r") as file:
        protocol_map = json.load(file)
else:
    print("protocol_map.json 文件不存在")

# 需要扫描的服务器地址列表
server_addresses: List[str] = default_server_hosts.copy()

# 设置
config_dir = "../config"
if not exists(path_join(config_dir)):
    mkdir(path_join(config_dir))


class UserAddressOperator:
    # 拼接json路径
    user_address_json = path_join(config_dir, "user_address_record.json")

    def __init__(self) -> None:
        """需要扫描的服务器地址操作器"""
        # 创建user_address_record.json文件
        if isfile(self.user_address_json) is False:
            with open(self.user_address_json, "w+", encoding="utf-8") as wfp:
                wfp.write("{\n\t\"address_list\": []\n}")

    def readConfigFileList(self) -> List[str]:
        """
        读取user_address_record.json数据，并添加进ServerList
        :return List[str]
        """
        global server_addresses
        result: List[str] = []

        try:
            with open(self.user_address_json, "r", encoding="utf-8") as rfp:
                json_data: dict = json.loads(rfp.read())
                address_list: List[str] = json_data.get('address_list')

                # 未读取到address_list
                if not address_list:
                    return result

                # 读取到数据后
                if address_list:
                    server_addresses.extend(address_list)
        except Exception as e:
            print("读取 user_address_record.json 文件时：", e)
        finally:
            return result

    def writeAddressToConfigFile(self, address: str) -> bool:
        """
        写入服务器地址至user_address_record.json文件中去
        :param address: str 服务器地址
        :return bool
        """
        try:
            # 获取原有的用户域名
            with open(self.user_address_json, "r", encoding="utf-8") as rfp:
                json_data: dict = json.loads(rfp.read())
                address_list: List[str] = json_data.get('address_list')
            if address not in address_list or address not in server_addresses:
                # 写入新的用户域名
                with open(self.user_address_json, "w", encoding="utf-8") as rfp:
                    json.dump({"address_list": address_list + [address]}, rfp, indent=4)
                server_addresses.append(address)
            return True
        except Exception as e:
            print("写入 user_address_record.json 时：", e)
            return False


class ScaleRater:
    """
    获取屏幕缩放比例的类
    因为窗口创建后计算值不在准确
    所以仅在窗口创建前获取一次值
    """
    def __init__(self):
        self.scale_rate: float = 1.0
        self.update_scale_rate()

    def update_scale_rate(self):
        hdc = GetDC(0)
        real_width = GetDeviceCaps(hdc, DESKTOPHORZRES)
        ReleaseDC(0, hdc)
        fake_width = GetSystemMetrics(SM_CXSCREEN)
        new_scale_rate = round(real_width / fake_width, 2)
        if new_scale_rate != self.scale_rate:
            self.scale_rate = new_scale_rate

    def __call__(self) -> float:
        return self.scale_rate


# 初始化数据
UserAddressOperator().readConfigFileList()

scale_rater = ScaleRater()