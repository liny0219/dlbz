"""
梦境模式 - 自动化梦境玩法
将按键精灵VB脚本翻译为Python实现
"""

import time
import logging
from typing import Tuple, Optional
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from common.world import World
from common.app import AppManager
from utils.sleep_utils import sleep_until

class DreamMode:
    """
    梦境模式类
    自动化处理游戏中的梦境玩法，包括开始游戏、招募、丢骰子、战斗等流程
    """
    
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, log_queue=None):
        """
        初始化梦境模式
        
        :param device_manager: 设备管理器
        :param ocr_handler: OCR处理器
        :param log_queue: 日志队列，用于向主进程发送日志
        """
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.log_queue = log_queue
        self.logger = logging.getLogger("dldbz.dream")
        
        # 初始化AppManager和World对象
        self.app_manager = AppManager(device_manager)
        self.world = World(device_manager, ocr_handler, self.app_manager)
        
        # 初始化变量
        self.loop_count = 0
        self.max_loops = 10000
        
        # 统计信息
        self.stats = {
            "total_loops": 0,
            "successful_recruits": 0,
            "successful_battles": 0,
            "successful_events": 0,
            "total_awards": 0,  # 总奖励积分
            "start_time": time.time(),
            "total_time": 0.0
        }
        
        # 图片识别阈值
        self.image_threshold = 0.8
        self.battle_threshold = 0.7
        self.click_wait_interval = 0.5  # 点击等待间隔
        
        # 坐标配置（需要根据实际游戏界面调整）
        self.coordinates = {
            # 丢骰子相关
            'dice_select': (1135, 592),
            'dice_confirm': (641, 290),
            
            # 事件相关
            'event_option2': (1102, 406),
            'event_confirm': (800, 480),
            'event_leave': (1117, 644),
            
            # 战斗相关
            'battle_start': (140, 1115),
            'auto_battle_confirm': (1096, 653),
            'battle_settlement': (1152, 598),
            
            # 奖励结算相关
            'reward_confirm': (640, 580),
        }
        
        # OCR识别区域
        self.ocr_regions = {
            'end_step': (918, 639, 980, 666),  # 终点步数识别区域
            'step_count': (1136, 641, 1195, 664),  # 步数识别区域
        }
        
        self.logger.info("梦境模式初始化完成")

    def log_message(self, message: str):
        """记录日志消息"""
        self.logger.info(message)
        if self.log_queue:
            try:
                self.log_queue.put(message)
            except Exception as e:
                self.logger.error(f"发送日志到队列失败: {e}")

    def find_image(self, image_name: str, threshold: Optional[float] = None) -> Optional[Tuple[int, int]]:
        """
        查找图片位置
        
        :param image_name: 图片名称
        :param threshold: 识别阈值
        :return: 找到的坐标，未找到返回None
        """
        if threshold is None:
            threshold = self.image_threshold
            
        image = self.device_manager.get_screenshot()
        self.logger.info(f"查找图片: {image_name}, 阈值: {threshold}")
        result = self.ocr_handler.match_image(image, image_name, threshold)
        if result:
            time.sleep(self.click_wait_interval)
        return result

    def click_position(self, x: int, y: int):
        """
        点击指定位置
        
        :param x: X坐标
        :param y: Y坐标
        :param duration: 点击持续时间(毫秒)
        """
        self.device_manager.click(x, y)

    def delay(self, seconds: float):
        """
        延迟等待
        
        :param seconds: 等待秒数
        """
        time.sleep(seconds)
        self.logger.debug(f"延迟等待: {seconds}秒")

    def ocr_text(self, region: Tuple[int, int, int, int]) -> str:
        """
        OCR识别文字
        
        :param region: 识别区域 (x1, y1, x2, y2)
        :return: 识别到的文字
        """
        image = self.device_manager.get_screenshot()
        result = self.ocr_handler.recognize_text(image,region,rec_char_type="digit")
        if result and len(result) > 0:
            return result[0]['text']
        return ""

    def send_stats_report(self):
        """发送统计报告"""
        if self.log_queue:
            try:
                # 计算总用时
                self.stats["total_time"] = time.time() - self.stats["start_time"]
                total_minutes = self.stats["total_time"] / 60
                
                report = f"""REPORT_DATA__
轮次: {self.stats["total_loops"]} 次
成功招募: {self.stats["successful_recruits"]} 次
成功战斗: {self.stats["successful_battles"]} 次
成功事件: {self.stats["successful_events"]} 次
总奖励积分: {self.stats["total_awards"]} 分
总用时: {total_minutes:.1f} 分钟"""
                
                self.log_queue.put(report)
                self.logger.info("统计报告已发送")
            except Exception as e:
                self.logger.error(f"发送统计报告失败: {e}")

    def send_realtime_stats(self):
        """发送实时统计数据"""
        if self.log_queue:
            try:
                # 计算总用时
                self.stats["total_time"] = time.time() - self.stats["start_time"]
                total_minutes = self.stats["total_time"] / 60
                
                report = f"""REPORT_DATA__
轮次: {self.stats["total_loops"]} 次
成功招募: {self.stats["successful_recruits"]} 次
成功战斗: {self.stats["successful_battles"]} 次
成功事件: {self.stats["successful_events"]} 次
总奖励积分: {self.stats["total_awards"]} 分
总用时: {total_minutes:.1f} 分钟"""
                
                self.log_queue.put(report)
            except Exception as e:
                self.logger.error(f"发送实时统计失败: {e}")

    def update_stats(self, stat_type: str, increment: int = 1):
        """
        更新统计数据
        
        :param stat_type: 统计类型
        :param increment: 增量
        """
        if stat_type in self.stats:
            self.stats[stat_type] += increment
            self.logger.debug(f"更新统计: {stat_type} = {self.stats[stat_type]}")
            # 实时发送统计数据更新
            self.send_realtime_stats()

    def run(self, config_params=None):
        """
        运行梦境模式主循环
        
        :param config_params: 配置参数字典
        """
        # 更新配置参数
        if config_params:
            self.update_config(config_params)
        
        self.log_message("开始运行梦境模式")
        
        try:
            while self.loop_count < self.max_loops:
                self.log_message(f"梦境循环第 {self.loop_count + 1} 次")
                
                # 检查开始游戏界面
                if self.check_start_game():
                    continue
                
                # 检查丢骰子界面
                if self.check_dice_interface():
                    continue
                
                # 检查各种格子类型
                if self.check_grid_types():
                    continue
                
                # 检查放弃游戏
                if self.check_give_up():
                    continue
                
                # 检查奖励结算
                if self.check_reward_settlement():
                    self.device_manager.double_click(1248, 560)
                    self.loop_count += 1
                    self.stats["total_loops"] = self.loop_count
                    self.send_realtime_stats()
                    continue
                # 短暂延迟避免过度占用CPU
                self.delay(0.1)
                
        except KeyboardInterrupt:
            self.log_message("梦境模式被用户中断")
        except Exception as e:
            self.log_message(f"梦境模式运行异常: {e}")
            self.logger.exception("梦境模式异常详情")
        finally:
            self.send_stats_report()
            self.log_message("梦境模式结束")

    def update_config(self, config_params: dict):
        """
        更新配置参数
        
        :param config_params: 配置参数字典
        """
        if "max_loops" in config_params:
            self.max_loops = config_params["max_loops"]
        
        if "image_threshold" in config_params:
            self.image_threshold = config_params["image_threshold"]
        
        if "battle_threshold" in config_params:
            self.battle_threshold = config_params["battle_threshold"]
        
        if "click_wait_interval" in config_params:
            self.click_wait_interval = config_params["click_wait_interval"]
        
        if "coordinates" in config_params:
            # 更新坐标配置
            for key, value in config_params["coordinates"].items():
                if isinstance(value, list) and len(value) == 2:
                    self.coordinates[key] = tuple(value)
        
        self.logger.info(f"配置已更新: max_loops={self.max_loops}, image_threshold={self.image_threshold}, click_wait_interval={self.click_wait_interval}")

    def check_start_game(self) -> bool:
        """
        检查并处理开始游戏界面
        
        :return: 是否处理了开始游戏
        """
        # 查找开始游戏按钮
        start_pos = self.find_image("assets/dream/kaishi.png")
        if start_pos:
            self.log_message("找到开始游戏界面")
            # 点击开始游戏按钮
            self.click_position(*start_pos)
            self.delay(self.click_wait_interval)
            return True
        
        start_buff = self.check_start_buff()
        if start_buff:
            self.log_message("找到起始buff界面")
            self.click_position(*start_buff)
            self.delay(self.click_wait_interval)
            return True
        
        start_buff_next = self.check_start_buff_next()
        if start_buff_next:
            self.log_message("找到起始buff界面")
            self.click_position(*start_buff_next)
            self.delay(self.click_wait_interval)
            return True

        recruit_btn_1 = self.check_recruit_1()
        if recruit_btn_1:
            self.click_position(*recruit_btn_1)
            self.delay(self.click_wait_interval)
            self.process_recruit(report=False)
            self.delay(self.click_wait_interval)
            return True

        recruit_btn_2 = self.check_recruit_2()
        if recruit_btn_2:
            self.click_position(*recruit_btn_2)
            self.delay(self.click_wait_interval)
            self.process_recruit(report=False)
            self.delay(self.click_wait_interval)
            return True

        game_start = self.check_game_start()
        if game_start:
            self.click_position(*game_start)
            self.delay(self.click_wait_interval)
            self.delay(6.0)
            self.log_message("开始游戏流程完成")
            return True
        
        return False
    
    def check_start_buff_next(self) -> Optional[Tuple[int, int]]:
        """
        检查并处理起始buff界面
        
        :return: 是否处理了起始buff界面
        """
        start_buff_pos = self.find_image("assets/dream/start_buff_next.png")
        if start_buff_pos:
            self.log_message("找到起始buff界面")
            return start_buff_pos
        return None
    
    def check_start_buff(self) -> Optional[Tuple[int, int]]:
        """
        检查并处理起始buff界面
        
        :return: 是否处理了起始buff界面
        """
        start_buff_pos = self.find_image("assets/dream/start_buff.png")
        if start_buff_pos:
            self.log_message("找到起始buff界面")
            return start_buff_pos
        return None
    
    def check_recruit_1(self) -> Optional[Tuple[int, int]]:
        """
        检查并处理招募界面
        
        :return: 是否处理了招募界面
        """
        # 查找招募相关图片
        recruit_pos = self.find_image("assets/dream/zhaomu_1.png")
        if recruit_pos:
            self.log_message("找到招募1界面")
            return recruit_pos
        return None
    
    def check_recruit_2(self) -> Optional[Tuple[int, int]]:
        """
        检查并处理招募界面
        
        :return: 是否处理了招募界面
        """
        # 查找招募相关图片
        recruit_pos = self.find_image("assets/dream/zhaomu_2.png")
        if recruit_pos:
            self.log_message("找到招募2界面")
            return recruit_pos
        return None
    
    def check_game_start(self) -> Optional[Tuple[int, int]]:
        """
        检查并处理游戏开始界面
        :return: 是否处理了游戏开始界面
        """
        game_start_pos = self.find_image("assets/dream/game_start.png")
        if game_start_pos:
            self.log_message("找到游戏开始界面")
            return game_start_pos
        return None

    def process_recruit(self, report: bool = True):
        """处理招募流程"""
        self.log_message("开始处理招募")

        self.click_position(648, 220)
        self.delay(self.click_wait_interval)

        self.click_position(218, 600)
        self.delay(self.click_wait_interval)
        
        self.log_message("招募流程完成")
        if report:
            self.update_stats("successful_recruits")

    def check_dice_interface(self) -> bool:
        """
        检查并处理丢骰子界面
        
        :return: 是否处理了丢骰子界面
        """
        # 查找丢骰子相关图片
        try:
            end_step_str = self.get_end_step()
            dice_count_str = self.get_dice_count()
            start_point = self.check_start_point()
            # 检查是否为有效数字
            if end_step_str.isdigit() and dice_count_str.isdigit():
                end_step = int(end_step_str)
                dice_count = int(dice_count_str)
                self.log_message(f"识别到终点步数: {end_step} 骰子数量: {dice_count}")
                self.process_dice(end_step, dice_count, start_point)
                return True
            elif end_step_str.isdigit() or dice_count_str.isdigit():
                game_exit_btn = self.check_game_exit_btn()
                if game_exit_btn is None:
                    return False
                self.click_position(*game_exit_btn)
                self.delay(self.click_wait_interval)
                sleep_until(self.world.click_confirm_yes)
                self.delay(self.click_wait_interval)
                return True

        except (ValueError, TypeError):
            # OCR识别失败或转换失败
            return False
        return False

    def process_dice(self,end_step:int,dice_count:int,start_point:bool):
        """处理丢骰子流程"""
        self.log_message("开始处理丢骰子")
        
        # 判断回合数
        try:
            if start_point:
                self.log_message("检测到开始点，准备丢骰子")
                 # 第一回合，点击骰子走一步
                x, y = self.coordinates['dice_select']
                self.click_position(x, y)
                self.delay(self.click_wait_interval)
                
                # 点击确认
                x, y = self.coordinates['dice_confirm']
                self.click_position(x, y)
                self.delay(self.click_wait_interval)
                
                self.log_message("丢骰子流程完成")
                return
            else:  # 第二回合阈值
                self.log_message("检测到第二回合，准备放弃游戏")
                # 点击放弃游戏
                game_exit_btn = self.check_game_exit_btn()
                if game_exit_btn is None:
                    return
                
                self.click_position(*game_exit_btn)
                self.delay(self.click_wait_interval)
                
                sleep_until(self.world.click_confirm_yes)
                self.delay(self.click_wait_interval)
                return
        except ValueError:
            self.log_message("处理丢骰子流程")

    def check_grid_types(self) -> bool:
        """
        检查并处理各种格子类型
        
        :return: 是否处理了格子
        """
        # 检查招募格子
        if self.check_recruit_grid():
            return True
        
        # 检查事件后续格子
        if self.check_event_follow_grid():
            return True
            
        # 检查事件格子
        if self.check_event_grid():
            return True
            
        # 检查事件后续格子
        if self.check_event_follow_grid():
            return True
            
        # 检查战斗格子
        if self.check_battle_grid():
            return True
        
        if self.process_battle():
            return True
            
        return False
    
    def check_game_exit_btn(self) -> Optional[Tuple[int, int]]:
        """
        检查游戏退出按钮
        
        :return: 是否处理了游戏退出按钮
        """
        game_exit_btn = self.find_image("assets/dream/game_exit_btn.png")
        if game_exit_btn:
            return game_exit_btn
        return None
    
    def check_start_point(self) -> bool:
        """
        检查开始点
        
        :return: 是否处理了开始点
        """
        start_point = self.find_image("assets/dream/start_point.png")
        if start_point:
            self.log_message("找到开始点")
            return True
        return False

    def check_recruit_grid(self) -> bool:
        """
        检查招募格子
        
        :return: 是否处理了招募格子
        """
        # 查找招募相关图片
        recruit_pos = self.find_image("assets/dream/zhaomu.png")
        if recruit_pos:
            self.log_message("找到招募格子")
            self.process_recruit()
            return True
        return False

    def check_event_grid(self) -> bool:
        """
        检查事件格子
        
        :return: 是否处理了事件格子
        """
        # 查找事件相关图片
        event_pos = self.find_image("assets/dream/likai.png")
        if event_pos:
            self.log_message("找到事件格子")
            self.process_event()
            return True
        return False

    def process_event(self):
        """处理事件格子"""
        self.log_message("开始处理事件")
        
        # 点击选项二
        x, y = self.coordinates['event_option2']
        self.click_position(x, y)
        self.delay(self.click_wait_interval)
        
        # 点击确认
        x, y = self.coordinates['event_confirm']
        self.click_position(x, y)
        self.delay(self.click_wait_interval)
        
        self.log_message("事件处理完成")

    def check_event_follow_grid(self) -> bool:
        """
        检查事件后续格子
        
        :return: 是否处理了事件后续格子
        """
        # 查找事件后续相关图片
        event_follow_pos = self.find_image("assets/dream/maozhua.png")
        if event_follow_pos:
            self.log_message("找到事件后续格子")
            self.process_event_follow()
            return True
        return False

    def process_event_follow(self):
        """处理事件后续格子"""
        self.log_message("开始处理事件后续")
        
        # 点击离开
        x, y = self.coordinates['event_leave']
        self.click_position(x, y)
        self.delay(self.click_wait_interval)
        
        # 点击确认
        x, y = self.coordinates['event_confirm']
        self.click_position(x, y)
        self.delay(self.click_wait_interval)
        
        self.log_message("事件后续处理完成")
        self.update_stats("successful_events")

    def check_battle_grid(self) -> bool:
        """
        检查战斗格子
        
        :return: 是否处理了战斗格子
        """
        battle_skip = self.find_image("assets/dream/battle_skip.png")
        if battle_skip:
            self.log_message("找到战斗跳过")
            self.click_position(*battle_skip)
            self.delay(self.click_wait_interval)
            return True
        # 查找战斗相关图片
        battle_pos = self.find_image("assets/dream/battle_start.png")
        if battle_pos:
            self.log_message("找到战斗格子")
            # 点击自动战斗
            self.click_position(*battle_pos)
            self.delay(self.click_wait_interval)
            self.process_battle()
            return True
        return False

    def process_battle(self):
        """处理战斗流程"""
        pos = self.is_battle_zhineng()
        if pos:
            self.click_position(*pos)
            self.delay(self.click_wait_interval)
            # 点击确认自动战斗
            x, y = self.coordinates['auto_battle_confirm']
            self.click_position(x, y)
            self.delay(2.0)
        
        # 等待战斗结束

        if self.is_battle_end():
            self.device_manager.double_click(1248, 560)
            self.delay(0.5)

        # 等待战斗离开界面
        if self.is_battle_leave():
            # 等待战斗结束，点击结算
            x, y = self.coordinates['battle_settlement']
            self.click_position(x, y)
            self.delay(self.click_wait_interval)
            self.update_stats("successful_battles")
            self.log_message("战斗流程完成")
            self.delay(0.5)

    def check_give_up(self) -> bool:
        """
        检查放弃游戏界面
        
        :return: 是否处理了放弃游戏
        """
        # 查找放弃游戏相关图片
        give_up_pos = self.find_image("assets/dream/game_exit.png")
        if give_up_pos:
            self.log_message("找到放弃游戏界面")
            self.click_position(*give_up_pos)
            self.delay(self.click_wait_interval)
            sleep_until(self.world.click_confirm_yes)
            self.delay(self.click_wait_interval)
            return True
        return False

    def check_reward_settlement(self) -> bool:
        """
        检查奖励结算界面
        
        :return: 是否处理了奖励结算
        """
        # 查找奖励结算相关图片
        settlement_pos = self.find_image("assets/dream/game_settle.png")
        if settlement_pos:
            self.log_message("找到奖励结算界面")
            award_count = self.get_award_count()
            if award_count > 0:
                self.log_message(f"找到奖励: {award_count} 个")
                # 累加奖励积分到统计中
                self.stats["total_awards"] += award_count
                self.log_message(f"累计奖励积分: {self.stats['total_awards']} 分")
            else:
                self.log_message("没有找到奖励")
            # 点击确认奖励
            x, y = self.coordinates['reward_confirm']
            self.click_position(x, y)
            self.delay(self.click_wait_interval)
            return True
        return False
    
    # 获取终点步数
    def get_end_step(self):
        """获取终点步数"""
        end_step = self.ocr_text(self.ocr_regions['end_step'])
        return end_step
    
    #  获取骰子数量
    def get_dice_count(self):
        """获取骰子数量"""
        dice_count = self.ocr_text(self.ocr_regions['step_count'])
        return dice_count
    
    def get_award_count(self):
        """获取奖励数量"""
        image = self.device_manager.get_screenshot()    
        if image is None:
            return 0
        award_count = self.ocr_handler.recognize_text(image, (532, 506, 617, 535), rec_char_type="digit")
        if award_count and len(award_count) > 0:
            try:
                # OCR返回的是字典列表，需要提取text字段
                text = award_count[0]['text']
                return int(text) if text.isdigit() else 0
            except (KeyError, ValueError, IndexError):
                self.logger.warning("奖励数量识别失败")
                return 0
        return 0
    
    def is_battle_leave(self):
        """检查战斗是否离开"""
        image = self.device_manager.get_screenshot()
        if image is None:
            return False
        battle_leave = self.ocr_handler.match_image(image, "assets/dream/battle_leave.png")
        return battle_leave
    
    def is_battle_zhineng(self):
        """检查战斗是否自动"""
        image = self.device_manager.get_screenshot()
        if image is None:
            return False
        battle_auto = self.ocr_handler.match_image(image, "assets/dream/zhineng.png", region=(472, 647,507, 667),
                                                   gray=True, threshold=0.9)
        return battle_auto
    
    def is_battle_end(self):
        """检查战斗是否结束"""
        image = self.device_manager.get_screenshot()
        if image is None:
            return False
        point_color = [
            (102, 33, 'F0EBE8', 1), 
            (92, 67, 'E7E3E2', 1), 
            (182, 64, 'F0EBE7', 1), 
            (182, 32, 'F0ECE9', 1), 
            (291, 76, 'F7F2EE', 1),
            (354, 29, 'F2EEED', 1), 
        ]
        battle_end = self.ocr_handler.match_point_color(image,point_color)
        if battle_end:
            return True
        return False

    def cleanup(self):
        """清理资源"""
        self.log_message("清理梦境模式资源")
        # TODO: 实现资源清理 