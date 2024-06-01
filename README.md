<div align="center">

![Logo](./assets/icon.ico)

# *Minecraft Server Ports Scanner GUI*

</div>

Language:

1. [简体中文](README.md)
2. [English](Docs/README_EN.md)

---

> [!IMPORTANT]
>
> _免责声明: 这仅用于教育目的, 我不对这些工具的任何滥用负责!_
>
> 请尊重作者及他人, 严禁出售、倒卖或进行任何牟利行为.
>
> 本项目的编写环境为 `Python 3.10.9 64-bit`
>
> 要加功能请[进群](https://qm.qq.com/q/RTR91LyV0o)说一下

## 简介

扫描一个服务器所有端口上的Minecraft服务器, 并把信息显示出来

耗时两周时间开发（我还要上学）

Q群: `153037480`, 名称`MCSPS交流群`, 如有任何疑问, 诚邀[加入我们](https://qm.qq.com/q/RTR91LyV0o).

## 优点

* 漂亮的GUI（使用了ttkbootstrap库, 真的很漂亮）
* ~~卡顿的调整大小~~
* ~~老古董tkinter库~~
* 扫描
    * 支持暂停
    * 多线程扫描
    * 先进的端口范围调节控件
    * 支持过滤服务器版本
* 信息显示
    * 美丽的彩色标题解析
    * Minecraft同款像素字体
    * 玩家UUID显示
    * Mod名称版本显示

## 未来可能完成
* [x] 设置页面
* [x] 信息窗口可重新获取信息并加载
* [x] MC服务器端口范围图表显示(服务器端口范围热图)
* [x] 扫描记录名增加日期
* [x] 热图可以根据鼠标位置显示信息
* [ ] 多扫描任务窗口
* [ ] 服务器信息MOD页 联网获取信息

## 配置环境 & 使用

本项目主分支仅支持 Windows, 感兴趣的可以开发 Mac / Linux 版.

你有两个选择.

1. 下载源码并运行.

   > 您可以使用`git clone`等方式克隆本仓库, 在本仓库目录下运行`pip install -r requirements.txt`
   安装所有本项目需要的模块, 并运行`main.py`.
  
2. 下载压缩包并运行可执行程序. 此压缩包里的代码使用Python嵌入包来运行, Python版本为`Python 3.8.9 32-bit`.

   > 您可以前往 Releases 页面, 直接下载本项目的压缩包文件, 解压出来后运行`MC服务器扫描器3.0.exe`.
   >
   > Releases 页面的 `xx.exe` 文件仅是一个7-Zip自解压程序

## 对开发者

我们**建议**使用 `Google Python Style Guide`.

我们**建议**遵循 `PEP 8` 中的代码规范要求.

## 画廊

![beautiful_GUI](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/a571046d-78af-4250-b70c-e8a52938f6bd)
![Colorful MOTD](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/f9f1b704-9f71-42a2-9e62-2a09c864fdbc)
![ScanControlBar](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/0bf193ce-c7d0-4cec-a7a3-46d9d6708112)
![ServerFilter](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/7f8bece8-46ad-401c-baa1-fc6ac668066c)
