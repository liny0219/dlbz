import time
from utils import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Optional, Any, Tuple
from PIL import Image
from utils.singleton import singleton

@singleton
class Battle:
    """
    战斗模块
    负责实现战斗相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler,app_manager:AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler

    def in_battle(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在战斗中。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有6点
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗中")
            return False
        points_colors = [
            (116, 19, "87878C", 1),
            (125, 19, "878790", 1),
            (116, 29, "8F9096", 1),
            (125, 29, "8F8F98", 1),
            (131, 26, "9999A1", 1),
            (139, 26, "9A9BA3", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results):
            logger.debug("检测到在战斗中")
            return True
        else:
            logger.debug("不在战斗中")
            return False

    def in_battle_round(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在战斗回合中。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有6点
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗回合中")
            return False
        points_colors = [
            (1061,639, "FFFFFF", 1),
            (1061,639, "FFFFFF", 1),
            (1060,659, "FFFFFF", 1),
            (1133,650, "FFFFFF", 1),
            (1131,665, "FFFFFF", 1)
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results) and self.in_battle(image):
            logger.debug("检测到在战斗回合中")
            return True
        else:
            logger.debug("不在战斗回合中")
            return False

    def dead(self, image: Optional[Image.Image] = None, role_id: int = 1) -> bool:
        """
        判断当前是否死亡。
        :param image: 可选，外部传入截图
        :param role_id: 可选，角色id，默认0代表任意角色死亡判断,1-8代表具体角色死亡判断
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否死亡")
            return False
        # 1到8号角色血条检测
        points_colors = [
            (1100,84, "1A1A1A", 1),
            (1100,228, "1A1A1A", 1),
            (1100,370, "1A1A1A", 1),
            (1100,516, "1A1A1A", 1),
            (1200,86, "1A1A1A", 1),
            (1200,230, "1A1A1A", 1),
            (1200,372, "1A1A1A", 1),
            (1200,665, "1A1A1A", 1),
        ]
        if role_id == 0:
            # 任意角色死亡判断
            results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
            return any(results) and self.in_battle(image)
        else:
            # 具体角色死亡判断
            role_point = points_colors[role_id-1]
            return self.ocr_handler.match_point_color(image, role_point[0], role_point[1], role_point[2], role_point[3]) and self.in_battle(image)
    
    def in_skill(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在技能释放中。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (684,201, "E8EBF0", 1),
            (718,205, "E8EBF0", 1),
            (761,207, "272626", 1),
            (759,176, "1F1E1E", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        return all(results) and self.in_battle(image)

    def in_sp_skill(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在技能释放中。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (661,152, "F8F8FE", 1),
            (633,173, "E8E9EA", 1),
            (705,173, "E8E9EA", 1),
            (660,169, "F8F8FE", 1),
        ]
        # 批量判断
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        return all(results) and self.in_battle(image)
    
    def auto_battle(self, interval:float = 0.2,max_times:int = 30) -> bool:
        """
        自动战斗
        """
        screenshot = self.device_manager.get_screenshot()
        if not self.in_battle_round(screenshot):
            return False
        times = 0
        done_click_auto = False
        while True: 
            if self.ocr_handler.match_click_text(["委托战斗开始"],region=(30,580,1240,700),image=screenshot):
                time.sleep(0.5)
                done_click_auto = True
                logger.info("点击委托战斗开始")
                return True
            if not done_click_auto and self.ocr_handler.match_click_text(["委托"],region=(30,580,1240,700),image=screenshot):
                logger.info("点击委托")
                time.sleep(interval)
            screenshot = self.device_manager.get_screenshot()
            times += 1
            if times >= max_times:
                return False

    def exit_battle(self, interval:int = 1,max_times:int = 5) -> bool:
        """
        退出战斗
        """
        if not self.in_battle_round():
            return False
        times = 0
        while True: 
            if self.ocr_handler.match_click_text(["是"],region=(293,172,987,548)):
                continue
            if self.ocr_handler.match_click_text(["放弃"],region=(30,580,1240,700)):
                continue
            in_battle = self.in_battle()
            if not self.ocr_handler.match_texts(["攻击"],region=(293,172,987,548)) and not in_battle:
                return True
            time.sleep(interval)
            times += 1
            if times >= max_times:
                return False

    # ================== 战斗指令执行相关方法 ==================
    def cmd_normal_attack(self, index: int = 1):
        """
        普通攻击
        :param index: 角色索引
        """
        logger.info(f"[Battle] 普通攻击，角色索引: {index}")
        # TODO: 实现点击普通攻击按钮逻辑

    def cmd_switch_and_attack(self, index: int = 1):
        """
        切换并攻击
        :param index: 角色索引
        """
        logger.info(f"[Battle] 切换并攻击，角色索引: {index}")
        # TODO: 实现切换角色并攻击逻辑

    def cmd_boost(self):
        """
        设置全能量
        """
        logger.info("[Battle] 设置全能量（Boost）")
        # TODO: 实现全能量逻辑

    def cmd_attack(self):
        """
        执行攻击
        """
        logger.info("[Battle] 执行攻击（Attack）")
        # TODO: 实现攻击逻辑

    def cmd_switch_all(self):
        """
        切换前后排
        """
        logger.info("[Battle] 切换前后排（SwitchAll）")
        # TODO: 实现切换前后排逻辑

    def cmd_sp_skill(self, index: int = 1):
        """
        特殊技能（SP）
        :param index: 技能索引
        """
        logger.info(f"[Battle] 释放特殊技能（SP），技能索引: {index}")
        # TODO: 实现SP技能逻辑

    def cmd_reset(self):
        """
        重置技能和能量
        """
        logger.info("[Battle] 重置技能和能量（Reset）")
        # TODO: 实现重置逻辑

    def cmd_switch(self, from_: int = 1, to: int = 2):
        """
        切换特定角色位置
        :param from_: 源角色索引
        :param to: 目标角色索引
        """
        logger.info(f"[Battle] 切换角色，从 {from_} 到 {to}")
        # TODO: 实现角色切换逻辑

    def cmd_wait(self, seconds: float = 1.0):
        """
        等待指定时间
        :param seconds: 等待秒数
        """
        logger.info(f"[Battle] 等待 {seconds} 秒")
        time.sleep(seconds)

    def cmd_skip(self, seconds: float = 1.0):
        """
        跳过指定时间（可用于跳过动画等）
        :param seconds: 跳过秒数
        """
        logger.info(f"[Battle] 跳过 {seconds} 秒（Skip）")
        # TODO: 实现跳过逻辑
        time.sleep(seconds)

    def cmd_click(self, x: int, y: int):
        """
        点击指定坐标
        :param x: X 坐标
        :param y: Y 坐标
        """
        logger.info(f"[Battle] 点击坐标 ({x}, {y})")
        self.device_manager.click(x, y)

    def cmd_auto(self):
        """
        自动战斗/脚本结束后的自动操作
        """
        logger.info("[Battle] 自动战斗/脚本结束自动操作（Auto）")
        # TODO: 实现自动战斗逻辑

    def cmd_battle_start(self):
        """
        战斗开始
        """
        logger.info("[Battle] 战斗开始（BattleStart）")
        # TODO: 实现战斗开始逻辑

    def cmd_battle_end(self):
        """
        战斗结束
        """
        logger.info("[Battle] 战斗结束（BattleEnd）")
        # TODO: 实现战斗结束逻辑

    def cmd_cmd_start(self):
        """
        指令开始
        """
        logger.info("[Battle] 指令开始（CmdStart）")
        # TODO: 实现指令开始逻辑

    def cmd_cmd_end(self):
        """
        指令结束
        """
        logger.info("[Battle] 指令结束（CmdEnd）")
        # TODO: 实现指令结束逻辑

    def cmd_finish(self):
        """
        脚本结束
        """
        logger.info("[Battle] 脚本结束（Finish）")
        # TODO: 实现脚本结束逻辑

    def cmd_check_dead(self, role_id: int = 0):
        """
        检查是否有角色死亡
        :param role_id: 角色id，0为任意角色
        """
        logger.info(f"[Battle] 检查角色是否死亡，role_id={role_id}")
        return self.dead(role_id=role_id)
