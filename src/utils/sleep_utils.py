import time
from loguru import logger

def sleep(interval: float = 1.0, multiplier: float = 1.0) -> None:
    """
    通用sleep函数，支持倍数。
    """
    logger.debug(f"指令间隔sleep {interval*multiplier}秒 {multiplier}倍")
    time.sleep(interval*multiplier)
    logger.debug(f"指令间隔sleep {interval}秒")

def sleep_until(condition_func, timeout: float = 30.0, interval: float = 1.0):
    """
    通用sleep_until函数，轮询等待条件。
    """
    logger.debug(f"开始轮询等待条件，最大超时{timeout}秒，每次间隔{interval}秒")
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = condition_func()
        if result:
            logger.debug("条件已满足，跳出等待")
            return result
        logger.debug("条件未满足，sleep...")
        time.sleep(interval)
    logger.debug(f"等待超时，条件未满足:{condition_func.__name__}")
    return None 
