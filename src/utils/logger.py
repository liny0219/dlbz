import logging
import sys
import os
from common.config import config

def setup_logger(gui_log_func=None):
    """
    配置标准logging日志输出到控制台/文件，并可选注册GUI日志Handler
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
    # GUI日志Handler（可选）
    if gui_log_func is not None:
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
        gui_handler = GuiLogHandler(gui_log_func)
        gui_handler.setLevel(log_level)
        gui_handler.setFormatter(formatter)
        # 避免重复添加
        if not any(isinstance(h, GuiLogHandler) for h in logger.handlers):
            logger.addHandler(gui_handler)
    # 屏蔽第三方库debug日志
    logging.getLogger("uiautomator2").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger.propagate = False
    return logger

# 默认logger不带GUI Handler
logger = setup_logger() 