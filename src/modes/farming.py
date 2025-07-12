from dataclasses import dataclass
import threading
import time
from typing import Any, Dict, Optional
from common import world
from utils import logger
from common.app import AppManager
from core.battle import Battle
from common.world import World
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
import traceback


@dataclass
class FarmingStateData:
    """
    刷野流程状态数据
    包含刷野过程中的各种状态信息和统计数据
    """
    app_alive: bool = False
    in_map: bool = False
    battle_count:int = 0
    last_time:float = 0
  
class FarmingMode:
    """
    刷野玩法模块
    负责实现自动刷野的核心逻辑，包括：
    - 自动寻找和战斗怪物
    - 收集战斗奖励
    - 状态管理和异常处理
    - 统计信息记录
    
    依赖设备管理、OCR识别、世界与战斗模块实现具体操作
    """

    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, log_queue=None) -> None:
        """
        初始化刷野模式
        设置必要的组件和配置参数
        
        :param device_manager: 设备管理器，负责点击、滑动等操作
        :param ocr_handler: OCR识别处理器，负责文字和图像识别
        :param log_queue: 日志队列，用于发送统计数据到主进程
        """
        # 核心组件初始化
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
        
        # 设置Battle的world依赖
        self.battle.set_world(self.world)
        
        self.log_queue = log_queue  # 添加日志队列属性
            
        # 状态数据初始化
        self.state_data = FarmingStateData()
        
    def report_data(self):
        """发送统计数据到主进程GUI"""
        logger.info(f"[report_data]当前战斗次数: {self.state_data.battle_count}")
        
        # 如果有日志队列，发送统计数据到主进程
        if self.log_queue is not None:
            lines = [
                f"刷野模式统计",
                f"当前战斗次数: {self.state_data.battle_count}",
                f"当前挂机时间: {self.state_data.last_time} 分钟" 
            ]
            report_str = '\n'.join(lines)
            try:
                self.log_queue.put("REPORT_DATA__" + report_str)
            except Exception as e:
                logger.warning(f"发送统计数据失败: {e}")

    def run(self) -> None:
        """
        刷野主循环入口
        负责整体流程调度和异常处理：
        1. 启动监控线程
        2. 执行刷野主循环
        3. 处理状态转换和异常情况
        4. 统计和报告结果
        """
        logger.info("[刷野模式] 开始执行刷野任务")
        
        # 重置状态数据
        self.state_data = FarmingStateData()
        
        start_time = time.time()
        is_left = 0
        battle = self.world._get_battle()
        try:
            while True:
                screenshot = self.device_manager.get_screenshot()
                in_battle = battle and battle.in_battle(screenshot)
                battle_end = self.battle.battle_end(screenshot)
                if battle_end:
                    self.world.click_tirm(6)
                    self.state_data.battle_count += 1
                    self.state_data.last_time = round((time.time() - start_time) / 60, 2)
                    self.report_data()
                    continue
                if in_battle:
                    self.battle.auto_battle(timeout=1)
                    continue
                if is_left:
                    time.sleep(1)
                    logger.info("[in_world]向右跑")
                    self.world.run_right()
                else:
                    time.sleep(1)
                    logger.info("[in_world]向左跑")
                    self.world.run_left()
                is_left = not is_left
                time.sleep(0.1)
                screenshot = self.device_manager.get_screenshot()
               
        except Exception as e:
            logger.error(f"[刷野模式] 主循环异常: {e}")
            logger.error(f"{e.__traceback__}\n{traceback.format_exc()}")
        finally:
            # 最终报告
            logger.info("[刷野模式] 刷野任务结束")
