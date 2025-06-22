"""
追忆之书玩法模式
实现追忆之书的自动化测试功能，支持配置战斗次数
"""

import time
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from utils.logger import logger
from common.world import World
from core.battle import Battle
from common.app import AppManager

class MemoryMode:
    """
    追忆之书玩法模式
    
    功能特性：
    - 支持自定义战斗次数
    - 使用配置的战斗脚本执行战斗
    - 完整的错误处理和日志记录
    - 与GUI集成的状态反馈
    """
    
    def __init__(self, device_manager:DeviceManager, ocr_handler:OCRHandler, log_queue=None):
        """
        初始化追忆之书模式
        
        :param device_manager: 设备管理器实例
        :param ocr_handler: OCR处理器实例
        :param log_queue: 日志队列，用于向主进程发送日志
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.log_queue = log_queue
        
        # 初始化Battle和AppManager实例
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        
        # 初始化世界对象，包含战斗执行器等核心组件
        self.world = World(device_manager, ocr_handler, self.battle, self.app_manager)
        
        # 统计信息（仅保留总次数用于进度跟踪）
        self.total_battles = 0
        self.is_running = False
        
        logger.info("追忆之书模式初始化完成")

    def run(self, script_path, battle_count, click_x=1100, click_y=200, ui_wait_time=0.5):
        """
        运行追忆之书
        
        :param script_path: 战斗脚本文件路径
        :param battle_count: 配置的战斗次数
        :param click_x: 点击阅读按钮的X坐标
        :param click_y: 点击阅读按钮的Y坐标
        :param ui_wait_time: UI操作间隔等待时间
        """
        if self.is_running:
            logger.warning("追忆之书模式已在运行中，跳过重复启动")
            return
            
        self.is_running = True
        
        try:
            logger.info(f"开始追忆之书，配置参数：脚本={script_path}, 战斗次数={battle_count}, 点击坐标=({click_x}, {click_y}), UI等待时间={ui_wait_time}秒")
            
            # 保存配置参数供后续使用
            self.click_x = click_x
            self.click_y = click_y
            self.ui_wait_time = ui_wait_time
            
            # 重置统计信息
            self.total_battles = 0
            
            # 检查战斗脚本文件
            if not self._validate_script_file(script_path):
                logger.error("战斗脚本文件验证失败，终止执行")
                return
            
            # 加载战斗脚本
            if not self._load_battle_script(script_path):
                logger.error("加载战斗脚本失败，终止执行")
                return
            
            # 执行追忆之书循环
            while self.total_battles < battle_count:
                try:
                    logger.info(f"开始第 {self.total_battles + 1}/{battle_count} 次追忆之书")
                    # 输出当前统计
                    self._print_current_stats(battle_count)
                    # 点击阅读
                    self.click_read()
                    time.sleep(ui_wait_time)  # 使用配置的UI等待时间
                    # 确认阅读
                    self.confirm_read()
                    time.sleep(ui_wait_time)  # 使用配置的UI等待时间
                    # 等待战斗开始
                    self.battle.press_in_round(timeout=15)
                    # 执行单次战斗
                    self.world.battle_executor.execute_all()
                    in_battle = self.battle.in_battle()
                    if in_battle:
                        self.battle.exit_battle()
                    # 等待战斗结果并处理（OCR检测会更新统计数据）
                    self._wait_and_handle_battle_result(ui_wait_time)
                    self.total_battles += 1
                    time.sleep(ui_wait_time)  # 使用配置的UI等待时间
                except Exception as e:
                    logger.error(f"第 {self.total_battles + 1} 次追忆之异常: {e}", exc_info=True)
                    # 发送异常导致的失败统计到GUI
                    self._send_stats_update(False)
                    self.total_battles += 1
            
            # 输出最终统计
            self._print_final_stats()
            
        except Exception as e:
            logger.error(f"追忆之书过程中发生异常: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("追忆之书结束")

    def _validate_script_file(self, script_path):
        """
        验证战斗脚本文件是否存在且可读
        
        :param script_path: 战斗脚本文件路径
        :return: 验证结果
        """
        import os
        
        try:
            # 处理相对路径
            if not os.path.isabs(script_path):
                from common.config import get_config_dir
                config_dir = get_config_dir()
                
                # 尝试在config目录下查找
                try_path = os.path.join(config_dir, script_path)
                if os.path.exists(try_path):
                    script_path = try_path
                else:
                    # 尝试在battle_scripts目录下查找
                    try_path2 = os.path.join(config_dir, 'battle_scripts', script_path)
                    if os.path.exists(try_path2):
                        script_path = try_path2
            
            # 检查文件是否存在
            if not os.path.exists(script_path):
                logger.error(f"战斗脚本文件不存在: {script_path}")
                return False
            
            # 检查文件是否可读
            if not os.access(script_path, os.R_OK):
                logger.error(f"战斗脚本文件无法读取: {script_path}")
                return False
            
            logger.info(f"战斗脚本文件验证成功: {script_path}")
            self.script_path = script_path  # 保存验证后的路径
            return True
            
        except Exception as e:
            logger.error(f"验证战斗脚本文件时发生异常: {e}")
            return False

    def _load_battle_script(self, script_path):
        """
        加载战斗脚本到战斗执行器
        
        :param script_path: 战斗脚本文件路径
        :return: 加载结果
        """
        try:
            logger.info(f"正在加载战斗脚本: {script_path}")
            
            # 使用世界对象中的战斗执行器加载指令
            load_result = self.world.battle_executor.load_commands_from_txt(script_path)
            
            if load_result:
                logger.info("战斗脚本加载成功")
                return True
            else:
                logger.error("战斗脚本加载失败")
                return False
                
        except Exception as e:
            logger.error(f"加载战斗脚本时发生异常: {e}", exc_info=True)
            return False



    def _print_final_stats(self):
        """
        输出最终统计信息
        """
        logger.info("=" * 50)
        logger.info("追忆之书完成")
        logger.info("=" * 50)
        logger.info(f"总战斗次数: {self.total_battles}")
        logger.info("详细统计信息请查看GUI界面")
        logger.info("=" * 50)



    def _print_current_stats(self, total_count):
        """
        输出当前统计信息
        
        :param total_count: 总计划次数
        """
        logger.info(f"当前进度: {self.total_battles}/{total_count}")

    def _wait_and_handle_battle_result(self, ui_wait_time):
        """
        等待战斗结果并处理相应的界面响应
        
        :param ui_wait_time: UI等待时间
        :return: 战斗是否成功
        """
        battle_success = False
        result_counted = False  # 确保只统计一次结果
        
        # 定义需要检测的OCR区域
        ocr_regions = [
            (443, 294, 819, 336),  # 主要检测区域  
            (550, 114, 724, 160)     # 备用检测区域
        ]
        if self.device_manager.device is None:
            logger.error("设备未连接")
            return False
        time.sleep(0.5)
        logger.info(f"长按按下,等待跳过")
        self.device_manager.press_down(100,20)
        while True:
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None:
                logger.warning("无法获取截图，跳过OCR检测")
                time.sleep(ui_wait_time)
                continue
            
            # 检测是否需要退出循环
            battle_finished = False
            
            # 遍历所有OCR检测区域
            for region in ocr_regions:
                result = self.ocr_handler.recognize_text(screenshot, region=region)
                
                # 处理OCR识别结果
                for text in result:
                    text_content = text.get('text', '')
                    
                    # 检测获得报酬（战斗成功）
                    if text_content == '获得报酬':
                        logger.info(f"获得报酬")
                        if not result_counted:
                            logger.info(f"长按抬起")
                            self.device_manager.press_up(100,20)
                            battle_success = True
                            result_counted = True
                            logger.info("检测到战斗成功：获得报酬")
                            # 发送统计更新消息到GUI（只在GUI端统计）
                            self._send_stats_update(True)
                        logger.info(f"确认获得报酬")
                        self.confirm_success()
                    
                    # 检测体力恢复（战斗结束）
                    elif text_content == '体力和精力已回到原本的状态':
                        logger.info(f"体力恢复")
                        if not result_counted:
                            logger.info(f"长按抬起")
                            self.device_manager.press_up(100,20)
                            result_counted = True
                            logger.info("检测到战斗失败：体力恢复")
                            # 发送统计更新消息到GUI（只在GUI端统计）
                            self._send_stats_update(False)
                        logger.info(f"体力恢复,确认治疗")
                        self.confirm_cure()
                        battle_finished = True
                        break
                
                # 如果检测到战斗结束，退出区域循环
                if battle_finished:
                    break
            
            # 如果战斗结束，退出主循环
            if battle_finished:
                break
            
            time.sleep(ui_wait_time)
        
        return battle_success

    def click_read(self):
        """
        点击追忆之书阅读按钮
        """
        try:
            logger.info(f"点击阅读按钮坐标: ({self.click_x}, {self.click_y})")
            self.device_manager.click(self.click_x, self.click_y)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"点击阅读按钮失败: {e}")

    def confirm_read(self):
        """
        确认阅读（可能有确认弹窗）
        """
        try:
            logger.info("确认阅读")
            self.device_manager.click(800, 620)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"确认阅读失败: {e}")

    def confirm_success(self):
        """
        确认战斗成功
        """
        try:
            logger.info("确认战斗成功")
            # 这里可以添加确认战斗成功的逻辑
            # 暂时使用简单的等待
            self.device_manager.click(655, 556)
        except Exception as e:
            logger.warning(f"确认战斗成功失败: {e}")

    def confirm_cure(self):
        """
        确认治疗
        """
        try:
            logger.info("确认治疗")
            self.device_manager.click(640, 400)
        except Exception as e:
            logger.warning(f"确认治疗失败: {e}")

    def _send_stats_update(self, success):
        """
        发送统计更新消息到GUI
        
        :param success: 是否成功
        """
        try:
            if self.log_queue:
                stats_msg = f"STATS_UPDATE__success:{str(success).lower()}"
                self.log_queue.put(stats_msg)
        except Exception as e:
            logger.warning(f"发送统计更新失败: {e}")
