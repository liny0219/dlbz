import time
import traceback
from typing import Optional
from common.app import AppManager
from utils import logger

def sleep(interval: float = 1.0, multiplier: float = 1.0) -> None:
    """
    通用sleep函数，支持倍数。
    """
    logger.debug(f"指令间隔sleep {interval*multiplier}秒 {multiplier}倍")
    time.sleep(interval*multiplier)
    logger.debug(f"指令间隔sleep {interval}秒")

def sleep_until(condition_func, timeout: float = 30.0, interval: float = 0.1, function_name: str = ""):
    """
    通用sleep_until函数，轮询等待条件。
    """
    logger.info(f"开始轮询等待条件，{condition_func.__name__} {function_name}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = condition_func()
        if result:
            logger.info(f"条件已满足，跳出等待{condition_func.__name__} {function_name} {result}")
            return result
        logger.debug("条件未满足，sleep...")
        time.sleep(interval)
    logger.info(f"等待超时，条件未满足:{condition_func.__name__} {function_name}")
    return None 

def sleep_until_app_running(condition_func, timeout: float = 30.0, 
                            interval: float = 0.1, function_name: str = "", 
                            app_manager: Optional[AppManager] = None, show_log = False):
    """
    通用sleep_until函数，轮询等待条件。
    """
    if show_log:
        logger.info(f"开始轮询等待条件，{condition_func.__name__} {function_name}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = condition_func()
        if result:
            logger.info(f"条件已满足，跳出等待{condition_func.__name__} {function_name} {result}")
            return result
        logger.debug("条件未满足，sleep...")
        time.sleep(interval)
        if app_manager is not None:
            if not app_manager.is_app_running():
                logger.debug("App未运行，跳出等待")
                return 'app_not_running'
    logger.info(f"等待超时，条件未满足:{condition_func.__name__} {function_name}")
    return None 
