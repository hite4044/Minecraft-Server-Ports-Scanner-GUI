# -*- coding: UTF-8 -*-
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from main_gui import GUI


def load():
    root = GUI()
    root.mainloop()


if __name__ == '__main__':
    load()
