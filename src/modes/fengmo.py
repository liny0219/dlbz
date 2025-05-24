import time
from loguru import logger
from common import world
from common import app
from common.app import AppManager
from common.world import WorldMode
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config
import yaml


class FengmoMode:
    """
    逢魔玩法模块
    负责实现逢魔相关的自动化逻辑
    """

    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.app_manager = AppManager(device_manager)
        self.world_mode = WorldMode(device_manager, ocr_handler, self.app_manager)
        # 统一通过config访问所有配置
        self.fengmo_config = config.fengmo
        city_name = self.fengmo_config.get("city", "newdelsta")
        cities = config.fengmo_cities.get("cities", {})
        if not isinstance(cities, dict):
            raise ValueError("配置文件格式错误，cities不是dict")
        if city_name not in cities:
            raise ValueError(f"未找到城市配置: {city_name}")
        self.city_config = cities[city_name]

    def run(self) -> None:
        self.app_manager.check_app_alive()
        time.sleep(2)
        # self.world_mode.rest_in_inn()
        self.world_mode.go_fengmo()