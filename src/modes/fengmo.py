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
        self.find_treasure_wait_time = 8
        self.find_minimap_wait_time = 3

    def run(self) -> None:
        while True:
            self.app_manager.check_app_alive()
            if self.rest_in_inn:
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth,self.entrance_pos)
            step:Step = Step.COLLECT_JUNK
            done_treasure = False
            done_monster = False
            done_cure = False
            if step == Step.COLLECT_JUNK:
                step,done_treasure,done_monster,done_cure = self.do_collect_junk()
            if step == Step.FIND_BOX:
                step = self.do_find_box(done_treasure,done_monster,done_cure)
            if step == Step.FIGHT_BOSS:
                self.do_fight_boss()

    def do_collect_junk(self):
        """
        一阶段捡垃圾
        """
        step = Step.COLLECT_JUNK
        done_treasure = False
        done_monster = False
        done_cure = False
        for check_point in self.check_points:
            while True:
                result = sleep_until(
                    lambda: ("in_world") if self.world.in_world() else ("found_boss") if self.check_found_boss() else None
                )
                if result is None:
                    raise Exception("[do_find_box]等待逢魔地图或Boss失败")
                if result == "found_boss":
                    step = Step.FIGHT_BOSS
                    return step,done_treasure,done_monster,done_cure
                if result == "in_world":
                    self.world.open_minimap()
                in_mini_map = sleep_until(self.world.in_minimap)
                if in_mini_map is None:
                    raise Exception("[do_collect_junk]等待小地图失败")
                self.device_manager.click(check_point[0],check_point[1])
                in_fengmo_map = sleep_until(self.world.in_world)
                if in_fengmo_map is None:
                    raise Exception("[do_collect_junk]等待逢魔地图失败")
                next_point = False
                # 多个逢魔点连续点击
                while True:
                    # 判断是否存在多个逢魔点
                    point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                    if not point_pos:
                        # 没有找到点，进入下个check_point
                        next_point = True
                        break
                    self.device_manager.click(*point_pos)
                    try:
                        result,state = self.wait_found_result()
                        if state == "done_monster":
                            done_monster = True
                        if state == "done_cure":
                            done_cure = True
                        if result != Step.COLLECT_JUNK:
                            step = result
                            break
                        # 如果check_point[2]为1，则不连续找点,进入下个check_point,避免跟入口点混淆以及一些特殊点无法点击
                        if check_point[2] == 1:
                            next_point = True
                            break 
                    except Exception as e:
                        raise Exception(f"[do_collect_junk]等待结果失败: {e}")
                if step != Step.COLLECT_JUNK:
                    return step,done_treasure,done_monster,done_cure
                if next_point:
                    break
        return Step.COLLECT_JUNK,done_treasure,done_monster,done_cure

    def do_find_box(self,done_treasure:bool,done_monster:bool,done_cure:bool):
        step = Step.FIND_BOX
        """
        二阶段找宝箱
        """
        while True:
            result = sleep_until(
                lambda: ("in_world") if self.world.in_world() else ("found_boss") if self.check_found_boss() else None
            )
            if result is None:
                raise Exception("[do_find_box]等待逢魔地图或Boss失败")
            if result == "found_boss":
                step = Step.FIGHT_BOSS
                return step
            if result == "in_world":
                self.world.open_minimap()
            in_mini_map = sleep_until(self.world.in_minimap)
            if in_mini_map is None:
                raise Exception("[do_find_box]等待小地图失败")
            # 找宝箱
            if not done_treasure:
                find_map_treasure = sleep_until(self.world.find_map_treasure, self.find_minimap_wait_time)
                if find_map_treasure:
                    self.device_manager.click(*find_map_treasure)
                    self.wait_found_point_treasure()
                    continue
            # 找怪物
            if not done_monster:
                find_map_monster = sleep_until(self.world.find_map_monster, self.find_minimap_wait_time)
                if find_map_monster:
                    done_treasure = True
                    self.device_manager.click(*find_map_monster)
                    self.wait_found_point_monster()
                    self.do_battle()
                    done_monster = True
                    continue
            # 找治疗点
            if not done_cure:
                find_map_cure = sleep_until(self.world.find_map_cure, self.find_minimap_wait_time)
                if find_map_cure:
                    done_treasure = True
                    done_monster = True
                    self.device_manager.click(*find_map_cure)
                    self.wait_found_cure()
                    done_cure = True
                    continue
    
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
        sleep_until(lambda:self.ocr_handler.match_click_text(["确定"],region=(381,223,897,489)))
        self.world.click_tirm()
    
    def wait_found_point_treasure(self):
        """
        等待找到宝箱
        """
        in_fengmo = sleep_until(self.world.in_world)
        if in_fengmo is None:
            raise Exception("[wait_found_point_treasure]等待逢魔地图失败")
        point_pos = sleep_until(self.world.find_fengmo_point_treasure, self.find_treasure_wait_time)
        if point_pos is None:
            raise Exception("[wait_found_point_treasure]等待宝箱点失败")
        self.device_manager.click(*point_pos)
        return self.wait_found_item()
        
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
    
    def wait_found_result(self, interval=1.0, max_retry=30) -> tuple[Step,str]:
        """
        逢魔专用：等待识别到"获得道具"或"已发现所有的逢魔之影"，自动处理战斗等待，返回三种状态。
        :param interval: 识别间隔秒数
        :param max_retry: 最大重试次数，防止死循环
        """
        region = (381, 223, 897, 489)
        retry = 0
        state = ""
        while retry < max_retry:
            # 检查是否在战斗中
            if self.battle.in_battle():
                self.do_battle()
                state = "done_monster"
                return Step.COLLECT_JUNK,state
            # 非战斗中，识别文本
            results = self.ocr_handler.recognize_text(region=region)
            if not results:
                retry += 1
                time.sleep(interval)
                continue
            for r in results:
                if "获得道具" in r['text']:
                    self.device_manager.click(640, 430)
                    return Step.COLLECT_JUNK,state
                if "已发现所有的逢魔之影" in r['text']:
                    self.device_manager.click(640,480)
                    if sleep_until(self.check_found_boss,timeout=3):
                        return Step.FIGHT_BOSS,state
                    return Step.FIND_BOX,state
                if "完全恢复了" in r['text']:
                    self.device_manager.click(640,480)
                    time.sleep(1)
                    state = "done_cure"
                    self.world.click_tirm()
                    return Step.COLLECT_JUNK,state
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
        