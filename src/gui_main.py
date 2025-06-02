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
    version = "v0.0.9 测试版"
    title = f"旅人休息站.免费脚本 {version} 分辨率 1280x720 (dpi 240)"
    app = MainWindow(title, CONFIG_FILES)
    app.mainloop()

if __name__ == "__main__":
    main()
