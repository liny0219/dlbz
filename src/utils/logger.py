import logging
import sys
import os

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

def setup_logger(append_log_func=None, log_format=None, datefmt=None):
    """
    配置标准logging日志输出到控制台/文件，并可选注册GUI日志Handler
    """
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
    if append_log_func:
        handler = GuiLogHandler(append_log_func)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
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
    logger.propagate = False
    return logger

# 默认logger不带GUI Handler
logger = setup_logger() 