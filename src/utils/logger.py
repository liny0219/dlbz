from loguru import logger
import sys
from common.config import config

def setup_logger():
    """
    配置loguru日志输出到控制台
    """
    log_format = config.logging.format
    log_level = config.logging.level
    logger.remove()  # 删除所有处理器
    # 日志路径判断sys.stdout是否为空,为空则输出到默认日志文件
    if sys.stdout is None:
        logger.add("logs/main.log", format=log_format, level=log_level)
    else:
        logger.add(sys.stdout, format=log_format, level=log_level)
    return logger 