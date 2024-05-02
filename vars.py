from os.path import join as path_join, isfile
from os import getcwd
import json
from typing import List, Dict

# 默认域名
default_server_hosts: List[str] = [
    "s2.wemc.cc",
    "dx31.starmc.cn",
    "mc48.starmc.cn",
    "119.188.245.162",
    "m6.ctymc.cn",
    "rpg.mc1314.cc",
    "mcpvp.asia",
    "cn-yw-plc-1.openfrp.top",
    "play.simpfun.cn",
    "ningbo-3689d402.of-7af93c01.shop",
    "cn-hz-bgp-1.of-7af93c01.shop",
    "cn-hk-bgp-4.openfrp.top",
    "ganzhou-eb7c59a5.of-7af93c01.shop",
    "cn-he-plc-2.of-7af93c01.shop",
    "cn-bj-plc-2.of-7af93c01.shop",
    "shenzhen-a8bf9282.of-7af93c01.shop",
    "ipyingshe.com",
    "xiaomy.net",
    "yuming.net",
    "dongtaiyuming.net",
    "chiyu.red",
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
    "server.hpnetwork.top"
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
try:
    with open(path_join("assets", "protocol_map.json"), "r") as f:
        protocol_map = json.load(f)
except OSError:
    print("protocol_map.json 文件不存在")

# 需要扫描的服务器地址列表
server_addresses: List[str] = default_server_hosts.copy()


class UserAddressOperator:
    # 拼接json路径
    user_address_json = path_join(getcwd(), "config", "user_address_record.json")

    def __init__(self) -> None:
        """需要扫描的服务器地址操作器"""
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
            # 写入新的用户域名
            with open(self.user_address_json, "w", encoding="utf-8") as rfp:
                json.dump({"address_list": address_list + [address]}, rfp)
            return True
        except Exception as e:
            print("写入 user_address_record.json 时：", e)
            return False


# 初始化数据
UserAddressOperator().readConfigFileList()
