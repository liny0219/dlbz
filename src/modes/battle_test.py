import time
import os
import traceback
from typing import Optional
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from utils import logger
from common.app import AppManager

class BattleTestMode:
    """
    战斗测试模式
    
    用于测试战斗脚本的正确性，支持单次或多次测试
    提供详细的执行日志和结果统计
    """

    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, 
                 log_queue=None, battle_script_path: Optional[str] = None):
        """
        初始化战斗测试模式
        
        :param device_manager: 设备管理器实例，用于与安卓设备交互
        :param ocr_handler: OCR处理器实例，用于图像识别
        :param log_queue: 日志队列，用于向主线程发送日志消息
        :param battle_script_path: 默认战斗脚本路径
        """
        from common.world import World
        from core.battle import Battle
        
        logger.info("[BattleTestMode] 初始化战斗测试模式")
        
        # 核心组件
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.log_queue = log_queue
        
        # 运行状态标志
        self.is_running = True
        
        # 配置信息
        self.battle_script_path = battle_script_path
        
        # 统计信息
        self.test_count = 0
        self.success_count = 0
        self.fail_count = 0
        
        # 初始化核心组件
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
        
        # 设置Battle的world依赖
        self.battle.set_world(self.world)
        
        logger.info("[BattleTestMode] 战斗测试模式初始化完成")

    def set_battle_script_path(self, script_path: str) -> None:
        """
        设置战斗脚本文件路径
        :param script_path: 脚本文件路径
        """
        self.battle_script_path = script_path
        logger.info(f"[BattleTestMode] 设置战斗脚本路径: {script_path}")

    def run(self, script_path: Optional[str] = None):
        """
        执行战斗测试主流程
        加载并执行指定的战斗脚本
        
        :param script_path: 战斗脚本文件路径
        """
        try:
            # 检查并使用传入的脚本路径
            if script_path is None:
                logger.error("未提供战斗脚本路径")
                return
                
            logger.info(f"开始战斗测试，脚本路径: {script_path}")
            
            # 加载战斗指令
            logger.info("正在加载战斗指令...")
            load_result = self.world.battle_executor.load_commands_from_txt(script_path)
            
            if not load_result:
                logger.error("战斗指令加载失败")
                return
            
            logger.info("战斗指令加载成功，开始执行...")
            
            # 执行战斗指令
            execute_result = self.world.battle_executor.execute_all()
            
            if execute_result:
                logger.info("战斗测试执行成功")
                self.success_count += 1
            else:
                logger.error("战斗测试执行失败")
                self.fail_count += 1
                
            # 统计信息
            logger.info(f"测试完成 - 成功: {self.success_count}, 失败: {self.fail_count}")
            
        except Exception as e:
            logger.error(f"战斗测试异常: {e}")
            logger.error(traceback.format_exc())
            self.fail_count += 1
        finally:
            self._report_test_results()

    def run_multiple_tests(self, script_path: str, test_count: int = 1) -> None:
        """
        运行多次战斗测试
        :param script_path: 战斗脚本文件路径
        :param test_count: 测试次数
        """
        self.set_battle_script_path(script_path)
        
        logger.info(f"[BattleTestMode] 开始执行 {test_count} 次战斗测试")
        
        for i in range(test_count):
            logger.info(f"[BattleTestMode] ========== 第 {i+1}/{test_count} 轮测试 ==========")
            self.run(self.battle_script_path)
            
            # 如果不是最后一次测试，等待一段时间
            if i < test_count - 1:
                wait_time = 2  # 等待2秒
                logger.info(f"[BattleTestMode] 等待 {wait_time} 秒后进行下一轮测试...")
                time.sleep(wait_time)

        self._report_test_results()

    def _report_test_results(self) -> None:
        """
        报告测试结果统计
        """
        logger.info("=" * 50)
        logger.info("[BattleTestMode] 战斗测试结果统计:")
        logger.info(f"[BattleTestMode] 总测试次数: {self.test_count}")
        logger.info(f"[BattleTestMode] 成功次数: {self.success_count}")
        logger.info(f"[BattleTestMode] 失败次数: {self.fail_count}")
        
        if self.test_count > 0:
            success_rate = (self.success_count / self.test_count) * 100
            logger.info(f"[BattleTestMode] 成功率: {success_rate:.1f}%")

        logger.info("=" * 50)

        # 发送统计数据到主进程GUI
        if self.log_queue is not None:
            lines = [
                "战斗测试统计",
                f"总测试次数: {self.test_count}",
                f"成功次数: {self.success_count}",
                f"失败次数: {self.fail_count}",
            ]
            if self.test_count > 0:
                success_rate = (self.success_count / self.test_count) * 100
                lines.append(f"成功率: {success_rate:.1f}%")
            
            report_str = '\n'.join(lines)
            try:
                self.log_queue.put("REPORT_DATA__" + report_str)
            except Exception as e:
                logger.warning(f"[BattleTestMode] 发送统计数据失败: {e}")

    def reset_statistics(self) -> None:
        """
        重置测试统计数据
        """
        self.test_count = 0
        self.success_count = 0
        self.fail_count = 0
        logger.info("[BattleTestMode] 测试统计数据已重置") 