from enum import Enum
from dataclasses import dataclass
from logging import Logger
import time
from typing import Any, Dict, Optional
from core import ocr_handler
from utils import ManagedThread, app_alive_monitor_func
from utils import logger
import threading
from common.app import AppManager
from core.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import Monster, config, CheckPoint
from utils.sleep_utils import sleep_until
import traceback

class Step(Enum):
    """
    逢魔流程阶段枚举
    - COLLECT_JUNK: 收集杂物阶段
    - FIND_BOX: 寻找宝箱/怪物/治疗点阶段
    - FIGHT_BOSS: 战斗Boss阶段
    """
    FINISH = 1
    COLLECT_JUNK = 2
    FIND_BOX = 3
    FIGHT_BOSS = 4

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
    app_alive: bool = False
    step: Step = Step.COLLECT_JUNK

    current_point: CheckPoint|None = None
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
        self.current_point = None

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
            logger.info(f"{e.__traceback__}\n{traceback.format_exc()}")

    
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
        self.world = World(device_manager, ocr_handler, self.battle, self.app_manager)
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
        self.find_point_wait_time = getattr(self.fengmo_config, 'find_point_wait_time', 2)
        self.start_wait_time = getattr(self.fengmo_config, 'start_wait_time', 0.8)
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
        app_shared = {
            'app_manager': self.app_manager,
            'state_data': self.state_data,
            'logger': logger,              # 可选
            'check_interval': 60,           # 可选
            'restart_wait': 5              # 可选
        }
        app_thread = ManagedThread(app_alive_monitor_func, app_shared)
        app_thread.start()
        check_info_shared = {
            'state_data': self.state_data,
            "device_manager": self.device_manager,
            'logger': logger,   # 可选
        }
        check_info_thread = ManagedThread(self.check_info, check_info_shared)
        check_info_thread.start()
        monsters = self.city_config.get("monsters", [])
        if monsters:
            self.world.set_monsters(monsters)
        while True:
            self.state_data.report_data()
            if self.rest_in_inn:
                logger.info("[run]旅店休息")
                self.world.rest_in_inn(self.inn_pos)
            self.world.go_fengmo(self.depth, self.entrance_pos)
            self.state_data.turn_start()
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
                reset_map = False
                next_tag = False
                while True:
                    self.wait_start_time()
                    #  当前查找逢魔点
                    logger.info(f"[collect_junk_phase]当前查找逢魔点: {check_point}")
                    if next_point:
                        break
                    logger.info(f"[collect_junk_phase]检查是否在城镇,是否在战斗中,执行战斗回调")
                    self.world.in_world_or_battle()
                    if self.check_state(Step.COLLECT_JUNK,check_point):
                        return
                    self.wait_start_time()
                    if (not reset_map and not next_tag) or (reset_map and next_tag):
                        logger.info(f"[collect_junk_phase]打开小地图")
                        self.world.open_minimap()
                        in_minimap = sleep_until(self.world.in_minimap)
                        if not in_minimap:
                            return
                        logger.info(f"[collect_junk_phase]点击小地图: {check_point}")
                        self.device_manager.click(*check_point.pos)
                        self.wait_start_time()
                        self.world.in_world_or_battle()
                        if self.check_state(Step.COLLECT_JUNK,check_point):
                            return
                        self.wait_start_time()
                    point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
                    logger.info(f"[collect_junk_phase]查找逢魔点: {point_pos} 点位: {check_point}")
                    if not point_pos:
                        next_point = True
                        break
                    logger.info(f"[collect_junk_phase]点击逢魔点: {point_pos} 点位: {check_point}")
                    self.device_manager.click(*point_pos[:2])
                    reset_map = check_point.reset_map
                    next_point = check_point.next_point
                    next_tag = True

    def _find_box_phase(self) -> None:
        """
        FIND_BOX 阶段主循环，负责查找宝箱、怪物、治疗点。
        - 处理宝箱、怪物、治疗点的查找与点击。
        - 通过 _handle_check_result 处理通用分支。
        - 可能因状态变化提前 return，或因异常抛出。
        """
        while True:
            logger.info(f"[find_box_phase]当前查找逢魔点: {self.state_data.current_point}")
            logger.info(f"[find_box_phase]是否等待在小镇中")
            self.world.in_world_or_battle()
            self.wait_start_time()
            if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                return
            self.world.open_minimap()
            in_minimap = sleep_until(self.world.in_minimap)
            if not in_minimap:
                raise Exception("[find_box_phase]打开小地图失败")
            logger.info(f"[find_box_phase]查找小地图标签")
            closest_point = self.find_map_tag()
            # 如果为空,则当前点遮挡了地图
            if closest_point: 
                self.state_data.current_point = closest_point
            if self.state_data.current_point is None:
                logger.error("[find_box_phase]出现异常,需要排查")
                raise Exception("[find_box_phase]出现异常,需要排查")
            check_point = self.state_data.current_point
            logger.info(f"[find_box_phase]点击小地图找到的最近点位: {check_point.pos}")
            self.device_manager.click(*check_point.pos)
            self.wait_start_time()
            logger.info(f"[find_box_phase]轮询配置的点位: {check_point.item_pos}")
            for point in check_point.item_pos:  
                logger.info(f"[find_box_phase]in_world_or_battle")
                self.world.in_world_or_battle()
                self.wait_start_time()
                if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                    return
                logger.info(f"[find_box_phase]点击配置的点位: {point}")
                self.device_manager.click(point[0],point[1])
                self.wait_start_time()


    def _fight_boss_phase(self):
        """
        Boss战阶段：
        进入逢魔地图，打开小地图，查找Boss点并点击，等待Boss点确认，进入战斗。
        边界处理：如Boss点未找到、地图未进入等，抛出异常。
        """
        logger.info(f"[fight_boss_phase]打开小地图")
        self.world.in_world_or_battle()
        self.wait_start_time()
        self.world.open_minimap()
        in_minimap = sleep_until(self.world.in_minimap)
        if not in_minimap:
            raise Exception("[fight_boss_phase]打开小地图失败")
        logger.info(f"[fight_boss_phase]查找Boss点")
        find_map_boss = sleep_until(self.world.find_map_boss)
        if find_map_boss:
            closest_point = self.find_closest_point(find_map_boss, self.check_points)
            self.state_data.current_point = closest_point
        if self.state_data.current_point is None:
            logger.error("[fight_boss_phase]出现异常,需要排查")
            raise Exception("[fight_boss_phase]出现异常,需要排查")
        logger.info(f"[fight_boss_phase]找到最近的Boss点: {closest_point}")
        check_point = self.state_data.current_point
        logger.info(f"[fight_boss_phase]点击小地图最近Boss的点: {check_point.pos}")
        self.device_manager.click(*check_point.pos)
        self.wait_start_time()
        logger.info(f"[fight_boss_phase]in_world_or_battle")
        self.world.in_world_or_battle()
        self.wait_start_time()
        point_pos = sleep_until(self.world.find_fengmo_point, self.find_point_wait_time)
        logger.info(f"[fight_boss_phase]查找Boss逢魔点: {point_pos}")
        if point_pos is None:
            raise Exception("[_fight_boss_phase]查找Boss逢魔点失败")
        logger.info(f"[fight_boss_phase]点击Boss逢魔点: {point_pos}")
        self.device_manager.click(*point_pos[:2])
        self.wait_start_time()
        self.world.in_world_or_battle(enemyName="逢魔之主")
        self.state_data.step = Step.FINISH
         

    def find_map_tag(self):
        screenshot = self.device_manager.get_screenshot()
        find_points = []
        # 记录 treasure 返回内容和类型
        treasure = self.world.find_map_treasure(screenshot)
        if treasure:
            find_points.extend(treasure)
        # 记录 monster 返回内容和类型
        monster = self.world.find_map_monster(screenshot)
        if monster:
            find_points.extend([monster])
        # 记录 cure 返回内容和类型
        cure = self.world.find_map_cure(screenshot)
        if cure:
            find_points.extend([cure])
        if self.state_data.current_point is None:
            return None
        current_point = self.state_data.current_point.pos
        closest_point_find_points = self.world.find_closest_point((current_point[0],current_point[1]), find_points)
        if closest_point_find_points:
            closest_point_check_point = self.find_closest_point(closest_point_find_points, self.check_points)
            if closest_point_check_point:
                return closest_point_check_point
        return None

    def check_info(self,shared: Dict[str, Any], stop_event: threading.Event, lock: Optional[threading.Lock] = None):
        try:
            state_data: StateData = shared['state_data']
            check_interval: float = shared.get('check_interval', 0.2)  # 检查间隔秒数
            logger: Logger = shared.get('logger', None)
            device_manager: DeviceManager = shared.get('device_manager', None)
            ocr_handler: OCRHandler = OCRHandler(device_manager)
            while not stop_event.is_set():
                time.sleep(check_interval) 
                screenshot = device_manager.get_cache_screenshot()
                region = (0, 0, 1280, 720)
                results = ocr_handler.recognize_text(region=region,image=screenshot)
                find_text = None
                for r in results:
                    if "战斗结算" in r['text']:
                        find_text = "battle_end"
                        self.world.click_tirm(6)
                        break
                    if "获得道具" in r['text']:
                        find_text = "found_treasure"
                        break
                    if "已发现所有的逢魔之影" in r['text']:
                        state_data.step = Step.FIND_BOX
                        find_text = "found_points"
                        break
                    if "完全恢复了" in r['text']:
                        find_text = "found_cure"
                        break
                    if "逢魔之主" in r['text']:
                        state_data.step = Step.FIGHT_BOSS
                        find_text = "found_boss"
                        ocr_handler.match_click_text(["是"],region=region,image=screenshot)
                        break
                if find_text:
                    logger.info(f"[check_info]找到文本: {find_text}")
                    ocr_handler.match_click_text(["确定"],region=region,image=screenshot)
        except Exception as e:
            err_msg = f"[check_info]出现异常: {e}"
            logger.info(err_msg)
            
    def check_state(self,step:Step,check_point:CheckPoint|None=None):
        if self.state_data.step != step:
            self.state_data.current_point = check_point
            logger.info(f"[check_state]当前状态: {self.state_data.step}，跳出check_state")
            logger.info(f"[check_state]当前状态: {self.state_data.step}")
            return True
        return False
    
    def wait_start_time(self):
        time.sleep(self.start_wait_time)

    def exit_battle(self):
        """
        退出战斗，调用Battle模块接口。
        """
        self.battle.exit_battle()
    
    def exit_fengmo(self,exit_pos:list[int], interval=1.0, max_retry=30):
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
        
        