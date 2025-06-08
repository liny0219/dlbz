import logging
import sys
import os
import shutil
import time
from pathlib import Path

class GuiLogHandler(logging.Handler):
    def __init__(self, append_log_func):
        super().__init__()
        self.append_log_func = append_log_func
    def emit(self, record):
        try:
            msg = self.format(record)
            self.append_log_func(msg)
        except Exception:
            pass

def get_logs_dir_size(logs_dir: str = "logs") -> float:
    """
    获取日志目录的总大小（MB）
    
    :param logs_dir: 日志目录路径
    :return: 目录大小（MB）
    """
    try:
        if not os.path.exists(logs_dir):
            return 0.0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(logs_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        return total_size / (1024 * 1024)  # 转换为MB
    except Exception as e:
        print(f"获取日志目录大小失败: {e}")
        return 0.0

def cleanup_logs_dir(logs_dir: str = "logs", max_size_mb: float = 10.0) -> bool:
    """
    检查并清理日志目录
    如果目录大小超过指定限制，则清空目录重新创建
    
    :param logs_dir: 日志目录路径
    :param max_size_mb: 最大允许大小（MB）
    :return: 是否执行了清理操作
    """
    try:
        current_size = get_logs_dir_size(logs_dir)
        
        if current_size > max_size_mb:
            print(f"日志目录大小 {current_size:.2f}MB 超过限制 {max_size_mb}MB，开始清理...")
            
            # 删除整个目录
            if os.path.exists(logs_dir):
                shutil.rmtree(logs_dir)
            
            # 重新创建目录
            os.makedirs(logs_dir, exist_ok=True)
            
            print(f"日志目录已清理完成")
            return True
        else:
            print(f"日志目录大小 {current_size:.2f}MB，无需清理")
            return False
            
    except Exception as e:
        print(f"清理日志目录失败: {e}")
        return False

def get_log_file_path(logs_dir: str = "logs", prefix: str = "main") -> str:
    """
    生成带时间戳的日志文件路径
    
    :param logs_dir: 日志目录
    :param prefix: 日志文件前缀
    :return: 日志文件完整路径
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.log"
    return os.path.join(logs_dir, filename)

def setup_logger(append_log_func=None, log_format=None, datefmt=None, cleanup_on_start=True, enable_file_log=True):
    """
    配置标准logging日志输出到控制台/文件，并可选注册GUI日志Handler
    
    :param append_log_func: GUI日志追加函数
    :param log_format: 日志格式
    :param datefmt: 日期格式
    :param cleanup_on_start: 是否在启动时检查并清理日志目录
    :param enable_file_log: 是否启用文件日志写入，默认True
    """
    # 在设置日志前先检查并清理日志目录
    if cleanup_on_start:
        cleanup_logs_dir()
    
    logger = logging.getLogger("dldbz")
    logger.setLevel(logging.INFO)
    # 移除所有旧的handler
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 始终有默认formatter
    if log_format:
        formatter = logging.Formatter(log_format, datefmt=datefmt)
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    
    # GUI Handler（如果提供）
    if append_log_func:
        handler = GuiLogHandler(append_log_func)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # 文件Handler - 根据enable_file_log参数决定是否写入本地日志文件
    if enable_file_log:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        log_file_path = get_log_file_path(logs_dir)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # 记录日志系统启动信息
        logger.info(f"日志系统已启动，日志文件: {log_file_path}")
    else:
        # 不启用文件日志时，仅输出到控制台或GUI
        log_file_path = None
    
    # 控制台Handler - 只在有stdout时添加
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 屏蔽第三方库debug日志
    logging.getLogger("uiautomator2").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger.propagate = False
    
    return logger

# 默认logger不带GUI Handler，也不写入文件日志
logger = setup_logger(enable_file_log=False) 