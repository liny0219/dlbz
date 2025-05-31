import logging
import sys
import os
from common.config import config

def setup_logger():
    """
    配置标准logging日志输出到控制台
    自动兼容loguru风格的日志格式
    """
    log_format, datefmt = config.get_logging_format_and_datefmt(config.logging.format, getattr(config.logging, 'datefmt', None))
    log_level = config.logging.level
    logger = logging.getLogger("dldbz")
    logger.setLevel(log_level)
    # 移除所有旧的handler
    if logger.hasHandlers():
        logger.handlers.clear()
    formatter = config.get_no_millisec_formatter(log_format, datefmt)
    # 控制台输出
    if sys.stdout is None:
        # 日志目录不存在则自动创建
        os.makedirs("logs", exist_ok=True)
        handler = logging.FileHandler("logs/main.log", encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # 屏蔽第三方库debug日志
    logging.getLogger("uiautomator2").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logger

# 兼容loguru风格用法，直接暴露logger实例
logger = setup_logger() 