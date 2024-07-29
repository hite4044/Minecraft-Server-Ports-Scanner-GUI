# -*- coding: UTF-8 -*-
import sys
import os


def check_con():
    if "-no_console" in sys.argv:
        from win32console import GetConsoleWindow
        from win32gui import ShowWindow, SetWindowLong
        from win32con import SW_HIDE, GWL_EXSTYLE, WS_EX_TOOLWINDOW
        try:
            hwnd = GetConsoleWindow()
            if hwnd:
                ShowWindow(hwnd, SW_HIDE)
            SetWindowLong(hwnd, GWL_EXSTYLE, WS_EX_TOOLWINDOW)
        except Exception as e:
            _ = e

def main():
    check_con()
    from time import perf_counter
    all_timer = perf_counter()
    from Gui.UserInterface import GUI

    gui_timer = perf_counter()
    root = GUI()
    print(f"GUI初始化时间: {perf_counter() - gui_timer:.3f}秒")
    print(f"程序启动时间: {perf_counter() - all_timer:.3f}秒")
    root.mainloop()
    from io import BytesIO
    sys.stderr = BytesIO()


if __name__ == '__main__':
    sys.path.append(".")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
