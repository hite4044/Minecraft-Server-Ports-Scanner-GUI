from win32gui import GetWindowText, SetWindowText, FindWindow, FindWindowEx, GetParent, EnumChildWindows
from time import time, sleep


def override_msg_window_buttons(left: str, right: str, timeout: float = 1.2):
    """
    覆写按钮文字

    @param left: 左侧按钮目标文字
    @param right: 右侧按钮目标文字
    @param timeout: 超时时间 (s)
    """
    def callback(hwnd: int, _):
        if GetWindowText(hwnd) == "是(&Y)":
            SetWindowText(hwnd, left)
        elif GetWindowText(hwnd) == "否(&N)":
            SetWindowText(hwnd, right)

    main_win = FindWindow("TkTopLevel", "MC服务器扫描器")
    timer = time()
    while True:
        msg_win = FindWindowEx(None, None, "#32770", "加载方式 ⠀")
        if msg_win == 0:
            if time() - timer > timeout:
                return
            sleep(0.1)
            continue
        if GetParent(msg_win) != main_win:
            return
        EnumChildWindows(msg_win, callback, None)
        return
