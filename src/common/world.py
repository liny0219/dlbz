import time
from loguru import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Optional, Any, Tuple
from PIL import Image
from utils.singleton import singleton

@singleton
class WorldMode:
    """
    世界地图玩法模块
    负责实现世界地图相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler,app_manager:AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler

    def in_world(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在城镇主界面且人物停止移动。
        通过检测左下角菜单的两个点颜色判断。
        :param image: 可选，外部传入截图
        :return: bool，是否在世界中
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在世界中")
            return False
        # 检查左下角菜单的两个点颜色
        cond1 = self.ocr_handler.match_point_color(image, 73,632, "E8EBF0", 1)
        cond2 = self.ocr_handler.match_point_color(image, 68,575, "F6F5F6", 1)
        if cond1 and cond2:
            logger.info("检测到在世界中")
            return True
        else:
            logger.info("不在世界中")
            return False

    def in_minimap(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在小地图中。
        通过检测地图界面两个关键点的颜色判断。
        :param image: 可选，外部传入截图
        :return: bool，是否在地图中
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在地图中")
            return False
        cond1 = self.ocr_handler.match_point_color(image, 33,638,[255, 254, 255], 1)
        cond2 = self.ocr_handler.match_point_color(image, 64,649,[255, 254, 255], 1)
        cond3 = self.ocr_handler.match_point_color(image, 452,676,[251, 249, 254], 1)
        if cond1 and cond2 and cond3:
            logger.info("检测到在小地图中")
            return True
        else:
            logger.info("不在小地图中")
            return False
        
    def in_inn(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆中。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_bed.png")
        if find:
            logger.info("检测到在旅馆中")
            return find
        else:
            logger.info("不在旅馆中")
            return None
    
    def find_inn_door(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆门口。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_door.png")
        if find:
            logger.info("检测到在旅馆门口")
            return find
        else:
            logger.info("不在旅馆门口")
            return None
        
    def find_fengmo_point(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在逢魔入口。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/fengmo_point.png")
        if find:
            logger.info("检测到在逢魔入口")
            return find
        else:
            logger.info("不在逢魔入口")
            return None

    def open_minimap(self):
        """
        打开小地图
        """
        self.device_manager.click(1060,100)

    def go_newdelsta_inn(self):
        """
        前往新德尔斯塔旅馆
        """
        self.device_manager.click(645,573)

    def go_newdelsta_fengmo_entrance(self):
        """
        前往新德尔斯塔风魔入口
        """
        self.device_manager.click(337,596)

    def click_tirm(self,count: int = 1,interval: float = 0.1) -> None:
        """
        点击跳过按钮，count次
        """
        for _ in range(count):
            logger.info("点击跳过按钮")
            self.device_manager.click(1100,680)
            time.sleep(interval)
        
    def rest_in_inn(self) -> None:
        """
        自动完成旅馆休息流程：
        1. 判断是否在城镇，打开小地图
        2. 进入旅馆
        3. 点击旅馆老板，等待欢迎光临
        4. 跳过对话，点击"是"
        5. 等待精力完全恢复
        6. 返回城镇，打开小地图
        7. 查找旅馆门口并点击
        :param app_manager: AppManager实例
        :param ocr_handler: OCRHandler实例
        """
        in_world = self.app_manager.sleep_until(self.in_world)
        if not in_world:
            logger.info("不在城镇中")
            return
        self.open_minimap()
        in_minimap = self.app_manager.sleep_until(self.in_minimap)
        if not in_minimap:
            return
        self.go_newdelsta_inn()
        in_inn = self.app_manager.sleep_until(self.in_inn)
        if not in_inn:
            return
        logger.info("点击旅馆老板")
        self.device_manager.click(*in_inn)
        logger.info("等待欢迎光临")
        self.app_manager.sleep_until(lambda: self.ocr_handler.match_click_text(["欢迎光临"]))
        logger.info("点击跳过")
        self.click_tirm(3)
        logger.info("点击是")
        self.app_manager.sleep_until(lambda: self.ocr_handler.match_click_text(["是"]))
        logger.info("等待完全恢复")
        self.app_manager.sleep_until(lambda: self.ocr_handler.match_click_text(["精力完全恢复了"]))
        logger.info("等待返回城镇")
        self.app_manager.sleep_until(self.in_world)
        logger.info("打开小地图")
        self.open_minimap()
        logger.info("等待小地图")
        in_minimap = self.app_manager.sleep_until(self.in_minimap)
        if not in_minimap:
            return
        logger.info("查找旅馆门口")
        door_pos = self.find_inn_door()
        if not door_pos:
            return
        logger.info("点击旅馆门口")
        self.device_manager.click(*door_pos)
        

    def go_fengmo(self):
        """
        前往逢魔
        """
        in_world = self.app_manager.sleep_until(self.in_world)
        if not in_world:
            logger.info("不在城镇中")
            return
        self.open_minimap()
        in_minimap = self.app_manager.sleep_until(self.in_minimap)
        if not in_minimap:
            return
        # 点击地图逢魔入口
        self.go_newdelsta_fengmo_entrance()
        # 寻找逢魔入口
        fengmo_pos = self.app_manager.sleep_until(self.find_fengmo_point)
        # 点击停止移动
        if not fengmo_pos:
            return
        self.click_tirm(2)
        # 再次确认寻找逢魔入口
        fengmo_pos = self.app_manager.sleep_until(self.find_fengmo_point)
        if not fengmo_pos:
            return
        # 点击逢魔入口
        self.device_manager.click(*fengmo_pos)
        # 选择深度
        self.app_manager.sleep_until(lambda: self.ocr_handler.match_texts(["选择深度"]))
        # 涉入
        self.app_manager.sleep_until(lambda: self.ocr_handler.match_click_text(["涉入"],region=(760,465,835,499)))