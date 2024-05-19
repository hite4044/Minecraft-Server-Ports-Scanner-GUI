# -*- coding: UTF-8 -*-

def main():
    from Gui.UserInterface import GUI
    root = GUI()
    root.mainloop()


if __name__ == '__main__':
    import os

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
