import logging
import sys
from common.config import config

def setup_logger():
    """
    配置标准logging日志输出到控制台
    自动兼容loguru风格的日志格式
    """
    log_format = config.logging.format
    # 自动兼容loguru风格格式
    if '{' in log_format and '}' in log_format:
        # 常见loguru风格占位符替换为logging风格
        log_format = (log_format
            .replace('{time}', '%(asctime)s')
            .replace('{level}', '%(levelname)s')
            .replace('{message}', '%(message)s')
            .replace('{name}', '%(name)s')
            .replace('{process}', '%(process)d')
            .replace('{thread}', '%(thread)d')
        )
    log_level = config.logging.level
    logger = logging.getLogger("dldbz")
    logger.setLevel(log_level)
    # 移除所有旧的handler
    if logger.hasHandlers():
        logger.handlers.clear()
    formatter = logging.Formatter(log_format)
    # 控制台输出
    if sys.stdout is None:
        handler = logging.FileHandler("logs/main.log", encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# 兼容loguru风格用法，直接暴露logger实例
logger = setup_logger() 