from loguru import logger
import yaml
from typing import Optional
from core.device_manager import DeviceManager
import time
from utils.singleton import singleton
from common.config import config

@singleton
class AppManager:
    """
    游戏App管理器，提供启动、关闭、检测运行状态等功能
    """
    def __init__(self, device_manager: DeviceManager, app_package: Optional[str] = None) -> None:
        self.device_manager = device_manager
        if app_package is None:
            app_package = config.game.package_name
        self.app_package = app_package
        self._initialized = True

    def is_app_running(self) -> bool:
        """
        检查App是否正在运行
        :return: bool
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法检查App运行状态")
                return False
            current_app = self.device_manager.device.app_current()
            running = current_app.get("package") == self.app_package
            logger.info(f"App当前包名: {current_app.get('package')}, 目标包名: {self.app_package}, 运行状态: {running}")
            return running
        except Exception as e:
            logger.error(f"检查App运行状态失败: {e}")
            return False

    def start_app(self) -> None:
        """
        启动App
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法启动App")
                return
            if not self.app_package:
                logger.error("app_package未设置，无法启动App")
                return
            self.device_manager.device.app_start(self.app_package)
            logger.info(f"启动App: {self.app_package}")
        except Exception as e:
            logger.error(f"启动App失败: {e}")

    def close_app(self) -> None:
        """
        关闭App
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法关闭App")
                return
            if not self.app_package:
                logger.error("app_package未设置，无法关闭App")
                return
            self.device_manager.device.app_stop(self.app_package)
            logger.info(f"关闭App: {self.app_package}")
        except Exception as e:
            logger.error(f"关闭App失败: {e}")

    def check_app_alive(self) -> bool:
        """
        检查App是否运行，未运行则自动启动
        :return: bool 启动后是否运行
        """
        if not self.is_app_running():
            logger.info("App未运行，尝试自动启动...")
            self.start_app()
            return self.is_app_running()
        return True

    def sleep(self, multiplier: float = 1.0) -> None:
        interval = config.command_interval
        logger.info(f"指令间隔sleep {interval*multiplier}秒 {multiplier}倍")
        time.sleep(interval*multiplier)
        logger.info(f"指令间隔sleep {interval}秒")

    def sleep_until(self, condition_func, timeout: float = 30.0, interval: Optional[float] = None):
        if interval is None:
            interval = config.command_interval
        if interval is None:
            interval = 1.0
        logger.info(f"开始轮询等待条件，最大超时{timeout}秒，每次间隔{interval}秒")
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = condition_func()
            if result:
                logger.info("条件已满足，跳出等待")
                return result
            logger.info("条件未满足，sleep...")
            time.sleep(float(interval))
        logger.warning("等待超时，条件未满足")
        return None 