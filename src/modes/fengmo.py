from enum import Enum
from dataclasses import dataclass
import os
from PIL import Image
import time
from typing import Optional
from utils import logger
from common.app import AppManager
from common.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import config, CheckPoint
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
    done_cure: bool = False

    turn_start_time: float = 0
    turn_end_time: float = 0
    turn_count: int = 0
    turn_time: float = 0
    total_finished_count: int = 0
    total_finished_time: float = 0
    total_fail_count: int = 0
    total_fail_time: float = 0
    avg_finished_time: float = 0
    avg_fail_time: float = 0

    def turn_start(self):
        self.turn_start_time = time.time()
        self.turn_end_time = 0
        self.step = Step.COLLECT_JUNK
        self.done_cure = False

    def turn_end(self,type='success'):
        try:
            self.turn_end_time = time.time()
            self.turn_time = round((self.turn_end_time - self.turn_start_time) / 60, 2)
            self.turn_count += 1
            if type == 'success':
                self.total_finished_count += 1
                self.total_finished_time = round((self.total_finished_time + self.turn_time), 2)
            else:
                self.total_fail_count += 1
                self.total_fail_time = round((self.total_fail_time + self.turn_time), 2)
            self.avg_finished_time = round((self.total_finished_time / self.total_finished_count), 2)
        except Exception as e:
            logger.info(f"{e.__traceback__}")

    
    def report_data(self):
        logger.info(f"[report_data]当前轮数: {self.turn_count}")
        logger.info(f"[report_data]当前轮次用时: {self.turn_time}分钟")
        logger.info(f"[report_data]当前成功次数: {self.total_finished_count}")
        logger.info(f"[report_data]当前成功用时: {self.total_finished_time}分钟")
        logger.info(f"[report_data]当前成功平均用时: {self.avg_finished_time}分钟")
        logger.info(f"[report_data]当前失败平均用时: {self.avg_fail_time}分钟")

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
        self.reset_pos = self.city_config.get("reset_pos", [])
        self.find_point_wait_time = 2
        self.find_treasure_wait_time = 2
        self.find_minimap_wait_time = 2
        self.check_info_timeout = 1
        self.state_data = StateData()

    def run(self) -> None:
        """
        逢魔主循环入口，负责整体流程调度：
        1. 检查App存活
        2. 休息（如配置）
        3. 进入逢魔
        4. 按阶段依次执行收集、找宝箱/怪物/治疗点、Boss战
        """
        self.state_data = StateData()
        while True:
            self.state_data.turn_start()
            self.state_data.report_data()

            self.app_manager.check_app_alive()
            if self.rest_in_inn:
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth, self.entrance_pos)
            self.state_data.step = Step.COLLECT_JUNK
            self.state_data.done_cure = False
            if self.state_data.step == Step.COLLECT_JUNK:
                self._collect_junk_phase()
            logger.info(f"[run]进入二阶段当前状态: {self.state_data.step}")
            if self.state_data.step == Step.FIND_BOX:
                self._find_box_phase()
            logger.info(f"[run]进入三阶段当前状态: {self.state_data.step}")
            if self.state_data.step == Step.FIGHT_BOSS:
                self._fight_boss_phase()

            self.state_data.turn_end(type='success')
            

    def _collect_junk_phase(self) -> None:
        """
        COLLECT_JUNK 阶段主循环，负责遍历 check_points 并处理收集杂物流程。
        - 处理小地图、逢魔地图、点位点击、点位结果判定等。
        - 通过 _handle_check_result 处理通用分支。
        - 可能因状态变化提前 return，或因异常抛出。
        """
        while True:
            for check_point in self.check_points:
                next_point = False
                while True:
                    if next_point:
                        break
                    while True:
                        check_result = sleep_until(self.check_info,timeout = self.check_info_timeout)
                        # 使用通用处理函数，减少重复
                        handle_result = self._handle_check_result(check_result)
                        if handle_result == 'in_world':
                            self.world.open_minimap()
                            break
                        if handle_result == 'return':
                            return
                        if handle_result == 'continue':
                            continue
                        if handle_result == 'break':
                            break
                    in_mini_map = sleep_until(self.world.in_minimap)
                    if in_mini_map is None:
                        raise Exception("[_collect_junk_phase]等待小地图失败")
                    logger.info(f"[collect_junk_phase]点击点位: {check_point} 坐标: {check_point.pos}")
                    self.device_manager.click(*check_point.pos)
                    result = self.in_world_or_battle()
                    if result is None:
                        raise Exception("[_collect_junk_phase]等待逢魔地图失败")
                    if result == "battle_end":
                        continue
                    while True:
                        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                        logger.info(f"[collect_junk_phase]查找逢魔点: {point_pos} 点位: {check_point}")
                        if not point_pos:
                            next_point = True
                            break
                        logger.info(f"[collect_junk_phase]点击逢魔点: {point_pos} 点位: {check_point}")
                        self.device_manager.click(*point_pos)
                        try:
                            check_result = sleep_until(lambda:self.check_info(filter={"in_world":False}))
                            logger.info(f"[collect_junk_phase]等待逢魔点结果: {check_result} 点位: {check_point}")
                            # 使用通用处理函数，减少重复
                            handle_result = self._handle_check_result(check_result)
                            if handle_result == 'return':
                                return
                            if check_point.next_point:
                                next_point = True
                                break
                            if check_point.reset_map:
                                break
                        except Exception as e:
                            raise Exception(f"[_collect_junk_phase]等待结果失败: {e}")

    def _find_box_phase(self) -> None:
        """
        FIND_BOX 阶段主循环，负责查找宝箱、怪物、治疗点。
        - 处理宝箱、怪物、治疗点的查找与点击。
        - 通过 _handle_check_result 处理通用分支。
        - 可能因状态变化提前 return，或因异常抛出。
        """
        done_treasure = False
        done_monster = False
        reset_count = 0
        current_point = None
        while True:
            if done_treasure and done_monster and self.state_data.done_cure:
                logger.info(f"[find_box_phase]完成所有类型，重置状态")
                done_treasure = False
                done_monster = False
                self.state_data.done_cure = False
                reset_count += 1
                if reset_count >= 2:
                    current_point = self.reset_pos
                    reset_count = 0
                    continue
            while True:
                logger.info(f"[find_box_phase]等待检查信息")
                check_result = sleep_until(self.check_info,timeout = self.check_info_timeout)
                # 使用通用处理函数，减少重复
                handle_result = self._handle_check_result(check_result)
                logger.info(f"[find_box_phase]检查信息结果: {handle_result}")
                if handle_result == 'in_world':
                    self.world.open_minimap()
                    break
                if handle_result == 'break':
                    break
                if handle_result == 'return':
                    return
                if handle_result == 'continue':
                    continue
            if current_point:
                self.device_manager.click(*current_point)
                current_point = None
            if not done_treasure:
                logger.info(f"[find_box_phase]查找宝箱")
                find_map_treasure = sleep_until(self.world.find_map_treasure, self.find_minimap_wait_time)
                if find_map_treasure is None:
                    done_treasure = True
                    continue
                    # 查找最近的check_point
                closest_point = self.find_closest_point(find_map_treasure, self.check_points)
                logger.info(f"[find_box_phase]查找最近点位: {closest_point}")
                if closest_point is None:
                    continue
                logger.info(f"[find_box_phase]点击宝箱点: {closest_point} 坐标: {closest_point.pos}")
                self.device_manager.click(*closest_point.pos)
                while True:
                    result = self.in_world_or_battle()
                    if result is None:
                        raise Exception("[wait_found_point_treasure]等待逢魔地图失败")
                    if result == "battle_end":
                        self.world.open_minimap()
                        in_mini_map = sleep_until(self.world.in_minimap)
                        if in_mini_map is None:
                            continue
                        self.device_manager.click(*closest_point.pos)
                    if result == "in_world":
                        break
                # 保存图片到debug目录
                image = self.device_manager.get_screenshot()
                if isinstance(image, Image.Image):
                    os.makedirs("debug", exist_ok=True)
                    image_path = f"debug/wait_found_point_treasure.png"
                    image.save(image_path)
                treasure_points = closest_point.found
                if not treasure_points or len(treasure_points) == 0:
                    logger.warning(f"[wait_found_point_treasure]treasure_points未配置，跳过点击宝箱点: {closest_point}")
                for point in treasure_points:
                    in_fengmo_map = sleep_until(self.world.in_world)
                    if not in_fengmo_map:
                        continue
                    self.device_manager.click(point[0],point[1])
                    logger.info(f"[wait_found_point_treasure]点击宝箱点: {point} 点位: {closest_point}")
                    check_result = sleep_until(lambda:self.check_info(filter={"in_world":False}),timeout=self.find_treasure_wait_time)
                    # 使用通用处理函数，减少重复
                    handle_result = self._handle_check_result(check_result)
                    logger.info(f"[wait_found_point_treasure]等待宝箱结果: {handle_result} 点位: {closest_point}")
                    if handle_result == 'return':
                        return
            if not done_monster:
                logger.info(f"[find_box_phase]查找怪物")
                find_map_monster = sleep_until(self.world.find_map_monster, self.find_minimap_wait_time)
                if not find_map_monster:
                    done_monster = True
                    continue
                # 查找最近的check_point
                closest_point = self.find_closest_point(find_map_monster, self.check_points)
                logger.info(f"[find_box_phase]查找最近点位: {closest_point}")
                if closest_point is None:
                    continue
                logger.info(f"[find_box_phase]点击怪物点: {closest_point}")
                self.device_manager.click(*closest_point.pos)
                while True:
                    result = self.in_world_or_battle()
                    if result is None:
                        raise Exception("[find_box_phase]等待逢魔地图失败")
                    if result == "battle_end":
                        self.world.open_minimap()
                        in_mini_map = sleep_until(self.world.in_minimap)
                        if in_mini_map is None:
                            continue
                        self.device_manager.click(*closest_point.pos)
                    if result == "in_world":
                        break
                    if result == 'found_boss':
                        return
                while True:
                    point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                    if point_pos is None:
                        done_monster = True
                        break
                    self.device_manager.click(*point_pos)
                    result = self.in_world_or_battle()
                    if result == 'battle_end':
                        break
                    if result == 'found_boss':
                        return
            # 找治疗点
            if not self.state_data.done_cure:
                logger.info(f"[find_box_phase]查找治疗点")
                find_map_cure = sleep_until(self.world.find_map_cure, self.find_minimap_wait_time)
                if find_map_cure is None:
                    self.state_data.done_cure = True
                    continue
                # 查找最近的check_point
                closest_point = self.find_closest_point(find_map_cure, self.check_points)
                logger.info(f"[find_box_phase]查找最近点位: {closest_point}")
                if closest_point is None:
                    continue
                logger.info(f"[find_box_phase]点击治疗点: {closest_point}")
                self.device_manager.click(*closest_point.pos)
                while True:
                    result = self.in_world_or_battle()
                    if result is None:
                        raise Exception("[find_box_phase]等待逢魔地图失败")
                    if result == "battle_end":
                        self.world.open_minimap()
                        in_mini_map = sleep_until(self.world.in_minimap)
                        if in_mini_map is None:
                            continue
                        self.device_manager.click(*closest_point.pos)
                    if result == "in_world":
                        break
                    if result == 'found_boss':
                        return
                while True:
                    point_pos = sleep_until(self.world.find_fengmo_point_cure, self.find_point_wait_time)
                    if point_pos:
                        self.device_manager.click(*point_pos)
                    result = sleep_until(self.check_info,timeout=self.check_info_timeout)
                    if result == "found_cure":
                        self.state_data.done_cure = True
                        break
                    if result == "in_battle":
                        break
                    if result == 'found_boss':
                        return
    def _fight_boss_phase(self):
        """
        Boss战阶段：
        进入逢魔地图，打开小地图，查找Boss点并点击，等待Boss点确认，进入战斗。
        边界处理：如Boss点未找到、地图未进入等，抛出异常。
        """
        while True:
            in_fengmo_map = sleep_until(self.world.in_world)
            if in_fengmo_map is None:
                raise Exception("[_fight_boss_phase]等待逢魔地图失败")
            self.world.open_minimap()
            in_mini_map = sleep_until(self.world.in_minimap)
            if in_mini_map is None:
                raise Exception("[_fight_boss_phase]等待小地图失败")
            find_map_boss = sleep_until(self.world.find_map_boss, self.find_minimap_wait_time)
            if not find_map_boss:
                raise Exception("[_fight_boss_phase]Boss点失败")
            closest_point = self.find_closest_point(find_map_boss, self.check_points)
            logger.info(f"[find_box_phase]查找最近点位: {closest_point}")
            if not closest_point:
                raise Exception("[_fight_boss_phase]查找最近Boss点失败")
            logger.info(f"[find_box_phase]点击最近Boss点: {closest_point}")
            self.device_manager.click(*closest_point.pos)
                
            result = self.in_world_or_battle()
            if result is None:
                raise Exception("[_fight_boss_phase]等待逢魔地图失败")
            if result == "battle_end":
                continue
            point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
            logger.info(f"[fight_boss_phase]查找Boss点: {point_pos}")
            if point_pos is None:
                raise Exception("[_fight_boss_phase]查找Boss点失败")
            logger.info(f"[fight_boss_phase]点击Boss点: {point_pos}")
            self.device_manager.click(*point_pos)
            confirm_pos = sleep_until(lambda:self.ocr_handler.match_click_text(["是"],region=(257,168,1023,552)))
            if confirm_pos is None:
                raise Exception("[wait_found_point_boss]等待确认点失败")
            logger.info(f"[fight_boss_phase]进入战斗")
            self.do_battle()
            logger.info(f"[fight_boss_phase]战斗结束")
            break

    def do_battle(self):
        """
        战斗流程：
        1. 检查是否进入战斗
        2. 自动战斗（如支持）
        3. 检查结算与确认，自动点击
        边界处理：自动战斗失败抛异常。
        """
        is_auto_battle = False
        battle_end = False
        while True:
            if self.battle.in_battle():
                if is_auto_battle:
                    continue
                if self.battle.auto_battle():
                    logger.info(f"auto_battle")
                    is_auto_battle = True
            else:
                if battle_end:
                    break
            if self.ocr_handler.match_texts(["战斗结算"]):
                battle_end = True
                self.world.click_tirm()
                time.sleep(1)
                self.world.click_tirm()
            if self.ocr_handler.match_click_text(["确定"],region=(516,571,769,644)):
                break
            if self.ocr_handler.match_texts(["战斗中"]):
                is_auto_battle = True

    def in_world_or_battle(self):
        """
        判断是否在逢魔地图或战斗中
        """
        battle_end = False
        while True:
            result = sleep_until(lambda:"in_world" if self.world.in_world() 
                                 else "in_battle" if self.battle.in_battle()
                                 else "found_boss" if self.check_found_boss()
                                 else None,timeout=3)
            if result == "found_boss":
                self.state_data.step = Step.FIGHT_BOSS
                return "found_boss"
            if result == "in_world":
                if battle_end:
                    return 'battle_end'
                return "in_world"
            if result == "in_battle":
                logger.info(f"do_battle")
                self.do_battle()
                battle_end = True
                continue
    
    def _handle_check_result(self, check_result: str | None) -> str | None:
        """
        通用处理 check_result 的分支逻辑，减少 run 方法中的重复代码。
        参数：
            check_result (str | None): sleep_until(self.check_info) 的返回结果
        返回：
            str: 'return' 表示需要 return 当前循环，'continue' 表示需要 continue，None 表示继续后续逻辑,
            'in_world' 表示在逢魔地图中，'in_battle' 表示在战斗中，'found_points' 表示找到点位，'found_cure' 表示找到治疗点，'found_boss' 表示找到Boss点
        逻辑说明：
            - 处理 found_boss、in_world、in_battle、found_points、found_cure 等分支
            - 保持与原有 run 方法一致的副作用和流程
        边界情况：
            - 未命中任何分支时返回 None
        """
        if check_result is None:
            return None
        if check_result == "found_boss":
            if self.state_data == Step.COLLECT_JUNK or self.state_data.step == Step.FIND_BOX:
                self.state_data.step = Step.FIGHT_BOSS
                return 'return'  # 需要 return 当前循环
        if check_result == "in_world":
            return 'in_world'  
        if check_result == "in_battle":
            self.do_battle()
            return 'continue'  # 需要 continue 当前循环
        if check_result == "found_points":
            if self.state_data.step == Step.COLLECT_JUNK:
                self.state_data.step = Step.FIND_BOX
                return 'return'  # 需要 return 当前循环
        if check_result == "found_cure":
            self.state_data.done_cure = True
            return 'continue'  # 需要 continue 当前循环
        if check_result == "in_minimap":
            return 'break'  # 需要 continue 当前循环
        return None

    def check_info(self,filter:dict[str,bool]={}):
        """
        检查信息
        """
        if filter.get("in_world",True) and self.world.in_world():
            return "in_world"
        if filter.get("in_battle",True) and self.battle.in_battle():
            return "in_battle"
        if filter.get("found_boss",True) and self.check_found_boss():
            return "found_boss"
        if filter.get("in_minimap",True) and self.world.in_minimap():
            return "in_minimap"
        region = (292, 175, 983, 540)
        results = self.ocr_handler.recognize_text(region=region)
        find_text = None
        for r in results:
            if "获得道具" in r['text']:
                find_text = "found_treasure"
            if "完全恢复了" in r['text']:
                find_text = "found_cure"
            if "已发现所有的逢魔之影" in r['text']:
                find_text = "found_points"
            if "完全恢复了" in r['text']:
                find_text = "found_cure"
            if "逢魔之主" in r['text']:
                find_text = "found_boss"
        if find_text:
            logger.info(f"[check_info]找到文本: {find_text}")
            self.ocr_handler.match_click_text(["确定"],region=region)
            return find_text
        return None

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
    
    def wait_found_point_treasure(self,check_point:CheckPoint):
        """
        等待找到宝箱点，点击并等待获得道具。
        边界处理：宝箱点未找到抛异常。
        :return: True-获得道具，False-未获得
        """           
        in_fengmo = self.in_world_or_battle()
        if in_fengmo is None:
            raise Exception("[wait_found_point_treasure]等待逢魔地图失败")
        # 保存图片到debug目录
        image = self.device_manager.get_screenshot()
        if isinstance(image, Image.Image):
            os.makedirs("debug", exist_ok=True)
            image_path = f"debug/wait_found_point_treasure.png"
            image.save(image_path)
        treasure_points = check_point.found
        if not treasure_points or len(treasure_points) == 0:
            logger.warning(f"[wait_found_point_treasure]treasure_points未配置，跳过点击宝箱点: {check_point}")
        for point in treasure_points:
            in_fengmo_map = sleep_until(self.world.in_world)
            if not in_fengmo_map:
                self.world.open_minimap()
                in_mini_map = sleep_until(self.world.in_minimap)
                if in_mini_map is None:
                    return
                self.device_manager.click(*check_point.pos)
            self.device_manager.click(point[0],point[1])
            logger.info(f"[wait_found_point_treasure]点击宝箱点: {point} 点位: {check_point}")
            while True:
                check_result = sleep_until(lambda:self.check_info(filter={"in_world":False}),timeout=self.find_treasure_wait_time)
                # 使用通用处理函数，减少重复
                handle_result = self._handle_check_result(check_result)
                logger.info(f"[wait_found_point_treasure]等待宝箱结果: {handle_result} 点位: {check_point}")
                if handle_result == 'return':
                    return
                if handle_result is not None:
                    break

    def wait_found_item(self):
        """
        等待获得道具提示，点击确认。
        :return: True-获得道具，False-未获得
        """
        if self.wait_found_point_text("获得道具",(381,223,897,489),is_raise=False):
            self.device_manager.click(643, 433)
            return True
        else:
            return False
        
    def wait_found_point_text(self,text:str,region:tuple[int,int,int,int],interval=1.0,max_retry=5,is_raise=True):
        """
        等待找到指定文本
        :param text: 目标文本
        :param region: 识别区域
        :param interval: 识别间隔
        :param max_retry: 最大重试次数
        :param is_raise: 是否抛异常
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
        if is_raise:
            raise Exception(f"[wait_found_point_text]等待{text}失败")
        else:
            logger.warning(f"[wait_found_point_text]等待{text}失败")
            return False
       
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
        
    def find_closest_point(self, target: list[int] | tuple[int, int], points: list[CheckPoint]) -> Optional[CheckPoint]:
        """
        在points中查找与target最近的点对象（要求点对象有pos属性）
        :param target: 目标点 [x, y] 或 (x, y)
        :param points: 点对象列表（每个对象有pos属性）
        :return: 距离最近的点对象
        """
        import math
        min_distance = float('inf')
        closest_point = None
        for point in points:
            distance = math.sqrt((point.pos[0] - target[0]) ** 2 + (point.pos[1] - target[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        return closest_point
        
        