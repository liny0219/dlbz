import time
import threading
from utils import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from PIL import Image
from utils.singleton import singleton
from common.config import Monster, config
from utils.sleep_utils import sleep_until

if TYPE_CHECKING:
    from common.world import World

@singleton
class Battle:
    """
    战斗模块
    负责实现战斗相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, app_manager: AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        :param app_manager: AppManager 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        # 移除对World的直接依赖，改为通过服务定位器获取
        self.world: Optional['World'] = None  # 延迟初始化
        self.extra_skill_bp_pos = (570, 305)
        self.extra_bp_offset_x = [0, 778, 895, 982]
        self.role_base_pos = (1100, 80)
        self.rols_base_y_offset = 140
        self.skill_base_x = [800,1020,1100,1200]
        self.skill_base_y = 200
        self.skill_base_y_offset = 105
        self.wait_time = config.battle.wait_time
        self.wait_ui_time = config.battle.wait_ui_time
        self.drag_press_time = config.battle.drag_press_time
        self.drag_wait_time = config.battle.drag_wait_time
        self.drag_release_time = config.battle.drag_release_time
        self.recognition_time = config.battle.recognition_time
        # 战斗相关timeout配置
        self.auto_battle_timeout = config.battle.auto_battle_timeout
        self.check_dead_timeout = config.battle.check_dead_timeout
        self.reset_round_timeout = config.battle.reset_round_timeout
        self.exit_battle_timeout = config.battle.exit_battle_timeout
        self.transform_timeout = config.battle.transform_timeout
        self.cast_sp_timeout = config.battle.cast_sp_timeout
        self.cast_skill_timeout = config.battle.cast_skill_timeout
        self.attack_timeout = config.battle.attack_timeout
        self.wait_in_round_timeout = config.battle.wait_in_round_timeout
        self.wait_done_timeout = config.battle.wait_done_timeout
        self.boost_timeout = config.battle.boost_timeout
        self.switch_all_timeout = config.battle.switch_all_timeout
        
        # 注册到服务定位器
        from utils.service_locator import register_service
        register_service("battle", self, type(self))
    
    def _get_world(self):
        """
        通过服务定位器获取World实例
        """
        from utils.service_locator import get_typed_service
        return get_typed_service("world")
    
    def set_world(self, world: 'World') -> None:
        """
        设置World依赖（依赖注入）- 保持向后兼容
        :param world: World实例
        """
        self.world = world

    # ================== 战斗状态判断相关方法 ==================

    def all_dead(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否全灭")
            return False
        points_colors_vip = [
            (622, 177, 'FEFAF9', 1),
            (621, 189, 'FFFEFD', 1),
            (622, 198, 'FFFEFF', 1),
            (612, 205, 'FEFEFE', 1),
            (630, 206, 'FBFFFF', 1)
        ]
        points_colors_no_vip = [
            (461, 484, '5C5C5C', 1),
            (818, 485, '37677D', 1),
            (669, 210, 'FEFEFE', 1),
            (670, 235, 'FFFFFF', 1),
            (612, 237, 'FFFFFF', 1),
            (612, 219, 'F3F3F3', 1),
        ]
        points_colors_failed = [
            (612, 210, 'FFFFFF', 1),
            (630, 210, 'FFFFFD', 1),
            (671, 231, 'FFFFFD', 1),
            (609, 219, 'FFFFFF', 1),
            (621, 490, '39697F', 1),
        ]
        # 批量判断
        results = self.ocr_handler.match_point_color(image, points_colors_vip)
        if not results:
            results = self.ocr_handler.match_point_color(image, points_colors_no_vip)
        if not results:
            results = self.ocr_handler.match_point_color(image, points_colors_failed)
        world = self.world or self._get_world()
        if results and world and world.click_confirm_yes(image, click=False):
            logger.debug("检测到在战斗回合中全灭")
            time.sleep(self.wait_time)
            return True
        else:
            logger.debug("不在战斗回合中全灭")
            return False
    
    def battle_end(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否战斗结算")
            return False
        results = self.ocr_handler.match_image(image, "assets/battle_end.png")
        if results:
            logger.info("在战斗结算")
            return True
        else:
            logger.debug("不在战斗结算")
            return False
    
    def in_battle(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在战斗中。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗中")
            return False
        region = (1028, 6, 1272, 587)
        find = self.ocr_handler.match_image_multi(image, "assets/hp_alive_front.png",region = region)
        if find and len(find) > 0:
            logger.debug("检测到在战斗中")
            return True
        find = self.ocr_handler.match_image_multi(image, "assets/hp_alive_back.png",region = region)
        if find and len(find) > 0:
            logger.debug("检测到在战斗中")
            return True
        return False
    
    def not_in_battle(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否不在战斗中。
        """
        return not self.in_battle(image)
    
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
            (1131,665, "FFFFFF", 1),
            (954, 652, '011017', 1),
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

    def not_in_round(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在战斗回合中")
            return False
        return not self.in_round(image)
    
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
            (443, 657, '4E4D4B', 1),
            (537, 655, '4F5450', 1),
            (489, 677, '0A0907', 1),
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
            (442, 652, 'DFDEDC', 1),
            (536, 652, 'DDDBE0', 1),
            (534, 665, '201F25', 1),
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
            (830, 658, 'E2D9DA', 1),
            (753, 657, 'DAD9D4', 1),
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
            (832, 658, '4F443E', 1),
            (753, 658, '4E4D4B', 1),
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
    def auto_battle(self, timeout: Optional[float] = None) -> bool:
        """
        自动战斗
        """
        if timeout is None:
            timeout = self.auto_battle_timeout
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

    def check_dead(self, role_id: int = 0, timeout: Optional[float] = None) -> bool:
        """
        判断当前是否死亡。
        :param image: 可选，外部传入截图
        :param role_id: 可选，角色id，默认0代表任意角色死亡判断,1-8代表具体角色死亡判断
        :return: bool
        """
        if timeout is None:
            timeout = self.check_dead_timeout
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

    def reset_round(self, timeout: Optional[float] = None) -> bool:
        """
        重置回合
        """
        if timeout is None:
            timeout = self.reset_round_timeout
        start_time = time.time()
        while not self.in_round() and self.in_battle():
            if time.time() - start_time > timeout:
                logger.info(f"[battle]reset_round 超时")
                return False
            self.device_manager.click(135,25)
            time.sleep(0.1)
        return True
            
    def exit_battle(self, timeout: Optional[float] = None) -> bool:
        """
        退出战斗
        """
        if timeout is None:
            timeout = self.exit_battle_timeout
        start_time = time.time()
        while not self.in_round():
            if time.time() - start_time > timeout:
                logger.info(f"[battle]exit_battle in_round 超时")
                return False
            self.device_manager.click(135,25)
            time.sleep(0.1)
        start_time = time.time()
        logger.info(f"[battle]exit_battle in_round")
        time.sleep(0.2)
        if self.in_battle():
            logger.info(f"[battle]exit_battle 点击放弃战斗")
            self.device_manager.click(592, 658)
            time.sleep(1)
        if self.in_battle():
            logger.info(f"[battle]exit_battle 选择放弃战斗")
            self.device_manager.click(800, 485)
            time.sleep(1)
        if self.in_battle():
            logger.info(f"[battle]exit_battle 确认放弃战斗")
            self.device_manager.click(800, 485)
            time.sleep(1)
            return True
        return False

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
                                  click_pos=[(945, 568),(945, 585)],
                                  switch=switch)
            
    def cast_pet(self, index:int, bp:int = 0, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = False) -> bool:
        """
        使用宠物
        """
        return self.cast_extra_skill(index, bp, role_id, x, y,
                                  normalize_pos=[(910, 210),(1080, 210)],
                                  click_pos=[(945, 533),(945, 585)],
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
        timeout = self.cast_skill_timeout
        if index < 1 or index > 4:
            logger.info(f"[Battle] 角色索引错误，index: {index}")
            return False
        if role_id < 0 or role_id > 4:
            logger.info(f"[Battle] 作用角色索引错误，role_id: {role_id}")
            return False
        if bp < 0 or bp > 3:
            logger.info(f"[Battle] 宠物bp错误，bp: {bp}")
            return False
        if x != 0 and y != 9:
            enemy_pos = [x, y]
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        if not sleep_until(self.in_round,timeout=timeout):
            logger.info("[Battle] 不在回合中超时")
            return False
        self.device_manager.click(role_pos[0], role_pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_skill_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
        if switch and not self.switch_back_role():
            logger.info("[Battle] 切换后排超时")
        if enemy_pos is not None:
            self.device_manager.click(*enemy_pos)
            logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
            time.sleep(self.wait_time)
        logger.info("[Battle] 技能界面中,切换额外技能界面")
        self.device_manager.click(696, 96)
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_sp_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
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
                drag_press_time=self.drag_press_time,
                drag_wait_time=self.drag_wait_time
            )
        # 点击发动按钮,兼容必杀技\支炎兽\ex技能时点击必杀发动选项
        for pos in click_pos:
            self.device_manager.click(pos[0], pos[1])
            time.sleep(self.wait_time + self.wait_ui_time)
            if self.in_round():
                break
        logger.info(f"[Battle] 点击发动按钮")
        time.sleep(self.wait_time + self.wait_ui_time)
        if role_id != 0:
            role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
            time.sleep(0.5)
            self.device_manager.click(*role_pos)
            logger.info(f"[Battle] 点击配置角色{role_id} {role_pos}")
            time.sleep(self.wait_time + self.wait_ui_time)
        return True     
                      

    def cast_skill_ex(self, index: int = 1, skill: int = 1, bp: int = 1, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = True) -> bool:
        """
        切换形态
        :param index: 角色索引
        :param switch: 是否切换角色
        """
        timeout = self.transform_timeout
        if index < 1 or index > 4:
            logger.error(f"[Battle] 角色索引错误，index: {index}")
            return False
        enemy_pos = None
        if x != 0 and y != 0:
            enemy_pos = (x,y)
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        skill_start = (self.skill_base_x[0], self.skill_base_y + (skill)*self.skill_base_y_offset)
        skill_end = (self.skill_base_x[bp], self.skill_base_y + (skill)*self.skill_base_y_offset)
        if not sleep_until(self.in_round,timeout=timeout):
            logger.info("[Battle] 不在回合中超时")
            return False
        self.device_manager.click(role_pos[0], role_pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_skill_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
        if switch and not self.switch_back_role():
            logger.info("[Battle] 切换后排超时")
            return False
        self.device_manager.click(960, 40)
        logger.info(f"[Battle] 点击潜力切换按钮")
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_skill_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
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
            self.device_manager.press_and_drag_step(skill_start, skill_end, self.drag_press_time, self.drag_wait_time)
        if role_id != 0:
            logger.info(f"[Battle] 点击配置角色{role_id}")
            skill_role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
            self.device_manager.click(skill_role_pos[0], skill_role_pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        return True

    def cast_sp(self, index:int, role_id:int = 0, x: int = 0, y: int = 0, 
                switch: bool = False) -> bool:
        timeout = self.cast_sp_timeout
        enemy_pos = None
        if index < 1 or index > 4:
            logger.info(f"[Battle] 角色索引错误，index: {index}")
            return False
        if role_id < 0 or role_id > 4:
            logger.info(f"[Battle] 作用角色索引错误，role_id: {role_id}")
            return False
        if x != 0 and y != 9:
            enemy_pos = [x, y]
        role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (index-1)*self.rols_base_y_offset)
        if not sleep_until(self.in_round,timeout=timeout):
            logger.info("[Battle] 不在回合中超时")
            return False
        self.device_manager.click(role_pos[0], role_pos[1])
        if not sleep_until(self.in_skill_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
        if switch and not self.switch_back_role(timeout=timeout):
            logger.info("[Battle] 切换后排超时")
            return False
        if enemy_pos is not None:
            self.device_manager.click(*enemy_pos)
            logger.info(f"[Battle] 点击敌人坐标: {enemy_pos}")
            time.sleep(self.wait_time)
        logger.info("[Battle] 技能界面中,切换额外技能界面")
        self.device_manager.click(696, 96)
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_sp_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
        # 点击修正坐标1与修正坐标2,兼容必杀技\支炎兽\ex技能时点击必杀选项,切换到必杀选项
        normalize_pos = [(560, 210),(680, 210)]
        for pos in normalize_pos:
            self.device_manager.click(pos[0], pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        # 点击发动按钮,兼容必杀技\支炎兽\ex技能时点击必杀发动选项
        normalize_pos = [(941, 525),(942, 464)]
        for pos in normalize_pos:
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

    def cast_skill(self, index: int = 1,skill: int = 1, bp: int = 0, role_id: int = 0,  x: int = 0, y: int = 0,
                    switch: bool = False, timeout: Optional[float] = None) -> bool:
        """
        使用技能
        :param index: 角色索引
        :param skill: 技能索引
        :param bp: 倍率
        :param x: 坐标x
        :param y: 坐标y
        :param switch: 是否切换角色
        """
        if timeout is None:
            timeout = self.cast_skill_timeout
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
        if not sleep_until(self.in_round,timeout=timeout):
            logger.info("[Battle] 不在回合中超时")
            return False
        logger.info("[Battle] 选择角色")
        self.device_manager.click(role_pos[0], role_pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        if not sleep_until(self.in_skill_on,timeout=timeout):
            logger.info("[Battle] 不在技能面板超时")
            return False
        logger.info("[Battle] 在技能面板")
        if switch and not self.switch_back_role():
            logger.info("[Battle 切换后排超时]")    
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
            self.device_manager.press_and_drag_step(skill_start, skill_end, self.drag_press_time, self.drag_wait_time)
        if role_id != 0:
            logger.info(f"[Battle] 点击配置角色{role_id}")
            skill_role_pos = (self.role_base_pos[0], self.role_base_pos[1] + (role_id-1)*self.rols_base_y_offset)
            self.device_manager.click(skill_role_pos[0], skill_role_pos[1])
        time.sleep(self.wait_time + self.wait_ui_time)
        return True
                

    def attack(self):
        """
        执行攻击
        """
        count = 0
        max_count = 3
        while count < max_count:
            if self.in_round():
                logger.info(f"[Battle] 在回合中")
                break
            else:
                logger.info(f"[Battle] 点击空白区域")
                self.device_manager.click(135,25)
                count += 1
            time.sleep(self.wait_time)
        logger.info(f"[Battle] 点击攻击按钮")
        self.device_manager.click(1100, 660)
        time.sleep(0.5)
        result = sleep_until(self.not_in_round,timeout=self.attack_timeout)
        if not result:
            logger.info(f"[Battle] 攻击等待超时")
            return False
        return result
    
    def wait_in_round_or_world(self, callback:Callable[[Image.Image], str|None]|None = None, timeout: Optional[float] = None) -> str:
        """
        等待回合开始或进入世界
        """
        if timeout is None:
            timeout = self.wait_in_round_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return 'wait_done_timeout'
            screenshot = self.device_manager.get_screenshot()
            if screenshot is None or not self.world:
                logger.error("[wait_in_round_or_world] 无法获取截图")
                return 'exception'
            if self.in_round(screenshot):
                return 'in_round'
            if self.world.in_world(screenshot):
                return 'in_world'
            if self.battle_end(screenshot):
                logger.info("[wait_in_round_or_world] 战斗结算")
                self.world.dclick_tirm(6)
            if callback:
                logger.debug("[wait_in_round_or_world] 执行回调")
                result = callback(screenshot)
                logger.debug(f"[wait_in_round_or_world] 执行回调结果: {result}")
                if result is not None:
                    return result
            time.sleep(self.wait_time)

    def wait_done(self, callback:Callable[[Image.Image], str|None]|None = None, timeout: Optional[float] = None) -> str:
        """
        等待战斗结束
        """
        if timeout is None:
            timeout = self.wait_done_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info("[wait_done] wait_done超时")
                return 'wait_done_timeout'
            screenshot = self.device_manager.get_screenshot()
            logger.debug(f"[wait_done] 等待战斗结束")
            if screenshot is None or not self.world:
                logger.error("[wait_done] 无法获取截图")
                return 'exception'
            if self.world.in_world(screenshot):
                logger.info("[wait_done] 进入世界")
                return 'in_world'
            if self.in_round(screenshot):
                logger.info("[wait_done] in_round")
                return 'in_round'
            if self.battle_end(screenshot):
                logger.info("[wait_done] 战斗结算")
                self.world.dclick_tirm(6)
            if callback:
                logger.debug("[wait_done] 执行回调")
                result = callback(screenshot)
                logger.debug(f"[wait_done] 执行回调结果: {result}")
                if result is not None:
                    return result
            time.sleep(self.wait_time)

    def check_battle_fail(self, image: Image.Image|None = None, type = 'tip'):
        if image is None:
           image = self.device_manager.get_screenshot()
        world = self.world or self._get_world()
        if not world:
            return False
        if not self.all_dead(image):
            return False
        logger.info(f"[check_battle_fail]检测到被全灭")
        start_time = time.time()
        while not world.in_world():
            if time.time() - start_time > 10:
                logger.info(f"[check_battle_fail]全灭返回世界超时")
                return False
            self.device_manager.click(480,480)
            logger.info(f"[check_battle_fail]点击放弃")
            time.sleep(0.5)
            self.device_manager.click(800,480)
            logger.info(f"[check_battle_fail]点击确认")
            time.sleep(0.5)
            if type == 'tip':
                logger.info(f"[check_battle_fail]tip confirm")
                world.click_confirm_yes()
        return True
    
    def press_in_round(self, timeout: float = 15) -> bool:
        try:
            if self.device_manager.device is None:
                logger.error("设备未连接")
                return False
            logger.info("等待战斗开始")
            logger.info(f"长按按下,等待跳过")
            self.device_manager.press_down(100,20)
            start_time = time.time()
            while not self.in_round():
                if time.time() - start_time > timeout:
                    logger.info("[press_in_round] 等待超时")
                    logger.info(f"长按抬起")
                    self.device_manager.press_up(100,20)
                    return False
                logger.info(f"等待跳过")
                time.sleep(1)
            logger.info(f"长按抬起")
            self.device_manager.press_up(100,20)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"[press_in_round] 失败: {e}")
            return False
        return True
    
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

    def cmd_pet(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0, switch: bool = False) -> bool:
        """
        使用宠物
        :param index: 宠物索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 使用宠物，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cast_pet(index, bp, role_id, x, y, switch)

    def cmd_xpet(self, index: int = 1, bp:int = 0, role_id:int = 0, x:int = 0, y:int = 0, switch: bool = True) -> bool:
        """
        切换并使用宠物
        :param index: 宠物索引
        :param role_id: 技能目标角色索引
        :param x: 坐标x
        :param y: 坐标y
        """
        logger.debug(f"[Battle] 切换并使用宠物，角色索引: {index},作用角色索引: {role_id},坐标: ({x}, {y})")
        return self.cmd_pet(index, bp, role_id, x, y, switch=True)
    
    def cmd_role_ex(self, index: int = 1, skill: int = 1, bp: int = 1, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = False) -> bool:
        """
        切换形态
        :param index: 角色索引
        """
        logger.debug(f"[Battle] 切换形态，角色索引: {index}")
        return self.cast_skill_ex(index, skill, bp, role_id, x, y, switch)
    
    def cmd_xrole_ex(self, index: int = 1, skill: int = 1, bp: int = 1, role_id:int = 0, x: int = 0, y: int = 0, switch: bool = True) -> bool:
        """
        切换形态
        :param index: 角色索引
        """
        logger.debug(f"[Battle] 切换形态，角色索引: {index}")
        return self.cast_skill_ex(index, skill, bp, role_id, x, y, switch)
    
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
        
    def cmd_boost(self, timeout: Optional[float] = None) -> bool:
        """
        全体加成
        """
        logger.info("[Battle] 全体加成")
        time.sleep(self.boost_timeout)
        self.device_manager.click(894, 655)
        time.sleep(self.boost_timeout)
        return True

    def cmd_attack(self) -> bool:
        """
        执行攻击
        """
        logger.debug("[Battle] 执行攻击（Attack）")
        return self.attack()

    def cmd_switch_all(self, timeout: Optional[float] = None) -> bool:
        """
        全员交替
        """
        if timeout is None:
            timeout = self.switch_all_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                logger.info("[Battle] cmd_switch_all超时")
                return False
            screenshot = self.device_manager.get_screenshot()
            if self.in_switch_on(screenshot):
                logger.info("[Battle] 全员交替on")
                return True
            if self.in_switch_off(screenshot):
                logger.info("[Battle] 全员交替off")
                self.device_manager.click(792, 659)
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
        return self.cast_sp(index, role_id, x, y, switch=True)

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
        logger.info(f"[Battle] 双击坐标 ({x}, {y})")
        self.device_manager.double_click(x, y)
        return True

    def cmd_press_in_round(self, timeout: float = 15) -> bool:
        return self.press_in_round(timeout)
    
    def cmd_auto_battle(self) -> bool:
        """
        自动战斗
        """
        logger.debug("[Battle] 自动战斗（AutoBattle）")
        return self.auto_battle()

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
    
    def cmd_exit_app(self) -> bool:
        """
        退出战斗
        """
        logger.debug("[Battle] 退出战斗（Exit）")
        self.app_manager.close_app()
        return True

    def find_enemy_ocr(self,monster_pos:list[tuple[int, int]],monsters:list[Monster]) -> Monster | None:
        """
        识别敌人
        """
        if monster_pos is None or len(monster_pos) == 0:
            logger.info("没有配置识别敌人位置")
            return None
        if monsters is None or len(monsters) == 0:
            logger.info("没有配置识别敌人")
            return
        logger.info(f"[find_enemy_ocr] 开始识别敌人")
        for pos in monster_pos:
            # 创建线程停止事件
            stop_event = threading.Event()
            def click_thread(device_manager, pos, stop_event):
                """
                持续点击指定位置的子线程
                :param device_manager: 设备管理器实例
                :param pos: 点击位置坐标元组 (x,y)
                :param stop_event: 线程停止事件
                """
                while not stop_event.is_set():
                    device_manager.click(pos[0], pos[1])
                    time.sleep(0.05)  # 短暂间隔避免点击过快
            # 启动点击线程        
            thread = threading.Thread(
                target=click_thread,
                args=(self.device_manager, pos, stop_event),
                daemon=True  # 设置为守护线程,主线程结束时自动结束
            )
            thread.start()
            # 使用识别时间进行循环识别
            start_time = time.time()
            logger.info(f"[find_enemy_ocr] 开始识别敌人,pos={pos},time={self.recognition_time}")
            self.device_manager.click(pos[0], pos[1])
            found_monster = None
            while time.time() - start_time < self.recognition_time:
                screenshot = self.device_manager.get_screenshot()
                logger.info(f"[find_enemy_ocr] 获取截图")
                result = self.ocr_handler.recognize_text(screenshot,(20,100,700,600))
                logger.info(f"[find_enemy_ocr] 识别结果")
                for r in result:
                    text = r["text"]
                    logger.info(f"[find_enemy_ocr]:{text}")
                    for monster in monsters:
                        if monster.name == text:
                            logger.info(f"匹配到敌人: {monster.name}")
                            found_monster = monster
                            break
                    if found_monster:
                        break
                if found_monster:
                    break
                time.sleep(0.1)  # 短暂等待后再次识别
            # 停止点击线程
            stop_event.set()
            thread.join(timeout=1.0)  # 等待线程结束，最多等待1秒
            if found_monster:
                return found_monster
        return None