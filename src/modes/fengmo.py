from enum import Enum
import time

from loguru import logger
from common.app import AppManager
from common.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config
from utils.sleep_utils import sleep_until


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
        step:Step = Step.FIGHT_BOSS
        while True:
            self.app_manager.check_app_alive()
            if self.rest_in_inn:
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth,self.entrance_pos)

            if step == Step.COLLECT_JUNK:
                step = self.do_collect_junk(step)
            if step == Step.FIND_BOX:
                step = self.do_find_box(step)
            if step == Step.FIGHT_BOSS:
                self.do_fight_boss()

    def do_collect_junk(self,step:Step):
        """
        一阶段捡垃圾
        """
        for check_point in self.check_points:
            while True:
                in_fengmo_map = sleep_until(self.world.in_world)
                if in_fengmo_map is None:
                    raise Exception("[do_collect_junk]等待逢魔地图失败")
                self.world.open_minimap()
                in_mini_map = sleep_until(self.world.in_minimap)
                if in_mini_map is None:
                    raise Exception("[do_collect_junk]等待小地图失败")
                self.device_manager.click(*check_point)
                in_fengmo_map = sleep_until(self.world.in_world)
                if in_fengmo_map is None:
                    raise Exception("[do_collect_junk]等待逢魔地图失败")
                point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                if point_pos is None:
                    # 没有找到点，进入下个check_point
                    break
                self.device_manager.click(*point_pos)
                try:
                    result = self.wait_found_result()
                    if result:
                        step = result
                        break
                except Exception as e:
                    raise Exception(f"[do_collect_junk]等待结果失败: {e}")
        return step

    def do_find_box(self,step:Step):
        """
        二阶段找宝箱
        """
        while True:
            in_fengmo_map = sleep_until(self.world.in_world)
            if in_fengmo_map is None:
                raise Exception("[do_find_box]等待逢魔地图失败")
            self.world.open_minimap()
            in_mini_map = sleep_until(self.world.in_minimap)
            if in_mini_map is None:
                raise Exception("[do_find_box]等待小地图失败")
            # 找宝箱
            find_map_treasure = sleep_until(self.world.find_map_treasure, self.find_minimap_wait_time)
            if find_map_treasure:
                self.device_manager.click(*find_map_treasure)
                self.wait_found_point_treasure()
                continue
            # 找怪物
            find_map_monster = sleep_until(self.world.find_map_monster, self.find_minimap_wait_time)
            if find_map_monster:
                self.device_manager.click(*find_map_monster)
                self.wait_found_point_monster()
                self.do_battle()
                continue
            # 找治疗点
            find_map_cure = sleep_until(self.world.find_map_cure, self.find_minimap_wait_time)
            if find_map_cure:
                self.device_manager.click(*find_map_cure)
                self.wait_found_cure()
                continue
            if self.check_found_boss():
                step = Step.FIGHT_BOSS
                break
            # 所有遍历完成,退出
        return step
    
    def do_fight_boss(self):
        """
        三阶段打Boss
        """
        in_fengmo_map = sleep_until(self.world.in_world)
        if in_fengmo_map is None:
            raise Exception("[do_fight_boss]等待逢魔地图失败")
        self.world.open_minimap()
        in_mini_map = sleep_until(self.world.in_minimap)
        if in_mini_map is None:
            raise Exception("[do_fight_boss]等待小地图失败")
        find_map_boss = sleep_until(self.world.find_map_boss, self.find_minimap_wait_time)
        if find_map_boss:
            self.device_manager.click(*find_map_boss)
        in_fengmo_map = sleep_until(self.world.in_world)
        if in_fengmo_map is None:
            raise Exception("[do_fight_boss]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[do_fight_boss]等待逢魔点失败")
        self.device_manager.click(*point_pos)
        self.wait_found_point_boss()
        self.do_battle()

    def do_battle(self):
        """
        战斗
        """
        # 检查等待战斗逻辑,先完成委托战斗,自定义战斗TODO
        is_auto_battle = False
        while True:
            time.sleep(1)
            if self.ocr_handler.match_click_text(["确定"],region=(516,571,769,644)):
                break
            if self.battle.in_battle():
                if is_auto_battle:
                    continue
                else:
                    if self.battle.auto_battle():
                        is_auto_battle = True
                    else:
                        raise Exception("[wait_found_point_boss]自动战斗失败")
            else:
                break

    def wait_found_point_boss(self):
        """
        等待找到Boss点
        """
        is_fengmo = sleep_until(self.world.in_world)
        if is_fengmo is None:
            raise Exception("[wait_found_point_boss]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_point_boss]等待逢魔点失败")
        self.device_manager.click(*point_pos)

        confirm_pos = sleep_until(lambda:self.ocr_handler.match_click_text(["是"],region=(257,168,1023,552)))
        if confirm_pos is None:
            raise Exception("[wait_found_point_boss]等待确认点失败")


    def wait_found_point_monster(self):
        """
        等待找到怪物点
        """
        is_fengmo = sleep_until(self.world.in_world)
        if is_fengmo is None:
            raise Exception("[wait_found_point_monster]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_point_monster]等待逢魔点失败")
        self.device_manager.click(*point_pos)

        # 检查等待战斗逻辑,先完成委托战斗,自定义战斗TODO
        is_auto_battle = False
        while True:
            time.sleep(1)
            if self.ocr_handler.match_click_text(["确定"],region=(516,571,769,644)):
                break
            if self.battle.in_battle():
                if is_auto_battle:
                    continue
                else:
                    if self.battle.auto_battle():
                        is_auto_battle = True
                    else:
                        raise Exception("[wait_found_point_boss]自动战斗失败")
            else:
                break

    # 检查是否出现Boss
    def check_found_boss(self):
        """
        检查是否出现Boss
        """
        region = (292,175,983,540)
        if self.ocr_handler.match_texts(["逢魔之主"],region=region):
            self.ocr_handler.match_click_text(["确定"],region=region)
            return True
        else:
            return False
    
    def wait_found_cure(self):
        """
        等待找到治疗点
        """
        is_fengmo = sleep_until(self.world.in_world)
        if is_fengmo is None:
            raise Exception("[wait_found_cure]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point_cure, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_cure]等待治疗点失败")
        self.device_manager.click(*point_pos)
        self.ocr_handler.match_click_text(["确定"],region=(381,223,897,489))
        time.sleep(1)
        self.world.click_tirm()
    
    def wait_found_point_treasure(self):
        """
        等待找到宝箱
        """
        in_fengmo = sleep_until(self.world.in_world)
        if in_fengmo is None:
            raise Exception("[wait_found_point_treasure]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point_treasure, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_point_treasure]等待宝箱点失败")
        self.device_manager.click(*point_pos)
        if self.wait_found_point_text("完全恢复",(381,223,897,489)):
            self.device_manager.click(643, 433)
            return True
        else:
            return False
        
    def wait_found_item(self):
        """
        等待获得道具提示
        """
        if self.wait_found_point_text("获得道具",(381,223,897,489)):
            self.device_manager.click(643, 433)
            return True
        else:
            return False
        
    def wait_found_point_text(self,text:str,region:tuple[int,int,int,int],interval=1.0,max_retry=30):
        """
        等待找到指定文本
        """
        retry = 0
        while retry < max_retry:
            results = self.ocr_handler.recognize_text(region=region)
            if results:
                for r in results:
                    if text in r['text']:
                        return True
            retry += 1
            time.sleep(interval)
        raise Exception(f"[wait_found_point_text]等待{text}失败")
    
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
        raise Exception("[wait_found_result]识别到错误结果")
    
    def exit_battle(self):
        """
        退出战斗
        """
        self.battle.exit_battle()
    
    def exit_fengmo(self,exit_pos:list[int], interval=1.0, max_retry=30):
        """
        退出逢魔
        """
        in_fengmo = sleep_until(self.world.in_world)
        if in_fengmo is None:
            raise Exception("[exit_fengmo]等待逢魔地图失败")
        self.world.open_minimap()
        in_minimap = sleep_until(self.world.in_minimap)
        if in_minimap is None:
            raise Exception("[exit_fengmo]等待小地图失败")
        self.device_manager.click(exit_pos[0],exit_pos[1])
        in_fengmo = sleep_until(self.world.in_world)
        if in_fengmo is None:
            raise Exception("[exit_fengmo]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point)
        if point_pos is None:
            raise Exception("[exit_fengmo]等待逢魔点失败")
        self.device_manager.click(*point_pos)
        retry = 0
        while retry < max_retry:
            text=self.ocr_handler.recognize_text(region=(381,223, 897,489))
            if text is None:
                time.sleep(1)
                continue
            for t in text:
                if "是否离开" in t['text']:
                    # self.device_manager.click(792,488)
                    logger.info("点击离开")
                    return
            retry += 1
            time.sleep(interval)
        raise Exception("[exit_fengmo]退出逢魔失败")
        