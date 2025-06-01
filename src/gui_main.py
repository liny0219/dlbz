import sys
import tkinter as tk
from gui.main_window import MainWindow

CONFIG_FILES = [
    ("fengmo.yaml", "逢魔玩法"),
    ("device.yaml", "设备"),
    ("battle.yaml", "战斗设置"),
    ("logging.yaml", "日志"),
    ("game.yaml", "游戏"),
    ("ocr.yaml", "OCR"),
]

def main():
    app = MainWindow(CONFIG_FILES)
    app.mainloop()

if __name__ == "__main__":
    main()
