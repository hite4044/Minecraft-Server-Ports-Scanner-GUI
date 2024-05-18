import ctypes
import warnings

import comtypes.client as cc

cc.GetModule(r"assets\TaskbarLib.tlb")

import comtypes.gen.TaskbarLib as tbl

taskbar = cc.CreateObject(
    "{56FDF344-FD6D-11d0-958A-006097C9A090}",
    interface=tbl.ITaskbarList3)

hWnd = ctypes.windll.kernel32.GetConsoleWindow()
taskbar.ActivateTab(hWnd)


class Progress(object):
    def __init__(self, hwnd=hWnd):
        super().__init__()
        self.initialised = False
        self.state = None
        self.win = hwnd

    def init(self):
        self.thisWindow = self.win
        taskbar.ActivateTab(self.win)
        taskbar.HrInit()
        self.state = 'normal'
        self.progress = 0
        self.initialised = True

    def setState(self, value):
        if not self.initialised:
            warnings.warn('Please initialise the object (method: Progress.initialise())')
            return

        match value:
            case 'normal':
                taskbar.SetProgressState(self.thisWindow, 0)
                self.state = 'normal'

            case 'warning':
                taskbar.SetProgressState(self.thisWindow, 10)
                self.state = 'warning'

            case 'error':
                taskbar.SetProgressState(self.thisWindow, 15)
                self.state = 'error'

            case 'loading':
                taskbar.SetProgressState(self.thisWindow, -15)
                self.state = 'loading'

            case 'done':
                ctypes.windll.user32.FlashWindow(self.thisWindow, True)
                self.state = 'done'

            case _:
                warnings.warn(
                    'Invalid Argument {}. Please select one from (normal, warning, error, loading, done).'.format(
                        value))

    def setProgress(self, value: int):
        if value > 100 or value < 0:
            warnings.warn('Invalid Argument {} .Please select one from (<=100,>=0).'.format(value))

        if self.initialised:
            taskbar.setProgressValue(self.thisWindow, value, 100)

        else:
            warnings.warn('Please initialise the object (method:Progress.initialise())')
