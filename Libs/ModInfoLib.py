from typing import List

import requests
from io import BytesIO
from bs4 import BeautifulSoup
from bs4.element import Tag
from PIL import Image
import cloudscraper

from time import sleep
#测试中
#
#
#
#
#我去我本地看一下
#
#
#
cookies = {"__cf_bm": "Ar_3IM4pzUOS4MTg0VWUzja.4Zufme1G1kBVMvMVMQk-1717896788-1.0.1.1-7Nus_RBqAVHGSw7V9xvLlC6UzcSPeZjHTVJ.RhXg2CbCGxqpf3zwM7gBUgmvQJKRRV_doIN4nnn87FA6DBelv8heMElEKW4reUOKcSDiooA"}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"}
curseforge = "https://www.curseforge.com"


class ModFileInfo:
    def __init__(self, file_tag: Tag, project_id: str):
        self.file_id = file_tag.find("a", class_="file-row-details").attrs["href"].split("/")[-1]
        self.file_url = f"{curseforge}/api/v1/mods/{project_id}/files/{self.file_id}/download"
        self.name = file_tag.find("span", class_="name").text


class ModFilesInfo:
    def __init__(self, url_name: str, game_version: str, correct_version: str):
        self.url = f"{curseforge}/minecraft/mc-mods/{url_name}/files/all"
        self.game_version = game_version
        self.correct_version = correct_version
        self.files_list: List[ModFileInfo] = []
        self.project_id = url_name

    def load_files_url(self):
        params = {"version": self.game_version, "page": "1", "pageSize": "20"}
        resp = requests.get(self.url, headers=headers, params=params, cookies=cookies)
        soup = BeautifulSoup(resp.text, "html.parser")
        project_info = soup.find("div", class_=["aside-box", "project-details-box"])
        for i in project_info.find("section").find_all("dd"):
            if i.find("span") is None:
                self.project_id = i.text
                break

        files_div = soup.find("div", class_="files-table")
        self.files_list.clear()
        for file_tag in files_div.children:
            assert isinstance(file_tag, Tag)
            if "file-row" in file_tag.attrs["class"]:
                self.files_list.append(ModFileInfo(file_tag, self.project_id))

    def get_download_url(self):
        for mod_file_info in self.files_list:
            if self.correct_version in mod_file_info.name:
                return mod_file_info.file_url


class ModInfo:
    def __init__(self, mod_tag: Tag, game_version: str, correct_version: str):
        print(mod_tag.text)
        self.id = mod_tag.find("a", class_="btn-cta download-cta").attrs["href"].split("/")[-1]
        self.title = mod_tag.find("a", class_="name").attrs["title"]
        self.url_name = mod_tag.find("a", class_="name").attrs["href"].split("/")[-1]
        self.image_url = mod_tag.find("img", attrs={"id": "row-image"}).attrs["src"]
        self.description = mod_tag.find("p", class_="description").text

        self.download_count = mod_tag.find("li", class_="detail-downloads").text
        self.last_updated = mod_tag.find("li", class_="detail-updated").text
        self.game_version = mod_tag.find("li", class_="detail-game-version").text
        self.game_version2 = game_version
        self.correct_version = correct_version
        self.size = mod_tag.find("li", class_="detail-size").text
        self.mod_loader = mod_tag.find("li", class_="detail-flavor").text

        self.file_obj = None

    def load_files(self):
        self.file_obj = ModFilesInfo(self.url_name, self.game_version2, self.correct_version)

    @property
    def image(self) -> Image.Image:
        resp = requests.get(self.image_url)
        image_io = BytesIO(resp.content)
        return Image.open(image_io, formats=["PNG"])

    def __str__(self):
        return f"Minecraft {self.mod_loader} Mod: {self.title}"


class Mod:
    def __init__(self, mod_id: str, game_version: str, correct_version: str):
        self.mod_info = None
        self.mod_id = mod_id
        self.game_version = game_version
        self.correct_version = correct_version
        self.mod_list: List[ModInfo] = []

    def load_mod_info(self):
        global cookies
        scraper = cloudscraper.create_scraper()
        url = "https://www.curseforge.com/minecraft/search"
        params = {"page": 1, "pageSize": 4, "class": "mc-mods", "search": self.mod_id}

        resp = requests.get(url, params=params, headers=headers, cookies=cookies)
        if resp.cookies.get("__cf_bm"):
            cookies["__cf_bm"] = resp.cookies.get("__cf_bm")
            resp2 = requests.get(url, params=params, headers=headers)
            cookies["CLID"] = resp2.cookies.get("CLID")

        if "Just a moment..." in resp.text:
            if not cookies.get("__cf_bm"):
                self.load_mod_info()
            else:
                raise RuntimeError("获取模组信息失败")

        self.__load_mod_list(resp.text)
        self.load_possible_mod()

    def __load_mod_list(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        mods_div = soup.find("div", class_="results-container")
        self.mod_list.clear()
        for i in mods_div.children:
            assert isinstance(i, Tag)
            if "project-card" in i.attrs["class"]:
                mod_info = ModInfo(i, self.game_version, self.correct_version)
                self.mod_list.append(mod_info)

    def load_possible_mod(self):
        max_download = 0
        max_mod = None
        for mod in self.mod_list:
            try:
                download_count = float(mod.download_count)
            except ValueError:
                download_count = float(mod.download_count[:-1])
                if mod.download_count[-1] == "K":
                    download_count *= 1000
                elif mod.download_count[-1] == "M":
                    download_count *= 100000
                elif mod.download_count[-1] == "B":
                    download_count *= 10000000
                else:
                    print(f"什么单位?:({mod.download_count[-1]})")
                    download_count = 0
            if download_count > max_download:
                max_download = download_count + 1 - 1
                max_mod = mod
        self.mod_info = max_mod

    def get_download_url(self):
        self.mod_info.load_files()
        assert isinstance(self.mod_info.file_obj, ModFilesInfo)
        self.mod_info.file_obj.load_files_url()
        return self.mod_info.file_obj.get_download_url()


haha = Mod("vampirism", "1.20.1", "1.10.8")
haha.load_mod_info()
haha.get_download_url()