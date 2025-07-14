from enum import Enum
from dataclasses import dataclass
import time
from typing import Optional
from PIL import Image
from utils import logger
from common.app import AppManager
from core.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.config import Monster, config, CheckPoint
from utils.sleep_utils import sleep_until
import traceback
import gc

class Step(Enum):
    """
    逢魔流程阶段枚举
    - COLLECT_JUNK: 收集杂物阶段
    - FIND_BOX: 寻找宝箱/怪物/治疗点阶段
    - FIGHT_BOSS: 战斗Boss阶段
    """
    UN_START = 0
    FINISH = 1
    COLLECT_JUNK = 2
    FIND_BOX = 3
    FIND_BOSS = 4
    FIGHT_BOSS = 5
    BATTLE_FAIL = 6
    State_FAIL = 7

# 状态处理结果常量
class StateResult:
    """状态处理结果常量"""
    APP_NOT_ALIVE = 'app_not_alive'
    BATTLE_FAIL = 'battle_fail'
    IN_BATTLE = 'in_battle'
    CONTINUE = 'continue'
    IN_WORLD = 'in_world'
    
# 检查信息常量
class CheckInfoResult:
    """检查信息结果常量"""
    FOUND_TREASURE = "found_treasure"
    FOUND_POINTS = "found_points"
    FOUND_CURE = "found_cure"
    FOUND_BOSS = "found_boss"
    BATTLE_END = "battle_end"
    BATTLE_FAIL = "battle_fail"

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
    map_fail: bool = False
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
        self.current_point = None
        self.map_fail = False

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
            if self.total_finished_count > 0:
                self.avg_finished_time = round((self.total_finished_time / self.total_finished_count), 2)
            if self.total_fail_count > 0:
                self.avg_fail_time = round((self.total_fail_time / self.total_fail_count), 2)
        except Exception as e:
            logger.info(f"{e.__traceback__}\n{traceback.format_exc()}")

    
    def report_data(self):
        """报告统计数据 - 补充完整字段"""
        # 计算成功率
        total_attempts = self.total_finished_count + self.total_fail_count
        success_rate = (self.total_finished_count / total_attempts * 100) if total_attempts > 0 else 0
        
        # 计算失败平均用时
        fail_avg_time = (self.total_fail_time / self.total_fail_count) if self.total_fail_count > 0 else 0
        
        # 计算综合平均用时
        total_time = self.total_finished_time + self.total_fail_time
        total_avg_time = (total_time / total_attempts) if total_attempts > 0 else 0
        
        # 记录详细统计信息到日志
        logger.info(f"[report_data]当前轮数: {self.turn_count}")
        logger.info(f"[report_data]当前轮次用时: {self.turn_time}分钟")
        logger.info(f"[report_data]当前成功次数: {self.total_finished_count}")
        logger.info(f"[report_data]当前失败次数: {self.total_fail_count}")
        logger.info(f"[report_data]当前成功用时: {self.total_finished_time}分钟")
        logger.info(f"[report_data]当前成功平均用时: {self.avg_finished_time}分钟")
        logger.info(f"[report_data]当前失败用时: {self.total_fail_time}分钟")
        logger.info(f"[report_data]当前失败平均用时: {fail_avg_time:.1f}分钟")
        logger.info(f"[report_data]当前成功率: {success_rate:.1f}%")
        logger.info(f"[report_data]当前综合平均用时: {total_avg_time:.1f}分钟")

class FengmoMode:
    """
    逢魔玩法模块
    负责实现逢魔相关的自动化逻辑，包括地图探索、宝箱/怪物/治疗点查找、Boss战等。
    依赖设备管理、OCR识别、世界与战斗模块。
    """

    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, log_queue=None) -> None:
        """
        初始化逢魔模式
        :param device_manager: 设备管理器，负责点击、操作等
        :param ocr_handler: OCR识别处理器
        :param log_queue: 日志队列，用于发送统计数据到主进程
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
        self.log_queue = log_queue  # 添加日志队列属性
        self.fengmo_config = config.fengmo
        self.city_name = self.fengmo_config.city
        self.depth = self.fengmo_config.depth
        self.rest_in_inn = self.fengmo_config.rest_in_inn
        self.vip_cure = self.fengmo_config.vip_cure
        fengmo_cities = config.fengmo_cities
        if self.city_name not in fengmo_cities:
            raise ValueError(f"未找到城市配置: {self.city_name}")
        self.city_config = fengmo_cities[self.city_name]
        self.inn_pos = self.city_config.get("inn_pos", [])
        self.monsters = self.city_config.get("monsters", [])
        self.monster_pos = self.city_config.get("monster_pos",[])
        self.entrance_pos = self.city_config.get("entrance_pos", [])
        self.check_points = self.city_config.get("check_points", [])
        self.find_point_wait_time = getattr(self.fengmo_config, 'find_point_wait_time', 1.5)
        self.wait_map_time = getattr(self.fengmo_config, 'wait_map_time', 0.5)
        self.wait_ui_time = getattr(self.fengmo_config, 'wait_ui_time', 0.2)
        self.default_battle_config = getattr(self.fengmo_config, 'default_battle_config', '')
        self.difficulty_delay = getattr(self.fengmo_config, 'difficulty_delay', 0.5)
        self.involve_match_threshold = getattr(self.fengmo_config, 'involve_match_threshold', 0.8)
        
        self.state_data: StateData = StateData()
        
        # 截图计数器，用于定期GC
        self._screenshot_counter = 0  # 截图计数器
        self._gc_interval = 100  # 每100次截图执行一次GC

        # 设置Battle的world依赖
        self.battle.set_world(self.world)

    def _manage_screenshot_memory(self):
        """管理截图内存，定期执行GC"""
        self._screenshot_counter += 1
        if self._screenshot_counter >= self._gc_interval:
            self._screenshot_counter = 0
            collected = gc.collect()
            logger.debug(f"定期内存清理完成，回收对象数: {collected}")

    def _in_world_or_battle(self):
        time.sleep(self.wait_ui_time)
        return self.world.in_world_or_battle(callback=lambda image: self.check_info(image))

    def _performance_monitor(self, operation_name: str):
        """
        性能监控装饰器上下文管理器
        
        :param operation_name: 操作名称
        """
        class PerformanceContext:
            def __init__(self, name):
                self.name = name
                self.start_time = None
                
            def __enter__(self):
                self.start_time = time.time()
                logger.debug(f"[性能监控]开始执行: {self.name}")
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time is not None:
                    elapsed = time.time() - self.start_time
                    if elapsed > 5:  # 超过5秒的操作记录警告
                        logger.warning(f"[性能监控]{self.name} 耗时较长: {elapsed:.2f}秒")
                    else:
                        logger.debug(f"[性能监控]{self.name} 完成: {elapsed:.2f}秒")
                    
        return PerformanceContext(operation_name)

    def cleanup(self):
        """清理线程资源"""
        logger.info("开始清理逢魔模式线程...")
        
        # 清理状态数据
        if hasattr(self, 'state_data'):
            del self.state_data
        
        # 清理配置引用
        if hasattr(self, 'fengmo_config'):
            del self.fengmo_config
        if hasattr(self, 'city_config'):
            del self.city_config
        
        # 强制垃圾回收
        collected = gc.collect()
        logger.info(f"逢魔模式线程清理完成，回收对象数: {collected}")

    def report_data(self):
        """报告统计数据 - 补充完整字段"""
        # 使用本地变量避免重复访问，使用类型断言确保linter知道state_data不为None
        state_data = self.state_data
        assert state_data is not None  # 类型断言，告诉linter state_data不为None
        
        # 计算成功率
        total_attempts = state_data.total_finished_count + state_data.total_fail_count
        success_rate = (state_data.total_finished_count / total_attempts * 100) if total_attempts > 0 else 0
        
        # 计算失败平均用时
        fail_avg_time = (state_data.total_fail_time / state_data.total_fail_count) if state_data.total_fail_count > 0 else 0
        
        # 计算综合平均用时
        total_time = state_data.total_finished_time + state_data.total_fail_time
        total_avg_time = (total_time / total_attempts) if total_attempts > 0 else 0
        
        # 记录详细统计信息到日志
        logger.info(f"[report_data]当前轮数: {state_data.turn_count}")
        logger.info(f"[report_data]当前轮次用时: {state_data.turn_time}分钟")
        logger.info(f"[report_data]当前成功次数: {state_data.total_finished_count}")
        logger.info(f"[report_data]当前失败次数: {state_data.total_fail_count}")
        logger.info(f"[report_data]当前成功用时: {state_data.total_finished_time}分钟")
        logger.info(f"[report_data]当前成功平均用时: {state_data.avg_finished_time}分钟")
        logger.info(f"[report_data]当前失败用时: {state_data.total_fail_time}分钟")
        logger.info(f"[report_data]当前失败平均用时: {fail_avg_time:.1f}分钟")
        logger.info(f"[report_data]当前成功率: {success_rate:.1f}%")
        logger.info(f"[report_data]当前综合平均用时: {total_avg_time:.1f}分钟")
        
        # 发送统计数据到主进程GUI - 使用紧凑的文字格式
        if self.log_queue is not None:
            report_str = f"""当前轮数: {state_data.turn_count} | 当前用时: {state_data.turn_time:.1f} 分钟
成功: {state_data.total_finished_count} 次 | 失败: {state_data.total_fail_count} 次 | 成功率: {success_rate:.1f}%
总用时: {state_data.total_finished_time + state_data.total_fail_time:.1f} 分钟 | 综合平均: {total_avg_time:.1f} 分钟
成功平均: {state_data.avg_finished_time:.1f} 分钟 | 失败平均: {fail_avg_time:.1f} 分钟"""
            
            self.log_queue.put(f"REPORT_DATA__{report_str}")

    def check_enter_fengmo(self):
        screenshot = self.device_manager.get_screenshot()
        if screenshot is None:
            logger.error("[run]获取截图失败")
            return
        self.check_info(screenshot)
        return "map_fail" if self.state_data.map_fail else None
    
    def run(self) -> None:
        """
        逢魔主循环入口，负责整体流程调度：
        1. 检查App存活
        2. 休息（如配置）
        3. 进入逢魔
        4. 按阶段依次执行收集、找宝箱/怪物/治疗点、Boss战
        """
        try:
            self.world.set_monsters(self.monster_pos,self.monsters,self.default_battle_config)
            self.state_data.step = Step.UN_START
            while True:
                self.report_data()
                logger.info(f"[run]当前配置的城市: {self.city_name} 深度增量: {self.depth}")
                # if not self.world.wait_in_fengmo_map():
                if self.rest_in_inn:
                    logger.info("[run]休息检查")
                    need_inn = True
                    if self.world.vip_cure(self.vip_cure) == 'finish_cure':
                        need_inn = False
                    if need_inn:
                        self.world.rest_in_inn(self.inn_pos)

                self.state_data.map_fail = False
                while True:
                    if not self.world.go_fengmo(self.depth, self.entrance_pos,
                                                 callback=self.check_enter_fengmo,
                                                 threshold=self.involve_match_threshold,
                                                 difficulty_delay=self.difficulty_delay):
                        self.state_data.step = Step.State_FAIL
                        break
                    if self.world.wait_in_fengmo_map(timeout=10):
                        self.state_data.step = Step.UN_START
                        break
                if self.state_data.step == Step.State_FAIL:
                    continue
                self.state_data.turn_start()
                self.state_data.step = Step.COLLECT_JUNK
                if self.state_data.step == Step.COLLECT_JUNK:
                    self._collect_junk_phase()
                logger.info(f"[run]进入二阶段当前状态: {self.state_data.step}")
                if self.state_data.step == Step.FIND_BOX:
                    self._find_box_phase()
                logger.info(f"[run]进入三阶段当前状态: {self.state_data.step}")
                if self.state_data.step == Step.FIND_BOSS:
                    self._find_boss_phase()
                if self.state_data.step == Step.BATTLE_FAIL or self.state_data.step == Step.State_FAIL:
                    self.state_data.turn_end(type='fail')
                if self.state_data.step == Step.FINISH:
                    self.state_data.turn_end(type='success')
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("逢魔进程收到中断信号，正在清理...")
        except Exception as e:
            logger.error(f"逢魔进程发生异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 确保清理线程资源
            self.cleanup()
            logger.info("逢魔进程已结束")

    def _collect_junk_phase(self) -> None:
        """
        COLLECT_JUNK 阶段主循环，负责遍历 check_points 并处理收集杂物流程。
        - 处理小地图、逢魔地图、点位点击、点位结果判定等。
        - 通过 _handle_check_result 处理通用分支。
        - 可能因状态变化提前 return，或因异常抛出。
        """
        while True:
            point_index = 0
            while point_index < len(self.check_points):
                check_point = self.check_points[point_index]
                next_point = False
                reset_map = False
                next_tag = False
                while True:
                    if next_point:
                        break
                    self.wait_map()
                    logger.info(f"[collect_junk_phase]检查是否在城镇,是否在战斗中,执行战斗回调")
                    in_world_or_battle = self._in_world_or_battle()
                    logger.info(f"[collect_junk_phase]in_world_or_battle: {in_world_or_battle}")
                    if in_world_or_battle:
                        if not in_world_or_battle["app_alive"]:
                            logger.info(f"[collect_junk_phase]App未运行")
                            if not self.wait_check_mode_state_ok():
                                return
                            if point_index > 0:
                                point_index -= 1
                            next_point = True  # 设置为True跳出内层循环
                            continue
                        if not in_world_or_battle["is_battle_success"]:
                            logger.info(f"[collect_junk_phase]战斗失败")
                            self.state_data.step = Step.BATTLE_FAIL
                            return
                        if in_world_or_battle["in_world"]:
                            logger.info(f"[collect_junk_phase]在城镇中")
                        if in_world_or_battle["in_battle"]:
                            logger.info(f"[collect_junk_phase]遇敌战斗过")
                            # 如果遇到战斗,返回上一个检查点继续检查
                            if point_index > 0:
                                point_index -= 1
                            next_point = True  # 设置为True跳出内层循环
                            continue
                    if self.check_state(Step.COLLECT_JUNK,check_point):
                        return
                    self.wait_map()
                    if (not reset_map and not next_tag) or (reset_map and next_tag):
                        logger.info(f"[collect_junk_phase]打开小地图")
                        while True:
                            self.wait_map()
                            self.world.open_minimap()
                            in_minimap = sleep_until(self.world.in_minimap,timeout=5)
                            if not in_minimap:
                                logger.info(f"[collect_junk_phase]小地图未打开")
                            else:
                                state = self.world.get_fengmo_state()
                                if state == 'boss':
                                    self.state_data.step = Step.FIND_BOSS
                                    self.world.closeUI()
                                    return
                                if state == 'box':
                                    self.state_data.step = Step.FIND_BOX
                                    self.world.closeUI()
                                    return
                                logger.info(f"[collect_junk_phase]点击小地图: {check_point}")
                                self.device_manager.click(check_point.pos[0], check_point.pos[1])
                            self.wait_map()
                            in_world_or_battle = self._in_world_or_battle()
                            logger.info(f"[collect_junk_phase]in_world_or_battle: {in_world_or_battle}")
                            if in_world_or_battle:
                                if not in_world_or_battle["app_alive"]:
                                    if not self.wait_check_mode_state_ok():
                                        return
                                    continue
                                if not in_world_or_battle["is_battle_success"]:
                                    logger.info(f"[collect_junk_phase]战斗失败")
                                    self.state_data.step = Step.BATTLE_FAIL
                                    return
                                if in_world_or_battle["in_world"]:
                                    logger.info(f"[collect_junk_phase]在城镇中")
                                    break
                                if in_world_or_battle["in_battle"]:
                                    logger.info(f"[collect_junk_phase]遇敌战斗过")
                                    time.sleep(self.wait_map_time)
                            if self.check_state(Step.COLLECT_JUNK,check_point):
                                return
                    self.wait_map()
                    #  当前查找逢魔点
                    logger.info(f"[collect_junk_phase]当前查找逢魔点: {check_point.id}")
                    point_pos = sleep_until(lambda: self.world.find_fengmo_point(current_point=check_point), 
                                            timeout=self.find_point_wait_time,
                                            function_name=f"find_fengmo_point {check_point.id}")
                    logger.info(f"[collect_junk_phase]查找到逢魔点: {point_pos}")
                    if not point_pos:
                        next_point = True
                        break
                    logger.info(f"[collect_junk_phase]点击逢魔点: {point_pos}")
                    self.device_manager.click(int(point_pos[0]), int(point_pos[1]))
                    reset_map = check_point.reset_map
                    next_point = check_point.next_point
                    next_tag = True
                
                # 如果next_point为True，则处理下一个检查点
                if next_point:
                    point_index += 1

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
            in_world_or_battle = self._in_world_or_battle()
            logger.info(f"[find_box_phase]in_world_or_battle: {in_world_or_battle}")
            if in_world_or_battle is not None:
                if not in_world_or_battle["app_alive"]:
                    if not self.wait_check_mode_state_ok():
                       return
                    continue
                if not in_world_or_battle["is_battle_success"]:
                    logger.info(f"[_find_box_phase]战斗失败")
                    self.state_data.step = Step.BATTLE_FAIL
                    return
            self.wait_map()
            if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                return
            self.world.open_minimap()
            def in_minimap_callback():
                if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                    return 'return'
                if self.world.in_minimap():
                    return 'continue'
                return False
            in_minimap = sleep_until(in_minimap_callback,timeout=5)
            if in_minimap == 'return':
                return
            if not in_minimap:
                logger.info(f"[find_box_phase]小地图未打开")
                continue
            logger.info(f"[find_box_phase]查找小地图标签")
            closest_point = self.find_map_tag()
            # 如果为空,则当前点遮挡了地图
            if closest_point: 
                self.state_data.current_point = closest_point
            else:
                logger.info(f"[find_box_phase]小地图未找到标签,可能逢魔之主弹窗被跳过,状态异常")
                logger.info(f"[find_box_phase]尝试寻找boss")
                boss_point = self.world.find_map_boss()
                self.world.closeUI()
                if boss_point:
                    logger.info(f"[find_box_phase]找到boss,状态矫正")
                    self.state_data.step = Step.FIND_BOSS
                    return
                else:
                    logger.info(f"[find_box_phase]小地图未找到boss,状态异常,退出重来")
                    self.world.exit_fengmo( self.entrance_pos, callback=self.check_enter_fengmo )
                    return
            if self.state_data.current_point is None:
                logger.error("[find_box_phase]出现异常,需要排查")
                raise Exception("[find_box_phase]出现异常,需要排查")
            check_point = self.state_data.current_point
            if check_point is None:
                logger.error("[find_box_phase]check_point为None，需要排查")
                raise Exception("[find_box_phase]check_point为None，需要排查")
            logger.info(f"[find_box_phase]点击小地图找到的最近点位:{check_point.id} {check_point.pos}")
            self.device_manager.click(check_point.pos[0], check_point.pos[1])
            self.wait_map()
            in_world_or_battle = self._in_world_or_battle()
            logger.info(f"[find_box_phase]in_world_or_battle: {in_world_or_battle}")
            if in_world_or_battle and in_world_or_battle["in_battle"]:
                logger.info(f"[find_box_phase]遇敌战斗过")
                self.wait_map()
            if in_world_or_battle is not None:
                if not in_world_or_battle["app_alive"]:
                    if not self.wait_check_mode_state_ok():
                       return
                    continue
                if not in_world_or_battle["is_battle_success"]:
                    logger.info(f"[_find_box_phase]战斗失败")
                    self.state_data.step = Step.BATTLE_FAIL
                    return
            if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                return
            if check_point is None:
                logger.error("[find_box_phase]check_point为None，需要排查")
                raise Exception("[find_box_phase]check_point为None，需要排查")
            logger.info(f"[find_box_phase]轮询配置的点位: {check_point.item_pos}")
            is_first = True
            for point in check_point.item_pos:
                if not is_first:
                    in_world_or_battle = self._in_world_or_battle()
                    logger.info(f"[find_box_phase]in_world_or_battle: {in_world_or_battle}")
                    if in_world_or_battle is not None:
                        if not in_world_or_battle["app_alive"]:
                            if not self.wait_check_mode_state_ok():
                                return
                            continue
                        if not in_world_or_battle["is_battle_success"]:
                            logger.info(f"[_find_box_phase]战斗失败")
                            self.state_data.step = Step.BATTLE_FAIL
                            return
                    logger.info(f"[find_box_phase]in_world_or_battle")
                    self.wait_map()
                    if self.check_state(Step.FIND_BOX,self.state_data.current_point):
                        return
                is_first = False
                logger.info(f"[find_box_phase]点击配置的点位: {point}")
                self.device_manager.click(point.pos[0],point.pos[1])
                self.wait_map()

    def _find_boss_phase(self):
        """
        Boss战阶段：
        进入逢魔地图，打开小地图，查找Boss点并点击，等待Boss点确认，进入战斗。
        边界处理：如Boss点未找到、地图未进入等，抛出异常。
        """
        first_loop = True
        while True:
            if first_loop:
                first_loop = False
                result = self.wait_check_boss()
                if result == 'in_world_battle_fail' or result == 'in_world_fight_boss':
                    return
                if result == 'app_not_alive':
                    if not self.wait_check_mode_state_ok():
                       return
                    continue
                self.wait_map()
            logger.info(f"[find_boss_phase]打开小地图")
            self.world.open_minimap()
            in_minimap = sleep_until(self.world.in_minimap,timeout=5)
            if not in_minimap:
                logger.error("[find_boss_phase]打开小地图失败")
                first_loop = True
                continue
            logger.info(f"[find_boss_phase]查找Boss点")
            find_map_boss = sleep_until(self.world.find_map_boss,timeout=6)
            if find_map_boss is None:
                logger.info(f"[find_boss_phase]找不到boss感叹号可能被自己挡住,退出重来")
                self.world.closeUI()
                self.state_data.step = Step.State_FAIL
                self.world.exit_fengmo(self.entrance_pos,callback=self.check_enter_fengmo)
                return
            if find_map_boss:
                closest_point = self.find_closest_point(find_map_boss, self.check_points)
                self.state_data.current_point = closest_point
                if self.state_data.current_point is None:
                    logger.error("[find_boss_phase]出现异常,需要排查")
                    raise Exception("[find_boss_phase]出现异常,需要排查")
                logger.info(f"[find_boss_phase]找到最近的Boss点: {closest_point}")
                check_point = self.state_data.current_point
                if check_point is None:
                    logger.error("[find_boss_phase]check_point为None，需要排查")
                    raise Exception("[find_boss_phase]check_point为None，需要排查")
                logger.info(f"[find_boss_phase]点击小地图最近Boss的点: {check_point.pos}")
                self.device_manager.click(check_point.pos[0], check_point.pos[1])
                self.wait_map()
                result = self.wait_check_boss()
                if result == 'in_world_battle_fail' or result == 'in_world_fight_boss':
                    return
                if result == 'app_not_alive':
                    if not self.wait_check_mode_state_ok():
                        return
                    continue
                while True:
                    self.app_manager.device_manager.device
                    self.wait_map()
                    point_pos = sleep_until(lambda: self.world.find_fengmo_point(current_point=check_point),
                                             self.find_point_wait_time,function_name="find_fengmo_point")
                    logger.info(f"[find_boss_phase]查找Boss逢魔点: {point_pos}")
                    if point_pos is None:
                        logger.info(f"[find_boss_phase]找不到boss感叹号,点击配置的点位")
                        current_point = self.state_data.current_point
                        if current_point is None:
                            logger.error("[find_boss_phase]current_point为None，需要排查")
                            raise Exception("[find_boss_phase]current_point为None，需要排查")
                        item_pops = current_point.item_pos
                        for item in item_pops:
                            logger.info(f"[find_boss_phase]点击预设的坐标: {item.pos}")
                            self.device_manager.click(item.pos[0],item.pos[1])
                    else:
                        logger.info(f"[find_boss_phase]点击Boss逢魔点: {point_pos}")
                        self.device_manager.click(int(point_pos[0]), int(point_pos[1]))
                    self.wait_map()
                    result = self.wait_check_boss()
                    if result == 'in_world':
                        break
                    if result == 'in_world_fight_boss' or result == 'in_world_battle_fail':
                        return
                    if result == 'app_not_alive':
                        if not self.wait_check_mode_state_ok():
                            return
                        continue

    def wait_check_mode_state_ok(self):
        step = None
        result = self.world.restart_wait_in_fengmo_world()
        if result == 'boss':
            step = Step.FIND_BOSS
        if result == 'box':
            step = Step.FIND_BOX
        if result == 'collect':
            step = Step.COLLECT_JUNK
        if self.state_data.step != step:
            self.state_data.step = Step.State_FAIL
            return False
        return True
    
    def find_map_tag(self):
        """
        查找地图标签 - 主线程专用
        
        设计意图：
        - 在主线程中查找小地图上的各种标签（宝箱、怪物、治疗点）
        - 返回距离最近的检查点
        - 为后续的点击操作提供目标位置
        """
        # 主线程中直接获取截图，不使用缓存
        screenshot = self.device_manager.get_screenshot()
        if screenshot is None:
            return None
            
        try:
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
            closest_find_points = []
            for find_point in find_points:
                closest_find_points.append(self.find_closest_point((find_point[0],find_point[1]), self.check_points))
            # 返回cloest_find_points id 最小的点
            if closest_find_points and len(closest_find_points) > 0:
                closest_find_points.sort(key=lambda x: x.id)
                return closest_find_points[0]
            return None
        except Exception as e:
            logger.warning(f"[find_map_tag]处理截图时发生异常: {e}")
            return None

    def wait_check_boss(self):
        in_world_or_battle = self._in_world_or_battle()
        logger.info(f"[wait_check_boss]in_world_or_battle: {in_world_or_battle}")
        if in_world_or_battle:
            if not in_world_or_battle["app_alive"]:
                self.world.restart_wait_in_fengmo_world()
                return 'app_not_alive'
            if not in_world_or_battle["is_battle_success"]:
                logger.info(f"[find_boss_phase]战斗失败")
                self.state_data.step = Step.BATTLE_FAIL
                return 'in_world_battle_fail'
            if in_world_or_battle["in_battle"]:
                logger.info(f"[check_boss]遇敌战斗过")
                if self.state_data.step == Step.FIGHT_BOSS:
                    logger.info(f"[check_boss]boss战斗")
                    self.state_data.step = Step.FINISH
                    return 'in_world_fight_boss'
                else:
                    logger.info(f"[check_boss]小怪战斗")
                    return 'in_world_fight_monster'
        return 'in_world'

    def check_info(self, screenshot: Image.Image|None):
        if screenshot is None:
            screenshot = self.device_manager.get_screenshot()
        try:
            try:
                if self.world.click_confirm(screenshot):
                    logger.info(f"[check_info]click_confirm")
                    time.sleep(self.wait_ui_time)
                    return
                if self.battle.battle_end(screenshot):
                    logger.info(f"[check_info]战斗结算")
                    self.world.dclick_tirm(3)
                    time.sleep(self.wait_ui_time)
                    return
                if self.world.check_exit_fengmo(screenshot):
                    logger.info(f"[check_info]退出逢魔")
                    self.state_data.map_fail = True
                    self.state_data.step = Step.State_FAIL
                    self.world.click_confirm_yes()
                    return
                if self.world.check_found_boss(screenshot):
                    logger.info(f"[check_info]找到boss,点击确认")
                    self.state_data.step = Step.FIGHT_BOSS
                    self.world.click_confirm_yes()
                    return
                if self.world.check_net_state(screenshot):
                    logger.info(f"[check_info]网络断开,点击重试")
                    self.device_manager.click(771, 417)
                    return
            except Exception as e:
                logger.info(f"[check_info]处理截图时发生异常: {e}")
        except Exception as e:
            err_msg = f"[check_info]出现异常: {e}"
            logger.info(err_msg)
            # 异常时停止线程，避免持续运行
            return
            
    def check_state(self,step:Step,check_point:CheckPoint|None=None):
        if self.state_data.step != step:
            self.state_data.current_point = check_point
            logger.info(f"[check_state]当前状态: {self.state_data.step}，跳出check_state")
            logger.info(f"[check_state]当前状态: {self.state_data.step}")
            return True
        return False
    
    def wait_map(self):
        time.sleep(self.wait_map_time)
        
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
        
        