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
    def __init__(self, device_manager: DeviceManager) -> None:
        self.device_manager = device_manager
        # 硬编码游戏包名，支持官服和B服
        self.app_packages = ['com.netease.ma167', 'com.netease.ma167.bilibili']
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
            running = current_app.get("package") in self.app_packages
            logger.debug(f"App当前包名: {current_app.get('package')}, 目标包名: {self.app_packages}, 运行状态: {running}")
            return running
        except Exception as e:
            logger.error(f"检查App运行状态失败: {e}\n{traceback.format_exc()}")
            return False

    def start_app(self) -> None:
        """
        启动游戏App，优先启动官服，失败则尝试B服
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法启动App")
                return
            
            if self.is_app_running():
                logger.info("游戏已在运行中")
                return
                
            # 尝试启动游戏，优先官服
            for package in self.app_packages:
                try:
                    self.device_manager.device.app_start(package)
                    logger.info(f"启动App成功: {package}")
                    return
                except Exception as e:
                    logger.warning(f"启动 {package} 失败: {e}")
                    continue
            
            logger.error("所有游戏包启动失败")
        except Exception as e:
            logger.error(f"启动App失败: {e}\n{traceback.format_exc()}")

    def close_app(self) -> None:
        """
        关闭游戏App
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法关闭App")
                return
                
            # 关闭所有可能运行的游戏包
            for package in self.app_packages:
                try:
                    self.device_manager.device.app_stop(package)
                    logger.info(f"关闭App: {package}")
                except Exception as e:
                    logger.debug(f"关闭 {package} 失败或未运行: {e}")
                    
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