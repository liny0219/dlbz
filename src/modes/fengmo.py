from enum import Enum
import time

from loguru import logger
from common.app import AppManager
from common.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config
from PIL import Image


# 逢魔的流程枚举
class Step(Enum):
    """
    逢魔流程枚举
    """
    # 捡垃圾
    COLLECT_JUNK = 0 
    # 找宝箱(所有宝箱显形)
    FIND_BOX = 1
    # 打Boss
    FIGHT_BOSS = 2

class State(Enum):
    """
    逢魔状态枚举
    """
    # 异常
    ERROR = 0
    # 正常
    NORMAL = 1



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
        self.depth = self.fengmo_config.depth
        self.rest_in_inn = self.fengmo_config.rest_in_inn

        fengmo_cities = config.fengmo_cities
        if self.city_name not in fengmo_cities:
            raise ValueError(f"未找到城市配置: {self.city_name}")
        self.city_config = fengmo_cities[self.city_name]

        self.inn_pos = self.city_config.get("inn_pos", [])
        self.entrance_pos = self.city_config.get("entrance_pos", [])
        self.check_points = self.city_config.get("check_points", [])
        self.find_point_wait_time = 3
        self.find_treasure_wait_time = 3
        self.find_minimap_wait_time = 3

    def run(self) -> None:
        step:Step = Step.COLLECT_JUNK
        state:State = State.NORMAL
        while True:
            self.exit_fengmo(self.entrance_pos)
            return
            self.app_manager.check_app_alive()
            if self.rest_in_inn:
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth,self.entrance_pos)

            for check_point in self.check_points:
                while True:
                    in_fengmo = self.app_manager.sleep_until(self.world.in_world)
                    if in_fengmo is None:
                        state = State.ERROR
                        break
                    self.world.open_minimap()
                    in_mini_map = self.app_manager.sleep_until(self.world.in_minimap)
                    if in_mini_map is None:
                        state = State.ERROR
                        break
                    self.device_manager.click(*check_point)
                    in_fengmo = self.app_manager.sleep_until(self.world.in_world)
                    if in_fengmo is None:
                        state = State.ERROR
                        break
                    point_pos = self.app_manager.sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                    if point_pos is None:
                        break
                    self.device_manager.click(*point_pos)
                    try:
                        result = self.wait_found_result()
                        if result:
                            step = result
                    except Exception as e:
                        state = State.ERROR
                        break
                if state == State.ERROR:
                    break
            if step == Step.FIND_BOX:
                while True:
                    in_fengmo = self.app_manager.sleep_until(self.world.in_world)
                    if in_fengmo is None:
                        state = State.ERROR
                        break
                    self.world.open_minimap()
                    in_mini_map = self.app_manager.sleep_until(self.world.in_minimap)
                    if in_mini_map is None:
                        state = State.ERROR
                        break
                    is_find = False
                    if not is_find:
                        # 找宝箱
                        find_map_treasure = self.app_manager.sleep_until(self.world.find_map_treasure, self.find_minimap_wait_time)
                        if find_map_treasure:
                            self.device_manager.click(*find_map_treasure)
                            is_find = True
                    if not is_find:
                        # 找Boss
                        find_map_boss = self.app_manager.sleep_until(self.world.find_map_boss, self.find_minimap_wait_time)
                        if find_map_boss:
                            self.device_manager.click(*find_map_boss)
                            is_find = True  
                    if not is_find:
                        # 找治疗点
                        find_map_cure = self.app_manager.sleep_until(self.world.find_map_cure, self.find_minimap_wait_time)
                        if find_map_cure:
                            self.device_manager.click(*find_map_cure)
                            is_find = True
                    if is_find:
                        try:
                            result = self.wait_found_result()
                            if result:
                                step = result
                        except Exception as e:
                            state = State.ERROR
                            break
                    time.sleep(1)

    def wait_found_result(self, interval=1.0, max_retry=30):
            """
            逢魔专用：等待识别到"获得道具"或"已发现所有的逢魔之影"，自动处理战斗等待，返回三种状态。
            :param interval: 识别间隔秒数
            :param max_retry: 最大重试次数，防止死循环
            :return: "error" | "normal" | "step"
            """
            region = (381, 223, 897, 489)
            retry = 0
            is_battle = False
            while retry < max_retry:
                # 检查是否在战斗中
                if self.battle.in_battle():
                    is_battle = True
                    time.sleep(interval)
                    continue
                # 战斗刚结束，重置标志
                if is_battle:
                    is_battle = False
                    return
                # 非战斗中，识别文本
                results = self.ocr_handler.recognize_text(region=region)
                if not results:
                    retry += 1
                    time.sleep(interval)
                    continue
                for r in results:
                    if "获得道具" in r['text']:
                        self.device_manager.click(643, 433)
                        return
                    if "已发现所有的逢魔之影" in r['text']:
                        return Step.FIND_BOX
                retry += 1
                time.sleep(interval)
            raise Exception("识别到错误结果")
    
    def exit_fengmo(self,exit_pos:list[int]):
        """
        退出逢魔
        """
        in_fengmo = self.app_manager.sleep_until(self.world.in_world)
        if in_fengmo is None:
            return
        self.world.open_minimap()
        in_minimap = self.app_manager.sleep_until(self.world.in_minimap)
        if in_minimap is None:
            return
        self.device_manager.click(exit_pos[0],exit_pos[1])
        in_fengmo = self.app_manager.sleep_until(self.world.in_world)
        if in_fengmo is None:
            return
        point_pos = self.app_manager.sleep_until(self.world.find_fengmo_point)
        if point_pos is None:
            return
        self.device_manager.click(*point_pos)
        while True:
            text=self.ocr_handler.recognize_text(region=(381,223, 897,489))
            if text is None:
                time.sleep(1)
                continue
            for t in text:
                if "是否离开" in t['text']:
                    # self.device_manager.click(792,488)
                    logger.info("点击离开")
                    return
            time.sleep(1)
        