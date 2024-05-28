<div align="center">

![Logo](../assets/icon.ico)

# *Minecraft Server Ports Scanner GUI*

</div>

Language:

1. [简体中文](../README.md)
2. [English](README_EN.md)

---

> [!IMPORTANT]
>
> _Disclaimer of Warranties: This is only for the educational purpose, not responsible for any conflict._
>
> Selling, reselling, or engaging in any profit-making activity is strictly forbidden.
>
> The project uses `Python 3.10.9 64-bit`.
>
> Before any pull requests submitted, [join our QQ channel](https://qm.qq.com/q/RTR91LyV0o) first.

## Introduction

A tool to scan for a Minecraft server on all ports of an IP address and display the information.

Our QQ channel is `153037480` named `MCSPS交流群`. If you have any problems about our project, highly recommended to [join us](https://qm.qq.com/q/RTR91LyV0o).

## Features

* Beautiful GUI ( which is present by ttkbootstrap )
* ~~Lagged window size changing~~
* ~~Ancient tkinter library~~
* Scan
    * Pause supported
    * Multi-thread scanning
    * Advanced port range adjustment control
    * Server versions filtering available
* Information displaying
    * Beautiful colorful title parse
    * Minecraft fonts
    * Player UUID displayed
    * Mod name & version displayed

## Future
* [x] Settings
* [ ] Multi-window for scanning tasks
* [x] The functionality for the info window to be reloaded
* [ ] Live-time chart showing scanning speed
* [ ] Minecraft server ports displaying with chart
* [ ] Listing ports with treemap
* [x] Scan records with date recorded

## Environment Setups & Using

The main branch only support Windows, Mac / Linux development is welcomed if interested.

There are two choice for you.

1. Download the code and run.

   > You can use `git clone`, etc. to download the repository, then run `pip install -r requirements.txt`
   to install all the modules needed, finally run `main.py` to run the program.

2. Download the zip package and run the executable program.

   > The code in this zip package runs on `Python 3.8.9 32-bit` embedded.
   > 
   > You can directly go to Releases, download the zip package, unzip, and run `MC服务器扫描器3.0.exe`.
   >
   > `xx.exe` on Releases page is a 7-Zip self-extracting program.

## To developers

`Google Python Style Guide` & `PEP 8` is **recommended** to obey.

## Gallery

![beautiful_GUI](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/a571046d-78af-4250-b70c-e8a52938f6bd)
![Colorful MOTD](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/f9f1b704-9f71-42a2-9e62-2a09c864fdbc)
![ScanControlBar](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/0bf193ce-c7d0-4cec-a7a3-46d9d6708112)
![ServerFilter](https://github.com/hite4044/Minecraft-Server-Ports-Scanner-GUI/assets/129571243/7f8bece8-46ad-401c-baa1-fc6ac668066c)
