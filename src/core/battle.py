import time
from utils import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Callable, Optional, Tuple
from PIL import Image
from utils.singleton import singleton
from common.config import Monster, config

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
        self.extra_skill_bp_pos = (570, 305)
        self.extra_bp_offset_x = [0, 778, 895, 982]
        self.role_base_pos = (1100, 80)
        self.rols_base_y_offset = 140
        self.skill_base_x = [800,1020,1100,1200]
        self.skill_base_y = 200
        self.skill_base_y_offset = 105
        self.wait_time = config.battle.wait_time
        self.wait_ui_time = config.battle.wait_ui_time
        self.wait_drag_time = config.battle.wait_drag_time
        self.battle_recognition_time = config.battle.battle_recognition_time

    # ================== 战斗状态判断相关方法 ==================
    def in_battle(self, image: Optional[Image.Image] = None, call_roll: bool = True,roll_count:int=2) -> bool:
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
            if not call_roll:
                logger.debug("不调用roll,不在战斗中")
                return False
            logger.debug("调用roll,不在战斗中")
            time.sleep(self.wait_time)
            image = self.device_manager.get_screenshot()
            result = self.in_battle(image, call_roll=roll_count>0,roll_count=roll_count-1)
            if result:
                logger.debug("调用roll后在战斗中")
                return True
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
            (798, 203, '28292B', 1),
            (718, 204, 'F8F6F7', 1),
            (772, 176, '1E1F21', 1)
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
            (518, 656, '252326', 1),
            (460, 657, '252326', 1),
            (537, 660, 'D9DADC', 1),
            (443, 661, 'E0E0E0', 1),
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
    def auto_battle(self, timeout:float = 10) -> bool:
        """
        自动战斗
        """
        screenshot = self.device_manager.get_screenshot()
        logger.debug("auto_battle 战斗场景中,等待回合")
        if not self.in_round(screenshot):
            return False
        start_time = time.time()
        is_auto_start = False
        while True: 
            if time.time() - start_time > timeout:
                logger.info(f"[battle]auto_battle 超时")
                return False
            time.sleep(0.4)
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None:
                logger.error("[battle]auto_battle 无法获取截图")
                return False
            if self.in_round(screenshot) and self.in_auto_off(screenshot):
                logger.info("点击委托")
                self.device_manager.click(491, 654)
                continue
            if self.in_auto_on(screenshot):
                logger.info("点击委托战斗开始")
                self.device_manager.click(1104, 643)
                is_auto_start = True
            if not self.in_auto_off(screenshot) and not self.in_auto_on(screenshot) and is_auto_start:
                logger.info("委托成功")
                return True

    def check_dead(self, role_id: int = 0, timeout:float = 1) -> bool:
        """
        判断当前是否死亡。
        :param image: 可选，外部传入截图
        :param role_id: 可选，角色id，默认0代表任意角色死亡判断,1-8代表具体角色死亡判断
        :return: bool
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info(f"[battle]check_dead没有检查到阵亡")
                return False
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
                results = False
                for idx, point in enumerate(points_colors):
                    if self.ocr_handler.match_point_color(image, [point],ambiguity=1):
                        logger.info(f"[battle]检测到角色死亡:角色{idx+1}")
                        return True
            else:
                # 具体角色死亡判断
                role_point = points_colors[role_id-1]
                results = self.ocr_handler.match_point_color(image, [(role_point[0], role_point[1], role_point[2], role_point[3])]) and self.in_battle(image)
                if results:
                    return True
            time.sleep(0.2)

    def reset_round(self, timeout:float = 10) -> bool:
        """
        重置回合
        """
        start_time = time.time()
        while not self.in_round() and self.in_battle():
            if time.time() - start_time > timeout:
                logger.info(f"[battle]reset_round 超时")
                return False
            self.device_manager.click(135,25)
            time.sleep(0.1)
        return True
            
    def exit_battle(self, timeout:float = 20) -> bool:
        """
        退出战斗
        """
        start_time = time.time()
        while not self.in_round():
            if time.time() - start_time > timeout:
                logger.info(f"[battle]exit_battle in_round 超时")
                return False
            self.device_manager.click(135,25)
            time.sleep(0.1)
        start_time = time.time()
        logger.info(f"[battle]exit_battle in_round")
        while True: 
            time.sleep(0.2)
            screenshot = self.device_manager.get_screenshot()
            if time.time() - start_time > timeout:
                logger.info(f"[battle]exit_battle 超时")
                return False
            # 顺序不能变,因为放弃会跟上面的确认战斗重叠
            if self.ocr_handler.match_texts(["选择放弃的话"],region=(293,172,987,548),image=screenshot):
                logger.info(f"[battle]exit_battle 选择放弃战斗")
                self.device_manager.click(800, 485)
                continue
            if self.ocr_handler.match_texts(["将放弃战斗"],region=(293,172,987,548),image=screenshot):
                logger.info(f"[battle]exit_battle 确认放弃战斗")
                self.device_manager.click(800, 485)
                return True
            if self.ocr_handler.match_click_text(["放弃"],region=(30,580,1240,700),image=screenshot):
                logger.info(f"[battle]exit_battle 点击放弃战斗")
                continue

    def switch_back_role(self, image: Optional[Image.Image] = None, timeout:float = 5) -> bool:
        """
        切换到后排角色
        """
        logger.debug("[Battle] 切换后排角色")
        if image is None:
            image = self.device_manager.get_screenshot()
        # 设置超时时间为5秒
        start_time = time.time()
        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                logger.info("[Battle] switch_back_role超时")
                return False
            if self.in_back_on(image):
                logger.debug("[Battle] 切换后排角色完成")
                time.sleep(self.wait_time + self.wait_ui_time)
                return True
            if self.in_front_on(image):
                logger.debug("[Battle] 点击切换后排角色")
                self.device_manager.click(1115, 640)
                time.sleep(self.wait_time + self.wait_ui_time)
            image = self.device_manager.get_screenshot()

    def cast_ex(self, index:int,bp:int = 0, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = False) -> bool:
        """
        使用ex技能
        """
        return self.cast_extra_skill(index, bp, role_id, x, y,
                                  normalize_pos=[(800, 210),(910, 210)],
                                  click_pos=[(945, 568)],
                                  switch=switch)
            
    def cast_pet(self, index:int, bp:int = 0, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = False) -> bool:
        """
        使用宠物
        """
        return self.cast_extra_skill(index, bp, role_id, x, y,
                                  normalize_pos=[(910, 210),(1080, 210)],
                                  click_pos=[(945, 533)],
                                  switch=switch)
                
    def cast_extra_skill(self, index:int, bp:int = 0, role_id:int = 0, 
                      x: int = 0, y: int = 0,
                      switch: bool = False,
                      normalize_pos:list[Tuple[int, int]] = [],
                      click_pos:list[Tuple[int, int]] = []) -> bool:
        """
        使用ex技能
        """
        enemy_pos = None
        if index < 1 or index > 4:
            logger.error(f"[Battle] 角色索引错误，index: {index}")
            return False
        if role_id < 0 or role_id > 4:
            logger.error(f"[Battle] 作用角色索引错误，role_id: {role_id}")
            return False
        if bp < 0 or bp > 3:
            logger.error(f"[Battle] 宠物bp错误，bp: {bp}")
            return False
        if x != 0 and y != 9:
            enemy_pos = [x, y]
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        while True:
            screenshot = self.device_manager.get_screenshot()
            if self.in_round(screenshot):
                logger.info("[Battle] 战斗回合中, 选择角色")
                self.device_manager.click(role_pos[0], role_pos[1])
                time.sleep(self.wait_time)
                screenshot = self.device_manager.get_screenshot()
                continue
            if not self.in_battle(screenshot):
                return False
            if self.in_skill_on(screenshot):
                if switch and not self.switch_back_role(screenshot):
                    return False
                if enemy_pos is not None:
                    self.device_manager.click(*enemy_pos)
                    logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
                    time.sleep(self.wait_time)
                if  not self.in_sp_on(screenshot):
                    logger.info("[Battle] 技能界面中,切换额外技能界面")
                    self.device_manager.click(696, 96)
                    time.sleep(self.wait_time + self.wait_ui_time)
                    screenshot = self.device_manager.get_screenshot()
                if  self.in_sp_on(screenshot):
                    logger.info("[Battle] 额外技能界面")
                    # 点击修正坐标1与修正坐标2,兼容必杀技\支炎兽\ex技能时点击必杀选项,切换到必杀选项
                    for pos in normalize_pos:
                        self.device_manager.click(pos[0], pos[1])
                    time.sleep(self.wait_time + self.wait_ui_time)
                    logger.info("[Battle] 校正界面")
                    if bp > 0:
                        logger.info(f"[Battle] 拖动选择BP{bp}")
                        self.device_manager.press_and_drag_step(
                            self.extra_skill_bp_pos,
                            (self.extra_bp_offset_x[bp], self.extra_skill_bp_pos[1]),
                            duration=0.5
                        )
                        time.sleep(self.wait_time + self.wait_ui_time)
                    # 点击发动按钮,兼容必杀技\支炎兽\ex技能时点击必杀发动选项
                    for pos in click_pos:
                        self.device_manager.click(pos[0], pos[1])
                    logger.info(f"[Battle] 点击发动按钮")
                    time.sleep(self.wait_time + self.wait_ui_time)

                    if role_id != 0:
                        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
                        time.sleep(0.5)
                        self.device_manager.click(*role_pos)
                        logger.info(f"[Battle] 点击配置角色{role_id} {role_pos}")
                        time.sleep(self.wait_time + self.wait_ui_time)
                    return True       

    def transform(self, index: int = 1, switch: bool = False, timeout:float = 15) -> bool:
        """
        切换形态
        :param index: 角色索引
        :param switch: 是否切换角色
        """
        if index < 1 or index > 4:
            logger.error(f"[Battle] 角色索引错误，index: {index}")
            return False
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info('[battle]transform 超时')
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_round(screenshot):
                self.device_manager.click(role_pos[0], role_pos[1])
                time.sleep(self.wait_time + self.wait_ui_time)
                continue
            if not self.in_battle(screenshot):
                return False
            if self.in_skill_on(screenshot):
                if switch and not self.switch_back_role(screenshot):
                    return False
                self.device_manager.click(960, 40)
                logger.info(f"[Battle] 点击潜力切换按钮")
                time.sleep(self.wait_ui_time)
                while True:
                    time.sleep(self.wait_time)
                    screenshot = self.device_manager.get_screenshot()
                    if self.in_skill_on(screenshot):
                        self.device_manager.click(135,25)
                        logger.info(f"[Battle] 点击收起技能栏")
                        while not self.in_skill_on(screenshot):
                            time.sleep(self.wait_time)
                            screenshot = self.device_manager.get_screenshot()
                        return True

    def cast_sp(self, index:int, role_id:int = 0, x: int = 0, y: int = 0, 
                switch: bool = False, timeout:float = 10) -> bool:
        enemy_pos = None
        if index < 1 or index > 4:
            logger.error(f"[Battle] 角色索引错误，index: {index}")
            return False
        if role_id < 0 or role_id > 4:
            logger.error(f"[Battle] 作用角色索引错误，role_id: {role_id}")
            return False
        if x != 0 and y != 9:
            enemy_pos = [x, y]
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info('[battle]cast_sp 超时')
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_round(screenshot):
                logger.info("[Battle] 选择角色")
                self.device_manager.click(role_pos[0], role_pos[1])
                time.sleep(self.wait_time + self.wait_ui_time)
                continue
            if not self.in_battle(screenshot):
                return False
            if self.in_skill_on(screenshot):
                if switch and not self.switch_back_role(screenshot):
                    return False
                if enemy_pos is not None:
                    self.device_manager.click(*enemy_pos)
                    logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
                    time.sleep(self.wait_time)
                if not self.in_sp_on(screenshot):
                    logger.info("[Battle] 技能界面中,切换额外技能界面")
                    self.device_manager.click(696, 96)
                    time.sleep(self.wait_time + self.wait_ui_time)
                    screenshot = self.device_manager.get_screenshot()
                    if self.in_sp_on(screenshot):
                        # 点击修正坐标1与修正坐标2,兼容必杀技\支炎兽\ex技能时点击必杀选项,切换到必杀选项
                        normalize_pos = [(560, 210),(680, 210)]
                        for pos in normalize_pos:
                            self.device_manager.click(pos[0], pos[1])
                        time.sleep(self.wait_time + self.wait_ui_time)
                        screenshot = self.device_manager.get_screenshot()
                        # 点击发动按钮,兼容必杀技\支炎兽\ex技能时点击必杀发动选项
                        normalize_pos = [(941, 525),(942, 464)]
                        for pos in normalize_pos:
                            self.device_manager.click(pos[0], pos[1])
                        logger.info(f"[Battle] 点击发动按钮")
                        time.sleep(self.wait_time + self.wait_ui_time)
                        screenshot = self.device_manager.get_screenshot()
                        if role_id != 0:
                            role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
                            time.sleep(0.5)
                            self.device_manager.click(*role_pos)
                            logger.info(f"[Battle] 点击配置角色{role_id} {role_pos}")
                            time.sleep(self.wait_time + self.wait_ui_time)
                        return True

    def cast_skill(self, index: int = 1,skill: int = 1, bp: int = 0, role_id: int = 0,  x: int = 0, y: int = 0,
                    switch: bool = False, timeout:int = 10) -> bool:
        """
        使用技能
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        logger.debug(f"[Battle] 选择角色，角色索引: {index},技能索引: {skill},倍率: {bp},坐标: ({x}, {y})")
        # 检查index 1-4
        # 检查skill 0-4
        # 检查bp 0-3
        if index < 1 or index > 4:
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
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info('[battle]cast_skill 超时')
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_round(screenshot):
                logger.info("[Battle] 选择角色")
                self.device_manager.click(role_pos[0], role_pos[1])
                time.sleep(self.wait_time + self.wait_ui_time)
                continue
            if not self.in_battle(screenshot):
                return False
            if self.in_skill_on(screenshot):
                logger.info("[Battle] 在技能面板")
                if switch and not self.switch_back_role(screenshot):
                       return False
                if enemy_pos:
                    logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
                    self.device_manager.click(enemy_pos[0], enemy_pos[1])
                    time.sleep(self.wait_time + self.wait_ui_time)
                if bp == 0:
                    logger.info(f"[Battle] 点击选择技能")
                    self.device_manager.click(skill_start[0], skill_start[1])
                else:
                    logger.info(f"[Battle] 拖动选择技能")
                    self.device_manager.press_and_drag_step(skill_start, skill_end, self.wait_drag_time)
                if role_id != 0:
                    logger.info(f"[Battle] 点击配置角色{role_id}")
                    skill_role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
                    self.device_manager.click(skill_role_pos[0], skill_role_pos[1])
                time.sleep(self.wait_time + self.wait_ui_time)
                return True

    def attack(self, timeout:float = 5):
        """
        执行攻击
        """
        is_done = False
        # 设置超时时间为5秒
        start_time = time.time()
        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                logger.info("[Battle] attack超时")
                return False
            screenshot = self.device_manager.get_screenshot()
            if not is_done and self.in_round(screenshot):
                self.device_manager.click(1100, 650)
                is_done = True
                time.sleep(self.wait_time)
            if is_done and not self.in_round(screenshot):
                return True
            time.sleep(self.wait_time)
    
    def wait_in_round_or_world(self, callback:Callable[[Image.Image], str|None]|None = None, timeout:float = 10) -> str:
        """
        等待回合开始或进入世界
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return 'wait_done_timeout'
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None:
                logger.error("[wait_in_round_or_world] 无法获取截图")
                return 'exception'
            if self.in_round(screenshot):
                return 'in_round'
            if callback:
                result = callback(screenshot)
                if result is not None:
                    return result
            time.sleep(self.wait_time)
            

    def wait_done(self, callback:Callable[[Image.Image], str|None]|None = None, timeout:float = 90) -> str:
        """
        等待战斗结束
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info("[wait_done] wait_done超时")
                return 'wait_done_timeout'
            screenshot = self.device_manager.get_screenshot()
            logger.debug(f"[wait_done] 等待战斗结束")
            if screenshot is None:
                logger.error("[wait_done] 无法获取截图")
                return 'exception'
            if self.in_round(screenshot):
                logger.info("[in_round] in_round")
                return 'in_round'
            if not self.in_battle(screenshot):
                return 'not_in_battle'
            if callback:
                result = callback(screenshot)
                if result is not None:
                    return result
            time.sleep(self.wait_time)
            
    # ================== 战斗指令执行相关方法 ==================
    def cmd_role(self, index: int = 1,skill: int = 1, bp: int = 0, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = False) -> bool:
        """
        普通攻击
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param role_id 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        logger.debug(f"[Battle] 普通攻击，角色索引: {index},技能索引: {skill},倍率: {bp},技能目标角色索引: {role_id},坐标: ({x}, {y})")
        return self.cast_skill(index, skill, bp, role_id, x, y, switch)
            
    def cmd_xrole(self, index: int = 1, skill: int = 1, bp: int = 1, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = True) -> bool:
        """
        切换并攻击
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param role_id 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        logger.debug(f"[Battle] 切换并攻击，角色索引: {index},技能索引: {skill},倍率: {bp},技能目标角色索引: {role_id},坐标: ({x}, {y})")
        return self.cmd_role(index, skill, bp, role_id, x, y, switch)  

    def cmd_pet(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        使用宠物
        :param index: 宠物索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 使用宠物，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cast_pet(index, bp, role_id, x, y)

    def cmd_xpet(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        切换并使用宠物
        :param index: 宠物索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 切换并使用宠物，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cmd_pet(index, bp, role_id, x, y)
    
    def cmd_transform(self, index: int = 1) -> bool:
        """
        切换形态
        :param index: 角色索引
        """
        logger.debug(f"[Battle] 切换形态，角色索引: {index}")
        return self.transform(index)
    
    def cmd_xtransform(self, index: int = 1) -> bool:
        """
        切换形态
        :param index: 角色索引
        """
        logger.debug(f"[Battle] 切换形态，角色索引: {index}")
        return self.transform(index, switch=True)
    
    def cmd_ex(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        使用ex技能
        :param index: ex技能索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 使用ex技能，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cast_ex(index, bp, role_id, x, y)
    
    def cmd_xex(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        使用ex技能
        :param index: ex技能索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 使用ex技能，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cast_ex(index, bp, role_id, x, y, switch=True)
        
    def cmd_boost(self, timeout:float = 15) -> bool:
        """
        全体加成
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info("[Battle] 全体加成超时")
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_boost_on(screenshot):
                logger.debug("[Battle] 全体加成on")
                return True
            if self.in_boost_off(screenshot):
                logger.debug("[Battle] 全体加成off")
                self.device_manager.click(893, 654)
            if not self.in_battle():
                logger.debug("[Battle] 不在战斗中")
                return False
            time.sleep(self.wait_time)

    def cmd_attack(self) -> bool:
        """
        执行攻击
        """
        logger.debug("[Battle] 执行攻击（Attack）")
        return self.attack()

    def cmd_switch_all(self, timeout:float = 5) -> bool:
        """
        全员交替
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info("[Battle] cmd_switch_all超时")
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_switch_on(screenshot):
                logger.debug("[Battle] 全员交替on")
                return True
            if self.in_switch_off(screenshot):
                logger.debug("[Battle] 全员交替off")
                self.device_manager.click(792, 659)
            if not self.in_battle():
                logger.debug("[Battle] 不在战斗中")
                return False
            time.sleep(self.wait_time)

    def cmd_sp_skill(self, index: int = 1, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        特殊技能（SP）
        :param index: 技能索引
        """
        logger.debug(f"[Battle] 释放前排特殊技能（SP），技能索引: 角色:{index} 技能对象:{role_id} 敌人坐标:{x,y}")
        return self.cast_sp(index, role_id, x, y)
    
    def cmd_xsp_skill(self, index: int = 1, role_id:int = 0, x:int = 0, y:int = 0) -> bool:
        """
        特殊技能（XSP）
        :param index: 技能索引
        """
        logger.debug(f"[Battle] 释放后排特殊技能（SP），技能索引: 角色:{index} 技能对象:{role_id} 敌人坐标:{x,y}")
        return self.cast_sp(index, role_id, x, y)

    def cmd_wait(self, seconds: float = 1.0) -> bool:
        """
        等待指定时间
        :param seconds: 等待秒数
        """
        logger.debug(f"[Battle] 等待 {seconds} 秒")
        time.sleep(seconds)
        return True

    def cmd_skip(self, seconds: float = 1.0) -> bool:
        """
        跳过指定时间（可用于跳过动画等）
        :param seconds: 跳过秒数
        """
        logger.debug(f"[Battle] 跳过 {seconds} 秒（Skip）")
        self.device_manager.long_click(1000, 300, seconds)
        return True

    def cmd_click(self, x: int, y: int) -> bool:
        """
        点击指定坐标
        :param x: X 坐标
        :param y: Y 坐标
        """
        logger.debug(f"[Battle] 点击坐标 ({x}, {y})")
        self.device_manager.click(x, y)
        return True

    def cmd_battle_start(self) -> bool:
        """
        战斗开始
        """
        logger.debug("[Battle] 战斗开始（BattleStart）")
        return True

    def cmd_battle_end(self) -> bool:
        """
        战斗结束
        """
        logger.debug("[Battle] 战斗结束（BattleEnd）")
        return True

    def cmd_check_dead(self, role_id: int = 0) -> bool:
        """
        检查是否有角色死亡
        :param role_id: 角色id，0为任意角色
        """
        logger.debug(f"[Battle] 检查角色是否死亡，role_id={role_id}")
        return self.check_dead(role_id)

    def cmd_run(self) -> bool:
        """
        逃跑
        """
        logger.debug("[Battle] 逃跑（Run）")
        return self.exit_battle()
    # 识别敌人
    def find_enemy(self, monsters:list[Monster], timeout:float=5.0 ) -> Monster | None:
        """
        识别敌人
        """
        start_time = time.time()
        timeout = self.battle_recognition_time
        logger.info(f"[Battle] 开始识别敌人,timeout={timeout}")
        while True:
            if time.time() - start_time > timeout:
                logger.info(f"超时{timeout}秒,没有识别到敌人")
                return None
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None:
                return None
            if monsters is None or len(monsters) == 0:
                logger.info("没有配置要识别的敌人")
                return None
            for monster in monsters:
                if monster.points is None:
                    logger.info(f"敌人{monster.name}没有配置点")
                    continue
                if self.ocr_handler.match_point_color(screenshot, monster.points,ambiguity=0.9):
                    logger.info(f"识别到敌人: {monster.name}")
                    return monster
            time.sleep(0.1)