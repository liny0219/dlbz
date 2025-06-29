import sys
import os
import multiprocessing
multiprocessing.freeze_support()

# 修复打包环境中的标准输出流问题
def fix_stdout_for_frozen():
    """修复打包环境中的标准输出流问题"""
    if getattr(sys, 'frozen', False):
        # 如果是打包环境，确保stdout不为None
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')

# 在导入其他模块前修复stdout
fix_stdout_for_frozen()

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# 导入并应用打包环境修复
try:
    from utils.frozen_fix import fix_frozen_environment
    fix_frozen_environment()
except ImportError:
    pass  # 如果模块不存在，继续执行

from gui.main_window import MainWindow

CONFIG_FILES = [
    ("fengmo.yaml", "逢魔玩法"),
    ("device.yaml", "设备"),
    ("battle.yaml", "战斗设置"),
    ("logging.yaml", "日志"),
    ("ocr.yaml", "OCR"),
]

version = "v1.8.4"

def main():
    title = f"旅人休息站.免费脚本 {version} 分辨率 1280x720 (dpi 240)"
    app = MainWindow(title, CONFIG_FILES)
    app.mainloop()

if __name__ == "__main__":
    main()
