import time
from cv2 import log
from loguru import logger
from common import world
from common import app
from common.app import AppManager
from common.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config
from PIL import Image


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
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
        # 统一通过config访问所有配置
        self.fengmo_config = config.fengmo
        self.city_name = self.fengmo_config.city
        self.cities = config.fengmo_cities.get("cities", {})
        if self.city_name not in self.cities:
            raise ValueError(f"未找到城市配置: {self.city_name}")
        self.city_config = self.cities[self.city_name]
        self.depth = self.fengmo_config.depth
        self.rest_in_inn = self.fengmo_config.rest_in_inn

        
    def run(self) -> None:
        while True:
            self.app_manager.check_app_alive()
            self.world.rest_in_inn()
            self.world.go_fengmo(self.depth)
            time.sleep(1)
        