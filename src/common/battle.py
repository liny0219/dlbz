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
        self.role_base_pos = (1100, 80)
        self.rols_base_y_offset = 140
        self.skill_base_x = [800,1020,1100,1200]
        self.skill_base_y = 200
        self.skill_base_y_offset = 105
        self.wait_time = 0.1
        self.wait_drag_time = 0.3

    # ================== 战斗状态判断相关方法 ==================
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
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results:
            logger.debug("检测到在战斗中")
            time.sleep(self.wait_time)
            return True
        else:
            logger.debug("不在战斗中")
            return False

    def in_round(self, image: Optional[Image.Image] = None) -> bool:
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
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results and self.in_battle(image):
            logger.debug("检测到在战斗回合中")
            time.sleep(self.wait_time)
            return True
        else:
            logger.debug("不在战斗回合中")
            return False

    def in_sp_on(self, image: Optional[Image.Image] = None) -> bool:
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
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)

    def in_skill_on(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (799, 309, '282A29', 1),
            (800, 421, '252726', 1),
            (800, 527, '252628', 1)
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)
    
    def in_auto_off(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (460, 657, '050004', 1),
            (521, 661, '050004', 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)

    def in_auto_on(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (1099, 678, 'CAE7E5', 1),
            (991, 651, '1BA4B4', 1),
            (1199, 648, '1BAABB', 1),
            (871, 654, '010002', 1),
            (524, 656, '262427', 1),
            (461, 656, '252326', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)
    
    def in_switch_on(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (767, 656, '262125', 1),
            (816, 655, '211F22', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)

    def in_switch_off(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (818, 660, '050004', 1),
            (767, 658, '060004', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)
    
    def in_boost_on(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (918, 658, '7C7C7C', 1),
            (869, 657, '848283', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)

    def in_boost_off(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (918, 659, '0B090C', 1),
            (872, 660, '010002', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors)
        return results and self.in_battle(image)

    def in_front_on(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在前排。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False
        points_colors = [
            (791, 27, 'C8CAC9', 1),
            (796, 30, 'E4E8E7', 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        logger.debug(f"判断当前是否在前排: {results}")
        return results and self.in_skill_on(image)
    
    def in_back_on(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在后排。
        :param image: 可选，外部传入截图
        :return: bool
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在技能释放中")
            return False  
        points_colors = [
            (785, 26, 'F3F5F2', 1),
            (792, 15, 'C7C8C3', 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        logger.debug(f"判断当前是否在后排: {results}")
        return results and self.in_skill_on(image)
            

    # ================== 战斗相关方法 ==================
    def auto_battle(self, interval:float = 0.2,max_times:int = 30) -> bool:
        """
        自动战斗
        """
        screenshot = self.device_manager.get_screenshot()
        if not self.in_round(screenshot):
            return False
        times = 0
        while True: 
            times += 1
            if times >= max_times:
                return False
            if self.in_auto_on(screenshot):
                logger.info("点击委托战斗开始")
                self.device_manager.click(1104, 643)
                return True
            if self.in_auto_off(screenshot):
                logger.info("点击委托")
                self.device_manager.click(491, 654)
            screenshot = self.device_manager.get_screenshot()
            time.sleep(interval)

    def check_dead(self, image: Optional[Image.Image] = None, role_id: int = 1) -> bool:
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
            results = self.ocr_handler.match_point_color(image, points_colors)
            return results and self.in_battle(image)
        else:
            # 具体角色死亡判断
            role_point = points_colors[role_id-1]
            return self.ocr_handler.match_point_color(image, [(role_point[0], role_point[1], role_point[2], role_point[3])]) and self.in_battle(image)
      
    def exit_battle(self, interval:int = 1,max_times:int = 5) -> bool:
        """
        退出战斗
        """
        if not self.in_round():
            return False
        times = 0
        while True: 
            time.sleep(interval)
            times += 1
            if times >= max_times:
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.ocr_handler.match_click_text(["是"],region=(293,172,987,548),image=screenshot):
                continue
            if self.ocr_handler.match_click_text(["放弃"],region=(30,580,1240,700),image=screenshot):
                continue
            if not self.in_battle(screenshot):
                return True

    # ================== 战斗指令执行相关方法 ==================
    def cmd_role(self, index: int = 1,skill: int = 1, bp: int = 0, x: int = 0, y: int = 0, switch: bool = False):
        """
        普通攻击
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        logger.info(f"[Battle] 选择角色，角色索引: {index},技能索引: {skill},倍率: {bp},坐标: ({x}, {y})")
        # 检查index 1-8
        # 检查skill 0-4
        # 检查bp 0-3
        if index < 1 or index > 8:
            logger.error(f"[Battle] 角色索引错误，index: {index}")
            return False
        if skill < 0 or skill > 4:
            logger.error(f"[Battle] 技能索引错误，skill: {skill}")
            return False
        if bp < 0 or bp > 3:
            logger.error(f"[Battle] 倍率错误，bp: {bp}")
            return False

        enemy_pos = None
        if x != 0 and y != 0:
            enemy_pos = (x,y)
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        skill_start = (self.skill_base_x[0], self.skill_base_y + (skill)*self.skill_base_y_offset)
        skill_end = (self.skill_base_x[bp], self.skill_base_y + (skill)*self.skill_base_y_offset)
        finish = False
        while True:
            screenshot = self.device_manager.get_screenshot()
            if finish and self.in_round(screenshot):
                logger.info("[Battle] 技能释放完成")
                return True
            if not finish and self.in_round(screenshot):
                logger.info("[Battle] 选择角色")
                self.device_manager.click(role_pos[0], role_pos[1])
            if not finish and self.in_skill_on(screenshot):
                logger.info("[Battle] 在技能面板")
                if switch:
                    logger.info("[Battle] 切换角色")
                    while True:
                        if self.in_back_on(screenshot):
                            logger.info("[Battle] 切换角色完成")
                            break
                        if self.in_front_on(screenshot):
                            self.device_manager.click(1115, 640)
                        screenshot = self.device_manager.get_screenshot()
                        time.sleep(self.wait_time)
                if enemy_pos:
                    logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
                    self.device_manager.click(enemy_pos[0], enemy_pos[1])
                    time.sleep(self.wait_time + 0.2)
                if bp == 0:
                    logger.info(f"[Battle] 点击选择技能")
                    self.device_manager.click(skill_start[0], skill_start[1])
                else:
                    logger.info(f"[Battle] 拖动选择技能")
                    self.device_manager.press_and_drag_step(skill_start, skill_end, self.wait_drag_time)
                finish = True
            time.sleep(self.wait_time)
            
    def cmd_xrole(self, index: int = 1, skill: int = 1, bp: int = 1, x: int = 0, y: int = 0, switch: bool = True):
        """
        切换并攻击
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        logger.info(f"[Battle] 切换并攻击，角色索引: {index},技能索引: {skill},倍率: {bp},坐标: ({x}, {y})")
        self.cmd_role(index, bp, x, y, switch)  
        
    def cmd_boost(self):
        """
        全体加成
        """
        while True:
            screenshot = self.device_manager.get_screenshot()
            if self.in_boost_on(screenshot):
                logger.info("[Battle] 全体加成on")
                break
            if self.in_boost_off(screenshot):
                logger.info("[Battle] 全体加成off")
                self.device_manager.click(893, 654)
            time.sleep(0.2)

    def cmd_attack(self):
        """
        执行攻击
        """
        logger.info("[Battle] 执行攻击（Attack）")
        # TODO: 实现攻击逻辑

    def cmd_switch_all(self):
        """
        全员交替
        """
        while True:
            screenshot = self.device_manager.get_screenshot()
            if self.in_switch_on(screenshot):
                logger.info("[Battle] 全员交替on")
                break
            if self.in_switch_off(screenshot):
                logger.info("[Battle] 全员交替off")
                self.device_manager.click(792, 659)
            time.sleep(0.2)

    def cmd_sp_skill(self, index: int = 1):
        """
        特殊技能（SP）
        :param index: 技能索引
        """
        logger.info(f"[Battle] 释放特殊技能（SP），技能索引: {index}")
        # TODO: 实现SP技能逻辑
    
    def cmd_xsp_skill(self, index: int = 1):
        """
        特殊技能（XSP）
        :param index: 技能索引
        """
        logger.info(f"[Battle] 释放特殊技能（XSP），技能索引: {index}")
        # TODO: 实现XSP技能逻辑

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
        self.device_manager.long_click(1000, 300, seconds)

    def cmd_click(self, x: int, y: int):
        """
        点击指定坐标
        :param x: X 坐标
        :param y: Y 坐标
        """
        logger.info(f"[Battle] 点击坐标 ({x}, {y})")
        self.device_manager.click(x, y)

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

    def cmd_check_dead(self, role_id: int = 0):
        """
        检查是否有角色死亡
        :param role_id: 角色id，0为任意角色
        """
        logger.info(f"[Battle] 检查角色是否死亡，role_id={role_id}")
        return self.check_dead(role_id=role_id)
