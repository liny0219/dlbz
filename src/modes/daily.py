"""
日常玩法模式
实现花田与果炎的统一自动化功能
"""

import time
import os
from datetime import datetime
from typing import Dict, Any
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from utils.logger import logger
from common.world import World
from core.battle import Battle
from common.app import AppManager
from common.config import config

class DailyMode:
    """
    日常玩法模式
    
    功能特性：
    - 统一处理花田和果炎两个日常功能
    - 支持独立的配置和统计
    - 完整的错误处理和日志记录
    - 与GUI集成的状态反馈和时间统计
    - OCR识别时自动保存截图到debug/daily目录
    """
    
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, log_queue=None):
        """
        初始化日常玩法模式
        
        :param device_manager: 设备管理器实例
        :param ocr_handler: OCR处理器实例
        :param log_queue: 日志队列，用于向主进程发送日志和统计数据
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.log_queue = log_queue
        
        # 初始化核心组件
        self.app_manager = AppManager(device_manager)
        self.battle = Battle(device_manager, ocr_handler, self.app_manager)
        
        # 初始化世界对象，包含战斗执行器等核心组件
        self.world = World(device_manager, ocr_handler, self.battle, self.app_manager)
        
        # 设置Battle的world依赖
        self.battle.set_world(self.world)
        
        # 运行状态
        self.is_running = False
        
        # 调试截图目录配置
        self.debug_dir = "debug/daily"
        
        # 统计信息
        self.huatian_stats = {
            "huatian1": {
                "restart_count": 0,
                "total_time": 0.0,
                "target_found": False
            },
            "huatian2": {
                "restart_count": 0,
                "total_time": 0.0,
                "target_found": False
            }
        }
        
        self.guoyan_stats = {
            "restart_count": 0,
            "total_time": 0.0,
            "target_found": False
        }
        
        # 确保调试目录存在
        self._ensure_debug_directory()
        
        logger.info("日常玩法模式初始化完成")

    def _ensure_debug_directory(self):
        """
        确保调试截图目录存在
        """
        try:
            if not os.path.exists(self.debug_dir):
                os.makedirs(self.debug_dir, exist_ok=True)
                logger.info(f"创建调试截图目录: {self.debug_dir}")
        except Exception as e:
            logger.error(f"创建调试目录失败: {e}")

    def _save_ocr_screenshot(self, screenshot, ocr_type: str, success: bool = False):
        """
        保存OCR识别时的截图到调试目录
        
        :param screenshot: 截图对象
        :param ocr_type: OCR类型标识（如"huatian1", "huatian2", "guoyan"）
        :param success: 是否成功识别到目标
        """
        try:
            # 生成文件名：ocr类型_时间戳_成功状态.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
            if success:
                filename = f"ocr_{ocr_type}_{timestamp}_success.png"
            else:
                filename = f"ocr_{ocr_type}_{timestamp}.png"
            filepath = os.path.join(self.debug_dir, filename)
            
            # 保存截图
            if screenshot is not None:
                # 假设screenshot有save方法（如PIL Image）或者是numpy数组
                if hasattr(screenshot, 'save'):
                    screenshot.save(filepath)
                else:
                    # 如果是numpy数组，使用cv2保存
                    import cv2
                    cv2.imwrite(filepath, screenshot)
                
                logger.debug(f"已保存OCR调试截图: {filename}")
                
        except Exception as e:
            logger.error(f"保存OCR调试截图失败: {e}")

    def run(self, config_params: Dict[str, Any]):
        """
        运行日常玩法
        
        :param config_params: 配置参数字典，包含huatian_enabled和guoyan_enabled
        """
        if self.is_running:
            logger.warning("日常玩法模式已在运行中，跳过重复启动")
            return
            
        self.is_running = True
        
        try:
            logger.info("=" * 50)
            logger.info("开始执行日常玩法")
            logger.info(f"配置参数: {config_params}")
            logger.info("=" * 50)
            
            # 检查配置参数
            self.huatian_enabled = config_params.get("huatian_enabled", False)
            self.huatian1_enabled = config_params.get("huatian1_enabled", False)
            self.huatian2_enabled = config_params.get("huatian2_enabled", False)
            self.huatian_target_count = config_params.get("huatian_target_count", 10)
            self.guoyan_enabled = config_params.get("guoyan_enabled", False)
            self.guoyan_target_count = config_params.get("guoyan_target_count", 10)
            
            if not self.huatian_enabled and not self.guoyan_enabled:
                logger.warning("未启用任何日常功能，退出执行")
                return
            # 执行启用的日常功能
            if self.huatian_enabled:
                logger.info("开始执行花田功能...")
                # 重置花田统计
                self.reset_stats(reset_huatian=True, reset_guoyan=False)
                self._execute_huatian()
            
            time.sleep(1)
            if self.guoyan_enabled:
                logger.info("开始执行果炎功能...")
                # 只重置果炎统计，不影响花田统计
                self.reset_stats(reset_huatian=False, reset_guoyan=True)
                self._execute_guoyan()
            
            logger.info("=" * 50)
            logger.info("日常玩法执行完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"日常玩法执行过程中发生异常: {e}", exc_info=True)
        finally:
            self.is_running = False

    def _execute_huatian(self):
        """
        执行花田功能
        
        花田功能的具体业务逻辑：
        1. 检查当前状态
        2. 导航到花田位置
        3. 执行花田相关操作
        4. 记录统计数据
        """
        start_time = time.time()
        
        try:
            logger.info("[花田] 开始执行花田功能")
            
            # 步骤1: 检查应用状态
            if not self._check_app_status():
                logger.error("[花田] 应用状态检查失败")
                return

            map_name = self.world.get_map_name()
            if map_name is None or len(map_name) == 0:
                logger.error("无法识别地图名称")
                return
            if '无名小镇' not in map_name:
                if not self.world.tpAnywhere('无名小镇'):
                    logger.error("传送到无名小镇失败")
                    return
            else:
                logger.info("已经在无名小镇")
        
            
            # 步骤3: 处理花田1和花田2
            huatian1_pos = (514, 350)
            huatian2_pos = (680, 350)
            ocr_region = (512, 316, 767, 356)
            
            # 分别处理花田1和花田2，独立统计
            if self.huatian1_enabled:
                huatian1_start_time = time.time()
                if not self._check_huatian_target("花田1", huatian1_pos, ocr_region, huatian1_start_time):
                    return
                huatian1_elapsed_time = time.time() - huatian1_start_time
                self.huatian_stats["huatian1"]["total_time"] = huatian1_elapsed_time  # 覆盖，因为是一次完整的执行耗时
                logger.info(f"[花田1] 执行完成，重启次数: {self.huatian_stats['huatian1']['restart_count']} 耗时: {huatian1_elapsed_time:.0f}秒")
                # 发送最终统计更新，包含目标找到状态
                target_found = self.huatian_stats["huatian1"]["target_found"]
                self._send_stats_update("huatian1", huatian1_elapsed_time, target_found=target_found)
            
            if self.huatian2_enabled:
                huatian2_start_time = time.time()
                if not self._check_huatian_target("花田2", huatian2_pos, ocr_region, huatian2_start_time):
                    return
                huatian2_elapsed_time = time.time() - huatian2_start_time
                self.huatian_stats["huatian2"]["total_time"] = huatian2_elapsed_time  # 覆盖，因为是一次完整的执行耗时
                logger.info(f"[花田2] 执行完成，重启次数: {self.huatian_stats['huatian2']['restart_count']} 耗时: {huatian2_elapsed_time:.0f}秒")
                # 发送最终统计更新，包含目标找到状态
                target_found = self.huatian_stats["huatian2"]["target_found"]
                self._send_stats_update("huatian2", huatian2_elapsed_time, target_found=target_found)
            
            # 计算总耗时
            total_elapsed_time = time.time() - start_time
            logger.info(f"[花田] 花田功能执行成功，总耗时: {total_elapsed_time:.0f}秒")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[花田] 花田功能执行异常: {e}", exc_info=True)
            
            # 即使失败也要记录统计，但只影响启用的花田
            if self.huatian1_enabled:
                self.huatian_stats["huatian1"]["restart_count"] += 1
                self.huatian_stats["huatian1"]["total_time"] = elapsed_time  # 覆盖
                target_found = self.huatian_stats["huatian1"]["target_found"]
                self._send_stats_update("huatian1", elapsed_time, target_found=target_found)
            
            if self.huatian2_enabled:
                self.huatian_stats["huatian2"]["restart_count"] += 1
                self.huatian_stats["huatian2"]["total_time"] = elapsed_time  # 覆盖
                target_found = self.huatian_stats["huatian2"]["target_found"]
                self._send_stats_update("huatian2", elapsed_time, target_found=target_found)

    def _check_huatian_target(self, huatian_name: str, position: tuple, ocr_region: tuple, start_time: float) -> bool:
        """
        检查花田目标数量
        
        :param huatian_name: 花田名称（花田1或花田2）
        :param position: 点击位置坐标
        :param ocr_region: OCR识别区域
        :return: 是否找到目标数量
        """
        target_found = False
        target_count_str = str(self.huatian_target_count)
        in_target = False
        
        # 确定花田类型用于统计
        huatian_type = f"huatian{huatian_name.split('田')[1]}"
        
        while not target_found:
            if not in_target:
                self.world.move_mini_map(418, 222)
                in_target = True
            
            # 点击花田位置
            self.device_manager.click(position[0], position[1])
            time.sleep(1.5)
            
            # 获取截图
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None:
                logger.error("无法获取截图")
                return False
            
            # OCR识别目标数量
            ocr_result = self.ocr_handler.recognize_text(screenshot, ocr_region, rec_char_type='digit')

            if ocr_result is None or len(ocr_result) == 0:
                logger.error("无法识别目标数量")
                return False
            else:
                for line in ocr_result:
                    logger.info(f"找到{huatian_name}目标数量: {line['text']}")
                    if target_count_str in line['text']:
                        logger.info(f"{huatian_name}目标数量匹配: {self.huatian_target_count}")
                        target_found = True
                        # 保存成功识别的截图
                        self._save_ocr_screenshot(screenshot, huatian_type, success=True)
                        self.device_manager.click(640, 430)
                        break
            
            # 如果没有找到目标，保存普通截图并重启
            if not target_found:
                self._save_ocr_screenshot(screenshot, huatian_type, success=False)
                logger.info(f"未找到{huatian_name}目标数量，重启等待")
                self.world.restart_wait_in_world()
                
                # 增加重启次数
                self.huatian_stats[huatian_type]["restart_count"] += 1

                # 立即发送重启统计更新
                count = self.huatian_stats[huatian_type]["restart_count"]
                restart_elapsed_time = time.time() - start_time
                logger.info(f"{huatian_type}重启次数{count}, 耗时{restart_elapsed_time:.0f}秒")
                self._send_stats_update(huatian_type, restart_elapsed_time)
        
        # 找到目标后，标记为已找到
        self.huatian_stats[huatian_type]["target_found"] = True
        
        # 发送目标找到的统计更新
        elapsed_time = time.time() - start_time
        self._send_stats_update(huatian_type, elapsed_time, target_found=True)
        
        return True

    def _execute_guoyan(self):
        """
        执行果炎功能
        
        果炎功能的具体业务逻辑：
        1. 检查当前状态
        2. 导航到果炎位置
        3. 执行果炎相关操作
        4. 记录统计数据
        """
        start_time = time.time()
        
        try:
            logger.info("[果炎] 开始执行果炎功能")
            
            # 步骤1: 检查应用状态
            if not self._check_app_status():
                logger.error("[果炎] 应用状态检查失败")
                return
            
            # 步骤2: 检查当前位置
            map_name = self.world.get_map_name()
            if map_name is None or len(map_name) == 0:
                logger.error("无法识别地图名称")
                return
            if '圣树之泉' not in map_name:
                if not self.world.tpAnywhere('圣树之泉'):
                    logger.error("传送到圣树之泉失败")
                    return
            else:
                logger.info("已经在圣树之泉")
            

            target_found = False
            target_count_str = str(self.guoyan_target_count)
            ocr_region = (522, 317, 755, 355)
            in_target = False
            while not target_found:
                if not in_target:
                    self.world.move_mini_map(452, 238)
                    in_target = True
                self.device_manager.click(360, 385)
                time.sleep(1.5)
                # 获取截图
                screenshot = self.device_manager.get_screenshot()
                if screenshot is None:
                    logger.error("无法获取截图")
                    return False
                # OCR识别目标数量
                ocr_result = self.ocr_handler.recognize_text(screenshot, ocr_region, rec_char_type='digit')
                
                if ocr_result is None or len(ocr_result) == 0:
                    logger.error("无法识别目标数量")
                    return False
                else:
                    for line in ocr_result:
                        logger.info(f"找到果炎目标数量: {line['text']}")
                        if target_count_str in line['text']:
                            logger.info(f"果炎目标数量: {self.guoyan_target_count}")
                            target_found = True
                            # 保存成功识别的截图
                            self._save_ocr_screenshot(screenshot, "guoyan", success=True)
                            self.device_manager.click(640, 430)
                            break
                
                # 如果没有找到目标，保存普通截图
                if not target_found:
                    self._save_ocr_screenshot(screenshot, "guoyan", success=False)
                if not target_found:
                    logger.info(f"未找到果炎目标数量，重启等待")
                    self.world.restart_wait_in_world()
                    self.guoyan_stats["restart_count"] += 1
                    
                # 立即发送重启统计更新
                count = self.guoyan_stats["restart_count"] 
                restart_elapsed_time = time.time() - start_time
                logger.info(f"果炎重启次数{count}, 耗时:{restart_elapsed_time:.0f}秒")
                self._send_stats_update("guoyan", restart_elapsed_time)
            
            # 找到目标后，标记为已找到并发送统计更新
            self.guoyan_stats["target_found"] = True
            
            # 计算耗时并发送统计更新
            elapsed_time = time.time() - start_time
            self.guoyan_stats["total_time"] = elapsed_time  # 改为覆盖，与花田保持一致
            
            logger.info(f"[果炎] 果炎功能执行成功，耗时: {elapsed_time:.0f}秒")
            self._send_stats_update("guoyan", elapsed_time, target_found=True)
        
        except Exception as e:
            logger.error(f"[果炎] 果炎功能执行异常: {e}", exc_info=True)

    def _check_app_status(self) -> bool:
        """
        检查应用状态
        
        :return: 应用状态是否正常
        """
        try:
            logger.debug("检查应用状态...")
            
            # 检查设备连接
            if not self.device_manager.device:
                logger.error("设备未连接")
                return False
            
            # 检查应用是否在运行
            if not self.app_manager.is_app_running():
                logger.info("应用未运行，尝试启动应用...")
                self.app_manager.start_app()
                if not self.app_manager.is_app_running():
                    logger.error("启动应用失败")
                    return False
            
            logger.debug("应用状态检查通过")
            return True
            
        except Exception as e:
            logger.error(f"检查应用状态时发生异常: {e}", exc_info=True)
            return False

    def _send_stats_update(self, activity_type: str, elapsed_time: float, target_found: bool = False):
        """
        发送统计更新消息到主进程
        
        :param activity_type: 活动类型 ("huatian1", "huatian2" 或 "guoyan")
        :param elapsed_time: 执行耗时（秒）
        :param target_found: 是否找到目标
        """
        if self.log_queue is not None:
            try:
                # 获取当前重启次数
                if activity_type in ["huatian1", "huatian2"]:
                    restart_count = self.huatian_stats[activity_type]["restart_count"]
                elif activity_type == "guoyan":
                    restart_count = self.guoyan_stats["restart_count"]
                else:
                    restart_count = 0
                
                stats_msg = f"STATS_UPDATE__type:{activity_type},time:{elapsed_time:.2f},restart_count:{restart_count},target_found:{target_found}"
                self.log_queue.put(stats_msg)
                logger.info(f"[统计更新] 发送统计更新: {stats_msg}")
                logger.debug(f"[统计更新] 目标找到状态: {target_found}")
            except Exception as e:
                logger.error(f"发送统计更新失败: {e}")
        else:
            logger.warning(f"[统计更新] 日志队列为空，无法发送统计更新: {activity_type}, target_found={target_found}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取当前统计信息
        
        :return: 统计信息字典
        """
        return {
            "huatian": self.huatian_stats.copy(),
            "guoyan": self.guoyan_stats.copy()
        }

    def reset_stats(self, reset_huatian=True, reset_guoyan=True):
        """
        重置统计信息
        
        :param reset_huatian: 是否重置花田统计
        :param reset_guoyan: 是否重置果炎统计
        """
        if reset_huatian:
            self.huatian_stats = {
                "huatian1": {
                    "restart_count": 0,
                    "total_time": 0.0,
                    "target_found": False
                },
                "huatian2": {
                    "restart_count": 0,
                    "total_time": 0.0,
                    "target_found": False
                }
            }
            logger.info("花田统计信息已重置")
        
        if reset_guoyan:
            self.guoyan_stats = {
                "restart_count": 0,
                "total_time": 0.0,
                "target_found": False
            }
            logger.info("果炎统计信息已重置")

    def _send_final_stats(self):
        """
        发送最终统计信息
        """
        self._send_stats_update("huatian1", self.huatian_stats["huatian1"]["total_time"])
        self._send_stats_update("huatian2", self.huatian_stats["huatian2"]["total_time"])
        self._send_stats_update("guoyan", self.guoyan_stats["total_time"]) 