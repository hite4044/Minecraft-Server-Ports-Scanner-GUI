# -*- coding: UTF-8 -*-
from enum import Enum

import comtypes.client as cc
from win32gui import FlashWindowEx

cc.GetModule(r"assets\TaskbarLib.tlb")
import comtypes.gen.TaskbarLib as TaskbarLib


class FLASHW(Enum):
    FLASHW_STOP = 0x00000000
    FLASHW_CAPTION = 0x00000001
    FLASHW_TRAY = 0x00000002
    FLASHW_ALL = 0x00000003
    FLASHW_TIMER = 0x00000004
    FLASHW_TIMERNOFG = 0x0000000C


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
        self.taskbar.ActivateTab(hwnd)
        self.taskbar.HrInit()

    def set_progress_state(self, state: TBPFLAG):
        self.taskbar.setProgressState(self.hwnd, state.value)

    def set_progress_value(self, progress: int, maximum: int):
        self.taskbar.setProgressValue(self.hwnd, progress, maximum)

    def flash_window(self, count: int = 3, interval: float = 0.5, flags: int = 3):
        FlashWindowEx(self.hwnd, flags, count, int(interval * 1000))
