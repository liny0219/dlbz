import time
from tracemalloc import start
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
        # 从配置中读取游戏包名，支持官服和B服
        self.app_packages = ['com.netease.ma167', 'com.netease.ma167.bilibili']
        self.current_package = None
        self._initialized = True
        # 从配置中更新app_packages
        self._update_app_packages_from_config()

    def _update_app_packages_from_config(self):
        """
        从配置中更新app_packages列表
        """
        try:
            configured_package = config.device.app_packages
            if configured_package:
                # 如果配置的包名在支持的包名列表中，将其设为优先
                if configured_package in self.app_packages:
                    # 重新排序，将配置的包名放在第一位
                    self.app_packages = [configured_package] + [pkg for pkg in self.app_packages if pkg != configured_package]
                    logger.info(f"从配置中读取到app_packages: {configured_package}")
                else:
                    logger.warning(f"配置的app_packages {configured_package} 不在支持的包名列表中")
        except Exception as e:
            logger.error(f"从配置中读取app_packages失败: {e}")

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
            current_package = current_app.get("package")
            if self.current_package:
                if current_package == self.current_package:
                    return True
                else:
                    self.current_package = None
            for package in self.app_packages:
                if current_package == package:
                    self.current_package = package
                    logger.debug(f"App当前包名: {current_app.get('package')}, 目标包名: {self.app_packages}, 运行状态: {True}")
                    return True
            return False
        except Exception as e:
            logger.error(f"检查App运行状态失败: {e}\n{traceback.format_exc()}")
            return False

    def start_app(self,show_log:bool=False) -> None:
        """
        启动游戏App，优先启动配置中指定的服务器
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法启动App")
                return
            
            if self.is_app_running():
                if show_log:
                    logger.info("游戏已在运行中")
                return
            
            if self.current_package:
                self.device_manager.device.app_start(self.current_package)
                if show_log:
                    logger.info(f"启动App成功: {self.current_package}")
                time.sleep(3)
                return
            
            # 尝试启动游戏，优先配置中指定的服务器
            for package in self.app_packages:
                try:
                    self.device_manager.device.app_start(package)
                    if show_log:
                        logger.info(f"启动App成功: {package}")
                except Exception as e:
                    logger.info(f"启动 {package} 失败: {e}")
                    continue
            time.sleep(3)
        except Exception as e:
            logger.info(f"启动App失败: {e}\n{traceback.format_exc()}")

    def close_app(self,show_log:bool=False) -> None:
        """
        关闭游戏App
        """
        try:
            if not self.device_manager.device:
                logger.error("设备未连接，无法关闭App")
                return
            if self.current_package:
                self.device_manager.device.app_stop(self.current_package)
                if show_log:
                    logger.info(f"关闭App成功: {self.current_package}")
                return
            # 关闭所有可能运行的游戏包
            for package in self.app_packages:
                try:
                    self.device_manager.device.app_stop(package)
                    if show_log:
                        logger.info(f"关闭App: {package}")
                except Exception as e:
                    logger.debug(f"关闭 {package} 失败或未运行: {e}")
                    
        except Exception as e:
            logger.error(f"关闭App失败: {e}\n{traceback.format_exc()}")

    def restart_app(self) -> None:
        self.close_app()
        time.sleep(1)
        self.start_app()

    def check_app_alive(self) -> bool:
        """
        检查App是否运行
        :return: bool 是否运行
        """
        if not self.is_app_running():
            logger.info("检查到App未运行.")
            return False
        return True 