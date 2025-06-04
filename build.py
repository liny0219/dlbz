import os
import shutil
import subprocess
import paddle

"""
通用打包任务脚本。
后续可在此脚本中集成所有打包、资源整理、自动化构建等逻辑。
"""

def main():
    # 清空dist目录内的文件
    if os.path.exists('dist'):
        print("[打包脚本] 清空 dist 目录内的文件...")
        for item in os.listdir('dist'):
            item_path = os.path.join('dist', item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print("[打包脚本] dist 目录内文件已清空")
    else:
        os.makedirs('dist')
        print("[打包脚本] 创建 dist 目录")
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

    # 从gui_main.py获取version
    version = None
    with open('src/gui_main.py', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('version = '):
                version = line.split('=')[1].strip().strip('"\'')
                break
    
    if not version:
        print("[打包脚本] 警告: 无法从gui_main.py获取版本号")
        version = "unknown"
        
    # 压缩dist目录
    zip_name = f"旅人休息站{version}.zip"
    # 创建一个临时目录来包装dist内容
    temp_dir = "temp_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    # 将dist目录内容复制到临时目录的子目录中
    shutil.copytree('dist', os.path.join(temp_dir, f'旅人休息站{version}'))
    # 从临时目录创建zip文件
    shutil.make_archive(zip_name.replace('.zip',''), 'zip', temp_dir)
    print(f"[打包脚本] 已将 dist 目录压缩为 {zip_name} 文件")
    # 压缩后放到dist目录下
    shutil.move(zip_name, os.path.join('dist', zip_name))
    print(f"[打包脚本] 已将 {zip_name} 文件移动到 dist 目录下")
    # 清理临时目录
    shutil.rmtree(temp_dir)

    # 检查 paddle/libs 目录
    print(os.path.join(os.path.dirname(paddle.__file__), 'libs'))

if __name__ == '__main__':
    main() 