import time
from core.battle import Battle
from common.config import Monster
from core.battle_command_executor import BattleCommandExecutor
from utils import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Optional, Tuple
from PIL import Image
from utils.singleton import singleton
from utils.sleep_utils import sleep_until

@singleton
class World:
    """
    世界地图玩法模块
    负责实现世界地图相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler,battle:Battle, app_manager:AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.battle = battle
        self.battle_executor = BattleCommandExecutor(battle)
        self.monsters = []
        self.default_battle_config = ""
    
    def set_monsters(self,monsters:list[Monster],default_battle_config:str=""):
        self.monsters = monsters
        self.default_battle_config = default_battle_config

    def in_world(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在城镇主界面且人物停止移动。
        通过检测左下角菜单的多个点颜色判断。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有2点
        :return: bool，是否在世界中
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在世界中")
            return False
        points_colors = [
            (73, 632, "E8EBF0", 10),
            (68, 575, "F6F5F6", 10),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results:
            logger.debug("检测到在世界中")
            return True
        else:
            logger.debug("不在世界中")
            return False

    def in_minimap(self, image: Optional[Image.Image] = None) -> bool:
        """
        判断当前是否在小地图中。
        通过检测地图界面多个关键点的颜色判断。
        :param image: 可选，外部传入截图
        :param points_colors: 可选，[(x, y, color, range)] 数组，默认用原有3点
        :return: bool，是否在地图中
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在地图中")
            return False
        points_colors = [
            (33, 638, [255, 254, 255], 1),
            (64, 649, [255, 254, 255], 1),
            (452, 676, [251, 249, 254], 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results:
            logger.debug("检测到在小地图中")
            return True
        else:
            logger.debug("不在小地图中")
            return False
        
    def in_inn(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆中。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_bed.png")
        if find:
            logger.debug("检测到在旅馆中")
            return find
        else:
            logger.debug("不在旅馆中")
            return None
    
    def find_inn_door(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆门口。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_door.png")
        if find:
            logger.debug("检测到在旅馆门口")
            return find
        else:
            logger.debug("不在旅馆门口")
            return None
    
    def find_fengmo_point(self, image: Optional[Image.Image] = None, type: str = "right",offset=60) -> Optional[tuple[int, int, int]] | None:
        """
        判断当前是否有逢魔点(逢魔入口也是这个,判断感叹号)。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find_list = self.ocr_handler.match_image_multi(image, "assets/fengmo_point.png", threshold=0.9)
        find = None
        if find_list is not None and len(find_list) > 0:
            # 转换为int
            points = [(int(x), int(y)) for x, y, _ in find_list]
            # 根据type==left/right/up/down，获取find数组中x,y的
            # 获取x最大的点
            if type == "right": 
                find = max(points, key=lambda x: x[0])
            # 获取x最小的点
            elif type == "left":
                find = min(points, key=lambda x: x[0])
            # 获取y最大的点
            elif type == "down":
                find = max(points, key=lambda x: x[1])
            # 获取y最小的点
            elif type == "up":
                find = min(points, key=lambda x: x[1])
        forbidden_range = (936,36,1208,195)
        # 如果find在禁止范围内,则返回None
        if find:
            if forbidden_range[0] <= find[0] <= forbidden_range[2] and forbidden_range[1] <= find[1] <= forbidden_range[3]:
                logger.debug("检测到逢魔点,但在禁止范围内")
                return None
            else:
                logger.debug("检测到逢魔点")
                return (find[0],find[1]+offset,len(find_list))
        else:
            logger.debug("没有逢魔点")
            return None
        
    def find_fengmo_point_cure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的治疗点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/fengmo_point_cure.png")
        if find:
            logger.debug("检测到治疗点")
            return find
        else:
            logger.debug("没有治疗点")
            return None
    
    def read_fengmo_depth(self):
        text_list = self.ocr_handler.recognize_text(region=(615, 343, 663,380), rec_char_type='digit',scale=5)
        if len(text_list) == 0:
            return
        # 可以转为数字的直接返回
        for text in text_list:
            try:
                return int(text['text'])
            except:
                pass
        return None
    
    def do_fengmo_depth(self,op:str):
        if op == "add":
            self.device_manager.click(724,360)
        elif op == "sub":
            self.device_manager.click(555,360)
        else:
            raise ValueError(f"无效的操作: {op}")

    def click_tirm(self,count: int = 1,interval: float = 0.2) -> None:
        """
        点击跳过按钮，count次
        """
        for _ in range(count):
            logger.debug("点击跳过按钮")
            self.device_manager.click(1100,680)
            time.sleep(interval)
        
    def rest_in_inn(self,inn_pos:list[int]) -> None:
        """
        自动完成旅馆休息流程：
        1. 判断是否在城镇，打开小地图
        2. 进入旅馆
        3. 点击旅馆老板，等待欢迎光临
        4. 跳过对话，点击"是"
        5. 等待精力完全恢复
        6. 返回城镇，打开小地图
        7. 查找旅馆门口并点击
        :param app_manager: AppManager实例
        :param ocr_handler: OCRHandler实例
        """
        in_world = sleep_until(self.in_world)
        if not in_world:
            logger.debug("不在城镇中")
            return
        self.open_minimap()
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        self.device_manager.click(*inn_pos)
        in_inn = sleep_until(self.in_inn)
        if not in_inn:
            return
        logger.debug("点击旅馆老板")
        self.device_manager.click(*in_inn)
        logger.debug("等待欢迎光临")
        sleep_until(lambda: self.ocr_handler.match_click_text(["欢迎光临"]))
        logger.debug("点击跳过")
        self.click_tirm(3)
        logger.debug("点击是")
        sleep_until(lambda: self.ocr_handler.match_click_text(["是"]))
        logger.debug("等待完全恢复")
        sleep_until(lambda: self.ocr_handler.match_click_text(["精力完全恢复了"]))
        logger.debug("等待返回城镇")
        sleep_until(self.in_world)
        logger.debug("打开小地图")
        self.open_minimap()
        logger.debug("等待小地图")
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        logger.debug("查找旅馆门口")
        door_pos = self.find_inn_door()
        if not door_pos:
            return
        logger.debug("点击旅馆门口")
        self.device_manager.click(*door_pos)

    def go_fengmo(self,depth:int,entrance_pos:list[int],wait_time:float=0.2):
        """
        前往逢魔
        """
        logger.info(f"[go_fengmo]前往逢魔入口: {entrance_pos}")
        logger.info(f"[go_fengmo]检查是否在城镇")
        self.in_world_or_battle()
        logger.info(f"[go_fengmo]打开小地图")
        self.open_minimap()
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        logger.info(f"[go_fengmo]点击小地图: {entrance_pos}")
        self.device_manager.click(*entrance_pos)
        self.in_world_or_battle()
        time.sleep(wait_time)
        # 寻找逢魔入口
        fengmo_pos = sleep_until(self.find_fengmo_point)
        if fengmo_pos is None:
            return
        logger.info(f"[go_fengmo]点击逢魔入口: {fengmo_pos}")
        self.device_manager.click(*fengmo_pos[:2])
        logger.info(f"[go_fengmo]选择逢魔模式: {depth}")
        self.select_fengmo_mode(depth)
        # 涉入
        logger.info(f"[go_fengmo]涉入")
        sleep_until(lambda: self.ocr_handler.match_click_text(["涉入"],region=(760,465,835,499)))

    def select_fengmo_mode(self,depth:int):
        """
        选择逢魔模式
        """
        logger.info(f"[select_fengmo_mode]等待选择深度")
        sleep_until(lambda: self.ocr_handler.match_texts(["选择深度"]))
        logger.info(f"[select_fengmo_mode]读取当前深度")
        current_depth = self.read_fengmo_depth()
        while current_depth != depth:
            time.sleep(0.1)
            current_depth = self.read_fengmo_depth()
            if current_depth == depth:
                logger.info(f"[select_fengmo_mode]当前深度: {current_depth} 目标深度: {depth}")
                break
            if current_depth is None:
                logger.info(f"[select_fengmo_mode]读取深度失败")
                continue
            if current_depth < depth:
                logger.info(f"[select_fengmo_mode]当前深度: {current_depth} 目标深度: {depth} 增加深度")
                self.do_fengmo_depth("add")
            else:
                logger.info(f"[select_fengmo_mode]当前深度: {current_depth} 目标深度: {depth} 减少深度")
                self.do_fengmo_depth("sub")
    
    def find_map_treasure(self, image: Optional[Image.Image] = None) -> Optional[list[tuple[int, int]]]:
        """
        判断当前是否已发现的地图宝箱点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image_multi(image, "assets/map_treasure.png")
        if find:
            logger.debug("发现的地图宝箱点")
            return [(int(x), int(y)) for x, y, _ in find]
        else:
            logger.debug("未发现地图宝箱点")
            return None
        
    def find_map_cure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图治疗点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_cure.png")
        if find:
            logger.debug("发现的地图治疗点")
            return find
        else:
            logger.debug("未发现地图治疗点")
            return None
        
    def find_map_monster(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图怪物点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_monster.png")
        if find:
            logger.debug("发现的地图怪物点")
            return find
        else:
            logger.debug("未发现地图怪物点")
            return None
        
    def find_map_boss(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图Boss点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_boss.png")
        if find:
            logger.debug("发现的地图Boss点")
            return find
        else:
            logger.debug("未发现地图Boss点")
            return None
        
    def in_world_or_battle(self, enemyName:str='', check_battle:bool=True):
        def check_in_world_or_battle():
            screenshot = self.device_manager.get_screenshot()
            if self.in_world(screenshot):
                return "in_world"
            elif self.battle.in_battle(screenshot):
                return "in_battle"
            else:
                return None
        battle_done_done = False
        while True:
            check_in_world = sleep_until(check_in_world_or_battle)
            if check_in_world == "in_world":
                logger.info("在城镇中")
                return True
            elif check_in_world == "in_battle":
                logger.debug("战斗场景中")
                if not check_battle:
                    return False
                if battle_done_done:
                    continue
                if check_battle and not battle_done_done:
                    logger.info("执行战斗场景")
                    monster = self.find_enemy(self.monsters)
                    if monster is None:
                        logger.info("没有识别到敌人")
                        if enemyName:
                            logger.info(f"没有识别到敌人{enemyName},使用硬编码的映射敌人配置")
                            monster = next((x for x in self.monsters if x.name == enemyName), None)
                            if monster is None:
                                logger.info(f"没有找到硬编码的映射敌人配置{enemyName}")
                                self.do_default_battle()
                            else:
                                loadConfig = self.battle_executor.load_commands_from_file(monster.battle_config)
                                if not loadConfig:
                                    logger.info(f"没有找到硬编码映射敌人的战斗配置{enemyName}")
                                    self.do_default_battle()
                                else:
                                    logger.info("使用硬编码映射敌人的战斗配置")
                                    self.battle_executor.execute_all()
                        else:
                            logger.info("没有识别到敌人,使用默认战斗配置")
                            self.do_default_battle()
                    if monster:
                        loadConfig = self.battle_executor.load_commands_from_file(monster.battle_config)
                        if not loadConfig:
                            logger.info("没有找到匹配敌人的战斗配置")
                            self.do_default_battle()
                        else:
                            logger.info("使用匹配敌人的战斗配置")
                            self.battle_executor.execute_all()
                    battle_done_done = True
                continue
            else:
                logger.debug("异常")
                return False
            
    def do_default_battle(self):
        """
        执行默认战斗
        """
        loadConfig = self.battle_executor.load_commands_from_file(self.default_battle_config)
        if not loadConfig:
            logger.info("没有默认战斗配置,使用委托战斗")
            self.battle.auto_battle()
        else:
            logger.info("使用默认战斗配置")
            self.battle_executor.execute_all()

    def open_minimap(self):
        """
        点击小地图
        """
        time.sleep(0.2)
        self.device_manager.click(1060,100)
        time.sleep(0.2)

    def find_closest_point(self, target: tuple[int, int], points: list[tuple[int, int]]) -> Optional[tuple[int, int]]:
        """
        在points中查找与target最近的点
        :param target: 目标点 (x, y)
        :param points: 点坐标列表 [(x, y), ...]
        :return: 距离最近的点 (x, y) 或 None
        """
        if not points or target is None:
            return None
        cx, cy = target
        min_dist = float('inf')
        closest = None
        for pt in points:
            dist = ((pt[0] - cx) ** 2 + (pt[1] - cy) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = pt
        return closest
    # 识别敌人
    def find_enemy(self, monsters:list[Monster],max_count:int=3) -> Monster | None:
        """
        识别敌人
        """
        count = 0
        while True:
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
            count += 1
            if count >= max_count:
                return None

