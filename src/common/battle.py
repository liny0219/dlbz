import time
from loguru import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Optional, Any, Tuple
from PIL import Image
from utils.singleton import singleton

@singleton
class Battle:
    """
    战斗模块
    负责实现战斗相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler,app_manager:AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler

    def in_battle(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在战斗中。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有6点
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗中")
            return False
        points_colors = [
            (116, 19, "87878C", 1),
            (125, 19, "878790", 1),
            (116, 29, "8F9096", 1),
            (125, 29, "8F8F98", 1),
            (131, 26, "9999A1", 1),
            (139, 26, "9A9BA3", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results):
            logger.info("检测到在战斗中")
            return True
        else:
            logger.info("不在战斗中")
            return False

    def in_battle_round(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在战斗回合中。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有6点
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗回合中")
            return False
        points_colors = [
            (1061,639, "FFFFFF", 1),
            (1061,639, "FFFFFF", 1),
            (1060,659, "FFFFFF", 1),
            (1133,650, "FFFFFF", 1),
            (1131,665, "FFFFFF", 1)
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results) and self.in_battle(image):
            logger.info("检测到在战斗回合中")
            return True
        else:
            logger.info("不在战斗回合中")
            return False

    def dead(self, image: Optional[Image.Image] = None, role_id: int = 1) -> bool:
        """
        判断当前是否死亡。
        :param image: 可选，外部传入截图
        :param role_id: 可选，角色id，默认0代表任意角色死亡判断,1-8代表具体角色死亡判断
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否死亡")
            return False
        # 1到8号角色血条检测
        points_colors = [
            (1100,84, "1A1A1A", 1),
            (1100,228, "1A1A1A", 1),
            (1100,370, "1A1A1A", 1),
            (1100,516, "1A1A1A", 1),
            (1200,86, "1A1A1A", 1),
            (1200,230, "1A1A1A", 1),
            (1200,372, "1A1A1A", 1),
            (1200,665, "1A1A1A", 1),
        ]
        if role_id == 0:
            # 任意角色死亡判断
            results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
            return any(results) and self.in_battle(image)
        else:
            # 具体角色死亡判断
            role_point = points_colors[role_id-1]
            return self.ocr_handler.match_point_color(image, role_point[0], role_point[1], role_point[2], role_point[3]) and self.in_battle(image)
    
    def in_skill(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在技能释放中。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (684,201, "E8EBF0", 1),
            (718,205, "E8EBF0", 1),
            (761,207, "272626", 1),
            (759,176, "1F1E1E", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        return all(results) and self.in_battle(image)

    def in_sp_skill(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在技能释放中。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (661,152, "F8F8FE", 1),
            (633,173, "E8E9EA", 1),
            (705,173, "E8E9EA", 1),
            (660,169, "F8F8FE", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        return all(results) and self.in_battle(image)
