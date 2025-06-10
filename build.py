import os
import shutil
import subprocess
import paddle
import time
from datetime import datetime

"""
通用打包任务脚本。
后续可在此脚本中集成所有打包、资源整理、自动化构建等逻辑。
包含详细的时间统计功能，用于监控打包过程中各阶段的耗时。
"""

def format_duration(seconds):
    """
    格式化时间显示
    将秒数转换为易读的时分秒格式
    
    Args:
        seconds (float): 耗时秒数
        
    Returns:
        str: 格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds:.2f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}小时{minutes}分{remaining_seconds:.2f}秒"

def print_stage_info(stage_name, start_time=None, end_time=None):
    """
    打印阶段信息，包括开始时间、结束时间和耗时
    
    Args:
        stage_name (str): 阶段名称
        start_time (float, optional): 开始时间戳
        end_time (float, optional): 结束时间戳
    """
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if start_time is None and end_time is None:
        print(f"[{current_time}] [打包脚本] ===============================")
        print(f"[{current_time}] [打包脚本] 开始执行: {stage_name}")
        print(f"[{current_time}] [打包脚本] ===============================")
    elif end_time is not None:
        duration = end_time - start_time
        formatted_duration = format_duration(duration)
        print(f"[{current_time}] [打包脚本] {stage_name} 完成！耗时: {formatted_duration}")
        print(f"[{current_time}] [打包脚本] ===============================")

def main():
    """
    主打包函数
    执行完整的打包流程，包括清理、打包、资源复制、压缩等步骤
    每个阶段都会记录详细的时间统计信息
    """
    # 记录总开始时间
    total_start_time = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"[打包脚本] 开始打包任务")
    print(f"[打包脚本] 开始时间: {start_datetime}")
    print(f"{'='*60}")
    
    # 阶段1: 清理dist目录
    print_stage_info("清理dist目录")
    stage_start = time.time()
    
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
    
    stage_end = time.time()
    print_stage_info("清理dist目录", stage_start, stage_end)
    
    # 阶段2: PyInstaller打包
    print_stage_info("PyInstaller打包")
    pyinstaller_start = time.time()
    
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
    
    pyinstaller_end = time.time()
    print_stage_info("PyInstaller打包", pyinstaller_start, pyinstaller_end)

    # 阶段3: 复制资源文件
    print_stage_info("复制资源文件")
    copy_start = time.time()
    
    # 复制多个资源目录
    src_dirs = ['config', 'assets','adb']  # 目录列表
    for src_dir in src_dirs:
        dir_copy_start = time.time()
        dst_dir = os.path.join('dist', src_dir)
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        dir_copy_end = time.time()
        dir_duration = format_duration(dir_copy_end - dir_copy_start)
        print(f"[打包脚本] 已将 {src_dir} 目录完整复制到 {dst_dir} (耗时: {dir_duration})")
    
    src_files = ['更新说明.txt','旅馆休息站使用说明.docx']  # 文件列表
    # 复制单个文件
    for src_file in src_files:
        if os.path.exists(src_file):
            shutil.copy2(src_file, 'dist')
            print(f"[打包脚本] 已将 {src_file} 文件复制到 dist 目录")
    
    copy_end = time.time()
    print_stage_info("复制资源文件", copy_start, copy_end)

    # 阶段4: 获取版本号和压缩
    print_stage_info("获取版本号和压缩打包")
    compress_start = time.time()
    
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
    
    print(f"[打包脚本] 检测到版本号: {version}")
        
    # 压缩dist目录
    zip_start = time.time()
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
    zip_end = time.time()
    zip_duration = format_duration(zip_end - zip_start)
    print(f"[打包脚本] 已将 dist 目录压缩为 {zip_name} 文件 (压缩耗时: {zip_duration})")
    
    # 压缩后放到dist目录下
    shutil.move(zip_name, os.path.join('dist', zip_name))
    print(f"[打包脚本] 已将 {zip_name} 文件移动到 dist 目录下")
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    compress_end = time.time()
    print_stage_info("获取版本号和压缩打包", compress_start, compress_end)

    # 检查 paddle/libs 目录
    print(f"[打包脚本] Paddle库路径: {os.path.join(os.path.dirname(paddle.__file__), 'libs')}")
    
    # 计算总耗时并输出统计信息
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"[打包脚本] 打包任务完成！")
    print(f"[打包脚本] 结束时间: {end_datetime}")
    print(f"[打包脚本] 总耗时: {format_duration(total_duration)}")
    print(f"{'='*60}")
    
    # 详细时间统计
    clean_duration = stage_end - stage_start
    pyinstaller_duration = pyinstaller_end - pyinstaller_start
    copy_duration = copy_end - copy_start
    compress_duration = compress_end - compress_start
    
    print(f"\n[打包脚本] 📊 详细时间统计:")
    print(f"[打包脚本]   ├─ 清理dist目录: {format_duration(clean_duration)} ({clean_duration/total_duration*100:.1f}%)")
    print(f"[打包脚本]   ├─ PyInstaller打包: {format_duration(pyinstaller_duration)} ({pyinstaller_duration/total_duration*100:.1f}%)")
    print(f"[打包脚本]   ├─ 复制资源文件: {format_duration(copy_duration)} ({copy_duration/total_duration*100:.1f}%)")
    print(f"[打包脚本]   ├─ 压缩打包: {format_duration(compress_duration)} ({compress_duration/total_duration*100:.1f}%)")
    print(f"[打包脚本]   └─ 总计: {format_duration(total_duration)}")
    print(f"\n[打包脚本] ✅ 打包文件已生成: dist/{zip_name}")

if __name__ == '__main__':
    main() 