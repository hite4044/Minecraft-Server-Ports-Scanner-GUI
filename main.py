# -*- coding: UTF-8 -*-

def main():
    from time import perf_counter
    all_timer = perf_counter()
    from Gui.UserInterface import GUI

    root = GUI()
    print(f"程序启动时间: {perf_counter() - all_timer:.3f}秒")
    root.mainloop()


if __name__ == '__main__':
    from os import chdir
    from os.path import dirname, abspath
    from sys import path
    path.append(".")

    chdir(dirname(abspath(__file__)))
    main()
