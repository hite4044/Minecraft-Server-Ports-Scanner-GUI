# -*- coding: UTF-8 -*-

def main():
    from Gui.UserInterface import GUI
    root = GUI()
    root.mainloop()


if __name__ == '__main__':
    from os import chdir
    from os.path import dirname, abspath

    chdir(dirname(abspath(__file__)))
    main()
