from loguru import logger
import sys
import yaml

def setup_logger():
    # 读取配置
    with open("config/settings.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # 配置logger
    logger.remove()  # 删除默认处理器
    logger.add(
        sys.stdout,
        format=config["logging"]["format"],
        level=config["logging"]["level"],
        colorize=True
    )
    
    return logger 