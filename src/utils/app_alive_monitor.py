import time
import threading
from typing import Dict, Any, Optional

def app_alive_monitor_func(shared: Dict[str, Any], stop_event: threading.Event, lock: Optional[threading.Lock] = None) -> None:
    """
    App存活检测线程函数
    可配合ManagedThread使用，实现App自动存活检测与重启。
    :param shared: 共享数据字典，必须包含 'app_manager' (有check_app_alive/start_app方法) 和 'state_data' (有app_alive属性)
        可选: 'logger' 日志对象, 'check_interval' 检查间隔秒数, 'restart_wait' 重启后等待秒数
    :param stop_event: 线程关闭信号
    :param lock: 可选锁（本函数未用到）
    """
    app_manager = shared['app_manager']
    state_data = shared['state_data']
    check_interval = shared.get('check_interval', 3)  # 检查间隔秒数
    restart_wait = shared.get('restart_wait', 5)      # 重启后等待秒数
    logger = shared.get('logger', None)
    while not stop_event.is_set():
        logger.debug("检查App存活状态")
        app_alive = app_manager.check_app_alive()
        if not app_alive:
            if logger:
                logger.info("检测到App未运行,尝试重启")
            app_manager.start_app()
            time.sleep(restart_wait)
        state_data.app_alive = app_alive
        time.sleep(check_interval) 