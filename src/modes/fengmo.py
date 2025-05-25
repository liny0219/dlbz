from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time

from loguru import logger
from common.app import AppManager
from common.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config
from utils.sleep_utils import sleep_until

class Step(Enum):
    """
    逢魔流程阶段枚举
    - COLLECT_JUNK: 收集杂物阶段
    - FIND_BOX: 寻找宝箱/怪物/治疗点阶段
    - FIGHT_BOSS: 战斗Boss阶段
    """
    COLLECT_JUNK = 0
    FIND_BOX = 1
    FIGHT_BOSS = 2

@dataclass
class StateData:
    """
    逢魔流程状态数据
    step: 当前流程阶段
    done_treasure: 是否已完成宝箱
    done_monster: 是否已完成怪物
    done_cure: 是否已完成治疗点
    reset_count: 当前重置次数
    """
    step: Step = Step.COLLECT_JUNK
    done_treasure: bool = False
    done_monster: bool = False
    done_cure: bool = False
    reset_count: int = 0

class FengmoMode:
    """
    逢魔玩法模块
    负责实现逢魔相关的自动化逻辑，包括地图探索、宝箱/怪物/治疗点查找、Boss战等。
    依赖设备管理、OCR识别、世界与战斗模块。
    """

    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler) -> None:
        """
        初始化逢魔模式
        :param device_manager: 设备管理器，负责点击、操作等
        :param ocr_handler: OCR识别处理器
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
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
        self.backup_points = self.city_config.get("backup_points", [])
        self.reset_pos = self.city_config.get("reset_pos", [])
        self.find_point_wait_time = 3
        self.find_treasure_wait_time = 3
        self.find_minimap_wait_time = 3
        self.state_data = StateData()

    def run(self) -> None:
        """
        逢魔主循环入口，负责整体流程调度：
        1. 检查App存活
        2. 休息（如配置）
        3. 进入逢魔
        4. 按阶段依次执行收集、找宝箱/怪物/治疗点、Boss战
        """
        while True:
            self.app_manager.check_app_alive()
            self.state_data = StateData()
            if self.rest_in_inn:
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth, self.entrance_pos)
            while True:
                step = self.state_data.step
                if step == Step.COLLECT_JUNK:
                    self._collect_junk_phase()
                elif step == Step.FIND_BOX:
                    self._find_box_phase()
                elif step == Step.FIGHT_BOSS:
                    self._fight_boss_phase()
                    break
                else:
                    logger.error(f"[run]未知流程阶段: {step}")
                    break
                # 只要 step 被切换，循环会自动进入下一个阶段

    def _collect_junk_phase(self):
        """
        收集杂物阶段：遍历所有check_points，依次点击并查找逢魔点。
        若发现Boss则切换阶段，否则全部点位完成后进入FIND_BOX阶段。
        边界处理：如地图/小地图未进入，自动重试或抛异常。
        """
        self.state_data.step = Step.COLLECT_JUNK
        self.state_data.done_treasure = False
        self.state_data.done_monster = False
        self.state_data.done_cure = False
        self.state_data.reset_count = 0
        for check_point in self.check_points:
            while True:
                result = sleep_until(
                    lambda: "in_world" if self.world.in_world() else "found_boss" if self.check_found_boss() else None
                )
                if result is None:
                    if self.state_data.reset_count < 1:
                        self.device_manager.click(*self.reset_pos)
                        self.state_data.reset_count += 1
                        continue
                    raise Exception("[_collect_junk_phase]等待逢魔地图或Boss失败")
                if result == "found_boss":
                    self.state_data.step = Step.FIGHT_BOSS
                    return
                if result == "in_world":
                    self.world.open_minimap()
                in_mini_map = sleep_until(self.world.in_minimap)
                if in_mini_map is None:
                    raise Exception("[_collect_junk_phase]等待小地图失败")
                self.device_manager.click(check_point[0], check_point[1])
                in_fengmo_map = sleep_until(self.world.in_world)
                if in_fengmo_map is None:
                    raise Exception("[_collect_junk_phase]等待逢魔地图失败")
                next_point = False
                while True:
                    point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                    if not point_pos:
                        next_point = True
                        break
                    self.device_manager.click(*point_pos)
                    try:
                        state = self.wait_found_result()
                        self.state_data.reset_count = 0
                        if state != Step.COLLECT_JUNK:
                            self.state_data.step = state
                            return
                        if len(check_point) > 2 and check_point[2] == 1:
                            next_point = True
                            break
                    except Exception as e:
                        raise Exception(f"[_collect_junk_phase]等待结果失败: {e}")
                if self.state_data.step != Step.COLLECT_JUNK:
                    return
                if next_point:
                    break
        self.state_data.step = Step.FIND_BOX

    def _find_box_phase(self):
        """
        寻找宝箱/怪物/治疗点阶段：
        依次查找宝箱、怪物、治疗点，优先级依次递进。
        每找到一个即点击并等待对应流程完成，全部完成后自动退出。
        """
        self.state_data.step = Step.FIND_BOX
        self.state_data.reset_count = 0
        while True:
            result = sleep_until(
                lambda: "in_world" if self.world.in_world() else "found_boss" if self.check_found_boss() else None
            )
            if result is None:
                if self.state_data.reset_count < 1:
                    self.device_manager.click(*self.reset_pos)
                    self.state_data.reset_count += 1
                    continue
                raise Exception("[_find_box_phase]等待逢魔地图或Boss失败")
            if result == "found_boss":
                self.state_data.step = Step.FIGHT_BOSS
                return
            if result == "in_world":
                self.world.open_minimap()
            in_mini_map = sleep_until(self.world.in_minimap)
            if in_mini_map is None:
                raise Exception("[_find_box_phase]等待小地图失败")
            # 找宝箱
            if not self.state_data.done_treasure:
                find_map_treasure = sleep_until(self.world.find_map_treasure, self.find_minimap_wait_time)
                if find_map_treasure:
                    self.device_manager.click(*find_map_treasure)
                    self.wait_found_point_treasure()
                    self.state_data.reset_count = 0
                    continue
            # 找怪物
            if not self.state_data.done_monster:
                find_map_monster = sleep_until(self.world.find_map_monster, self.find_minimap_wait_time)
                if find_map_monster:
                    self.state_data.done_treasure = True
                    self.device_manager.click(*find_map_monster)
                    self.wait_found_point_monster()
                    self.do_battle()
                    self.state_data.done_monster = True
                    self.state_data.reset_count = 0
                    continue
            # 找治疗点
            if not self.state_data.done_cure:
                find_map_cure = sleep_until(self.world.find_map_cure, self.find_minimap_wait_time)
                if find_map_cure:
                    self.state_data.done_treasure = True
                    self.state_data.done_monster = True
                    self.device_manager.click(*find_map_cure)
                    self.wait_found_cure()
                    self.state_data.done_cure = True
                    self.state_data.reset_count = 0
                    continue

    def _fight_boss_phase(self):
        """
        Boss战阶段：
        进入逢魔地图，打开小地图，查找Boss点并点击，等待Boss点确认，进入战斗。
        边界处理：如Boss点未找到、地图未进入等，抛出异常。
        """
        self.state_data.step = Step.FIGHT_BOSS
        in_fengmo_map = sleep_until(self.world.in_world)
        if in_fengmo_map is None:
            raise Exception("[_fight_boss_phase]等待逢魔地图失败")
        self.world.open_minimap()
        in_mini_map = sleep_until(self.world.in_minimap)
        if in_mini_map is None:
            raise Exception("[_fight_boss_phase]等待小地图失败")
        find_map_boss = sleep_until(self.world.find_map_boss, self.find_minimap_wait_time)
        if find_map_boss:
            self.device_manager.click(*find_map_boss)
        in_fengmo_map = sleep_until(self.world.in_world)
        if in_fengmo_map is None:
            raise Exception("[_fight_boss_phase]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[_fight_boss_phase]等待逢魔点失败")
        self.device_manager.click(*point_pos)
        self.wait_found_point_boss()
        self.do_battle()

    def wait_found_result(self, interval=1.0, max_retry=30)->Step:
        """
        逢魔专用：等待识别到"获得道具"或"已发现所有的逢魔之影"，自动处理战斗等待，返回三种状态。
        :param interval: 识别间隔秒数
        :param max_retry: 最大重试次数，防止死循环
        :return: Step.COLLECT_JUNK/Step.FIND_BOX/Step.FIGHT_BOSS
        边界处理：超时未识别到目标文本抛异常。
        """
        region = (381, 223, 897, 489)
        retry = 0
        while retry < max_retry:
            # 检查是否在战斗中
            if self.battle.in_battle():
                self.do_battle()
                self.state_data.done_monster = True
                return Step.COLLECT_JUNK
            # 非战斗中，识别文本
            results = self.ocr_handler.recognize_text(region=region)
            if not results:
                retry += 1
                time.sleep(interval)
                continue
            for r in results:
                if "获得道具" in r['text']:
                    self.device_manager.click(640, 430)
                    return Step.COLLECT_JUNK
                if "已发现所有的逢魔之影" in r['text']:
                    self.device_manager.click(640,480)
                    if sleep_until(self.check_found_boss,timeout=3):
                        return Step.FIGHT_BOSS
                    return Step.FIND_BOX
                if "完全恢复了" in r['text']:
                    self.device_manager.click(640,480)
                    time.sleep(1)
                    self.state_data.done_cure = True
                    self.world.click_tirm()
                    return Step.COLLECT_JUNK
            retry += 1
            time.sleep(interval)
        raise Exception("[wait_found_result]识别到错误结果")

    def do_battle(self):
        """
        战斗流程：
        1. 检查是否进入战斗
        2. 自动战斗（如支持）
        3. 检查结算与确认，自动点击
        边界处理：自动战斗失败抛异常。
        """
        is_auto_battle = False
        while True:
            time.sleep(1)
            if self.battle.in_battle():
                if is_auto_battle:
                    continue
                if self.battle.auto_battle():
                    is_auto_battle = True
                else:
                    raise Exception("[wait_found_point_boss]自动战斗失败")
            if self.ocr_handler.match_texts(["战斗结算"]):
                self.world.click_tirm()
            if self.ocr_handler.match_click_text(["确定"],region=(516,571,769,644)):
                break

    def wait_found_point_boss(self):
        """
        等待找到Boss点，点击并确认。
        边界处理：Boss点/确认点未找到抛异常。
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
        # 检查是否出现Boss
  
    def check_found_boss(self):
        """
        检查是否出现Boss
        :return: True-发现Boss，False-未发现
        """
        region = (292,175,983,540)
        if self.ocr_handler.match_texts(["逢魔之主"],region=region):
            self.ocr_handler.match_click_text(["确定"],region=region)
            return True
        else:
            return False

    def wait_found_point_monster(self):
        """
        等待找到怪物点，点击进入。
        边界处理：怪物点未找到抛异常。
        """
        is_fengmo = sleep_until(self.world.in_world)
        if is_fengmo is None:
            raise Exception("[wait_found_point_monster]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_point_monster]等待逢魔点失败")
        self.device_manager.click(*point_pos)
    
    def wait_found_cure(self):
        """
        等待找到治疗点，点击进入并确认。
        边界处理：治疗点未找到抛异常。
        """
        is_fengmo = sleep_until(self.world.in_world)
        if is_fengmo is None:
            raise Exception("[wait_found_cure]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point_cure, self.find_point_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_cure]等待治疗点失败")
        self.device_manager.click(*point_pos)
        sleep_until(lambda:self.ocr_handler.match_click_text(["确定"],region=(381,223,897,489)))
        self.world.click_tirm()
    
    def wait_found_point_treasure(self):
        """
        等待找到宝箱点，点击并等待获得道具。
        边界处理：宝箱点未找到抛异常。
        :return: True-获得道具，False-未获得
        """
        in_fengmo = sleep_until(self.world.in_world)
        if in_fengmo is None:
            raise Exception("[wait_found_point_treasure]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point_treasure,timeout=self.find_treasure_wait_time,interval=0.1)
        if point_pos is not None:
            self.device_manager.click(*point_pos)
        else:
            logger.info("[wait_found_point_treasure]等待宝箱点失败")
            for point in self.backup_points:
                self.device_manager.click(point[0],point[1])
        return self.wait_found_item()
        
    def wait_found_item(self):
        """
        等待获得道具提示，点击确认。
        :return: True-获得道具，False-未获得
        """
        if self.wait_found_point_text("获得道具",(381,223,897,489)):
            self.device_manager.click(643, 433)
            return True
        else:
            return False
        
    def wait_found_point_text(self,text:str,region:tuple[int,int,int,int],interval=1.0,max_retry=30):
        """
        等待找到指定文本
        :param text: 目标文本
        :param region: 识别区域
        :param interval: 识别间隔
        :param max_retry: 最大重试次数
        :return: True-找到，False-未找到
        边界处理：超时未找到抛异常。
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
       
    def exit_battle(self):
        """
        退出战斗，调用Battle模块接口。
        """
        self.battle.exit_battle()
    
    def exit_fengmo(self,exit_pos:list[int], interval=1.0, max_retry=30):
        """
        退出逢魔地图流程：
        1. 打开小地图，点击出口
        2. 等待逢魔点，点击
        3. 检查是否弹出离开确认
        :param exit_pos: 出口坐标
        :param interval: 识别间隔
        :param max_retry: 最大重试次数
        边界处理：超时未弹出确认抛异常。
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
        