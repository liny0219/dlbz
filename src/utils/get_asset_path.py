import os
import sys


def get_asset_path(rel_path: str,pack_mode:bool = False) -> str:
    """获取资源的绝对路径，处理打包和非打包两种情况"""
    if pack_mode:
        try:
            # PyInstaller 创建临时文件夹，保存打包的文件
            base_path = getattr(sys, '_MEIPASS', None)
            if base_path is None:
                base_path = os.path.abspath(".")
        except Exception:
            # 未打包时使用的目录
            base_path = os.path.abspath(".")
        return os.path.join(base_path, rel_path)
    else:
        return rel_path
    