import os
import sys

def get_asset_path(rel_path: str) -> str:
    """
    获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境。
    优先查找dist/、_MEIPASS/、cwd/、项目根目录。
    :param rel_path: 相对路径，如'assets/inn_bed.png'或'config/settings.yaml'
    :return: 绝对路径
    """
    # 1. PyInstaller打包环境
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        dist_path = os.path.join(exe_dir, rel_path)
        if os.path.exists(dist_path):
            return dist_path
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path:
            meipass_path = os.path.join(base_path, rel_path)
            if os.path.exists(meipass_path):
                return meipass_path
        cwd_path = os.path.join(os.getcwd(), rel_path)
        if os.path.exists(cwd_path):
            return cwd_path
    # 2. 开发环境
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    dev_path = os.path.join(project_root, rel_path)
    if os.path.exists(dev_path):
        return dev_path
    # 3. 兜底：直接返回相对路径
    return rel_path 