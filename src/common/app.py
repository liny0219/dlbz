from typing import Optional
from core.device_manager import DeviceManager
from utils import logger
from utils.singleton import singleton
from common.config import config
import traceback

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


    def get_app_package(self):
        if not self.device_manager.device:
            logger.error("设备未连接，无法检查App运行状态")
            return False
        current_app = self.device_manager.device.app_current()
        logger.info(f"当前App包名: {current_app.get('package')}")
        return current_app.get("package")

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
            logger.debug(f"App当前包名: {current_app.get('package')}, 目标包名: {self.app_package}, 运行状态: {running}")
            return running
        except Exception as e:
            logger.error(f"检查App运行状态失败: {e}\n{traceback.format_exc()}")
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
            if self.is_app_running():
                return
            self.device_manager.device.app_start(self.app_package)
            logger.info(f"启动App: {self.app_package}")
        except Exception as e:
            logger.error(f"启动App失败: {e}\n{traceback.format_exc()}")

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
            logger.error(f"关闭App失败: {e}\n{traceback.format_exc()}")

    def check_app_alive(self) -> bool:
        """
        检查App是否运行
        :return: bool 是否运行
        """
        if not self.is_app_running():
            logger.info("检查到App未运行.")
            return False
        return True 