# -*- coding: UTF-8 -*-
from enum import Enum

import comtypes.client as cc
from win32gui import FlashWindowEx

cc.GetModule(r"assets\TaskbarLib.tlb")
import comtypes.gen.TaskbarLib as TaskbarLib


class TBPFLAG(Enum):
    TBPF_NOPROGRESS = 0x00000000
    TBPF_INDETERMINATE = 0x00000001
    TBPF_NORMAL = 0x00000002
    TBPF_ERROR = 0x00000004
    TBPF_PAUSED = 0x00000008


class TaskbarApi:
    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.taskbar = cc.CreateObject(
            "{56FDF344-FD6D-11d0-958A-006097C9A090}",
            interface=TaskbarLib.ITaskbarList3)
        self.taskbar.HrInit()

        self.taskbar.DeleteTab(hwnd)
        self.taskbar.AddTab(hwnd)
        self.taskbar.ActivateTab(hwnd)

    def SetProgressState(self, state: TBPFLAG):
        self.taskbar.SetProgressState(self.hwnd, state.value)

    def SetProgressValue(self, progress: int, _max: int):
        self.taskbar.SetProgressValue(self.hwnd, progress, _max)


class FLASHW(Enum):
    FLASHW_STOP = 0x00000000
    FLASHW_CAPTION = 0x00000001
    FLASHW_TRAY = 0x00000002
    FLASHW_ALL = 0x00000003
    FLASHW_TIMER = 0x00000004
    FLASHW_TIMERNOFG = 0x0000000C


def FlashWindowCount(hwnd: int, count: int = 3, interval: float = 0.5, flags: FLASHW = FLASHW.FLASHW_ALL):
    FlashWindowEx(hwnd, flags.value, count, int(interval * 1000))
