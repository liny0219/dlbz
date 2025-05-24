import os
import shutil
import subprocess
import paddle

"""
通用打包任务脚本。
后续可在此脚本中集成所有打包、资源整理、自动化构建等逻辑。
"""

def main():
    # 1. 运行PyInstaller打包
    print("[打包脚本] 开始运行 PyInstaller 打包...")
    result = subprocess.run([
        'pyinstaller',
        'pyi.spec'
    ], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("[打包脚本] PyInstaller 打包失败！")
        print(result.stderr)
        return
    print("[打包脚本] PyInstaller 打包完成！")

    # 2. 复制多个资源目录
    src_dirs = ['config', 'assets']  # 可根据需要添加更多目录
    for src_dir in src_dirs:
        dst_dir = os.path.join('dist', src_dir)
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        print(f"[打包脚本] 已将 {src_dir} 目录完整复制到 {dst_dir}")
    # TODO: 在此添加更多打包相关自动化逻辑

    # 检查 paddle/libs 目录
    print(os.path.join(os.path.dirname(paddle.__file__), 'libs'))

if __name__ == '__main__':
    main() 