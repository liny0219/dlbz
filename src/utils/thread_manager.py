import threading
import time
from typing import Dict, Any, Optional

class ManagedThread:
    """
    支持父子线程嵌套的线程管理类
    - 支持共享数据
    - 支持优雅关闭
    - 支持在任意线程中启动子线程，并绑定生命周期
    """
    def __init__(self, target, shared_data, use_lock=False):
        """
        :param target: 线程函数，签名为 func(shared_data, stop_event, lock)
        :param shared_data: 共享数据
        :param use_lock: 是否加锁
        """
        self.shared_data = shared_data
        self.stop_event = threading.Event()
        self.lock = threading.Lock() if use_lock else None
        self.thread = threading.Thread(
            target=target,
            args=(self.shared_data, self.stop_event, self.lock)
        )

    def start(self):
        """启动线程"""
        self.thread.start()

    def stop(self):
        """通知线程退出并等待结束"""
        self.stop_event.set()
        self.thread.join(timeout=2)

    def is_alive(self):
        """判断线程是否存活"""
        return self.thread.is_alive()

def app_alive_monitor_func(shared: Dict[str, Any], stop_event: threading.Event, lock: Optional[threading.Lock] = None) -> None:
    """
    App存活检测线程函数
    :param shared: 共享数据字典，必须包含 'app_manager' (有check_app_alive/start_app方法) 和 'state_data' (有app_alive属性)
    :param stop_event: 线程关闭信号
    :param lock: 可选锁（本函数未用到）
    """
    app_manager = shared['app_manager']
    state_data = shared['state_data']
    check_interval = shared.get('check_interval', 3)  # 检查间隔秒数
    restart_wait = shared.get('restart_wait', 5)      # 重启后等待秒数
    logger = shared.get('logger', None)
    while not stop_event.is_set():
        app_alive = app_manager.check_app_alive()
        if not app_alive:
            if logger:
                logger.info("检测到App未运行,尝试重启")
            app_manager.start_app()
            time.sleep(restart_wait)
        state_data.app_alive = app_alive
        time.sleep(check_interval) 