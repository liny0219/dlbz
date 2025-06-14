import time
from core.battle import Battle
from common.config import CheckPoint, Monster
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
        self.battle_executor = BattleCommandExecutor(battle,self)
        self.monsters = []
        self.monster_pos = []
        self.default_battle_config = ""
    
    def set_monsters(self,monster_pos:list[tuple[int, int]],monsters:list[Monster],default_battle_config:str=""):
        self.monster_pos= monster_pos
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
            (73, 632, "E8EBF0", 2),
            (100, 637, '1F1E1C', 2),
            (73, 632, 'F5F1EE', 2),
            (86, 664, '8F8C85', 2),
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
            (33, 638, "FFFFFF", 1),
            (64, 649, "FFFFFF", 1),
            (452, 676, "FBF9FE", 1),
            (266, 86, '8B847A', 1),
            (226, 86, '847D73', 1),
            (1236, 21, 'F0F0F0', 1),
            (1187, 5, '6E6E6E', 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results:
            logger.debug("检测到在小地图中")
            return True
        else:
            logger.debug("不在小地图中")
            return False
        
    def in_fengmo_map(self, image: Optional[Image.Image] = None):
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_texts(["深度"],image,(960,205,1022,238))
        if find:
            logger.debug("检测到在逢魔地图中")
            return find
        else:
            logger.debug("不在逢魔地图中")
            return None
        
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
        
    def wait_in_fengmo_map(self, image: Optional[Image.Image] = None, timeout:float= 10):
        if image is None:
            image = self.device_manager.get_screenshot()
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.in_fengmo_map(image) and self.in_world(image):
                logger.info("在逢魔地图中")
                return True
            time.sleep(0.2)
            image = self.device_manager.get_screenshot()
        logger.info("不在逢魔地图中")
        return False
    
    def exit_fengmo_map(self,pops:list[int], image: Optional[Image.Image] = None, timeout:float= 10):
        if image is None:
            image = self.device_manager.get_screenshot()
        interval = 1
        start_time = time.time()
        in_fengmo_map = False
        while time.time() - start_time < timeout:
            if self.in_fengmo_map(image) and self.in_world(image):
                in_fengmo_map = True
                break
            time.sleep(interval)
            image = self.device_manager.get_screenshot()
        if not in_fengmo_map:
            return
        start_time = time.time()
        while time.time() - start_time < timeout:
            image = self.device_manager.get_screenshot()
            if self.in_world(image):
                time.sleep(interval)
                self.open_minimap()
                continue
            if not self.in_minimap(image):
                continue
            self.device_manager.click(*pops)
            time.sleep(1)
            sleep_until(self.in_fengmo_map)
            time.sleep(1)
            
            entrance_pop = self.find_fengmo_point(image)
            time.sleep(interval)
            if entrance_pop is not None:
                self.device_manager.click(entrance_pop[0],entrance_pop[1])
            start_time = time.time()
            while time.time() - start_time < timeout:
                image = self.device_manager.get_screenshot()
                time.sleep(interval)
                if self.ocr_handler.match_texts(["是否离开"],image):
                    self.click_confirm_pos()
                    continue
                if not self.in_fengmo_map(image) and self.in_world(image):
                    return True
    
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
    
    def find_fengmo_point(self, image: Optional[Image.Image] = None, type: str = "right",offset=60, current_point:CheckPoint|None=None) -> Optional[tuple[int, int, int]] | None:
        """
        判断当前是否有逢魔点(逢魔入口也是这个,判断感叹号)。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find_list = self.ocr_handler.match_image_multi(image, "assets/fengmo_point.png", threshold=0.9)
        # 过滤在禁止范围内的点
        forbidden_range = (936,36,1208,195)
        # 打印禁止范围和点的坐标，用于调试
        logger.debug(f"禁止范围: {forbidden_range}")
        # 过滤掉在禁止范围内的点，并在过滤时输出日志
        filtered_list = []
        for point in find_list:
            in_forbidden = (forbidden_range[0] <= int(point[0]) <= forbidden_range[2] and
                            forbidden_range[1] <= int(point[1]) <= forbidden_range[3])
            logger.info(f"发现点坐标: ({point[0]}, {point[1]})")
            logger.info(f"是否在禁止范围内: {in_forbidden}")
            if not in_forbidden:
                filtered_list.append(point)
        find_list = filtered_list
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
        if find:
            return (find[0],find[1]+offset,len(find_list))
        else:
            logger.info("没有找到逢魔点")
            if current_point and image:
                # 保存以current_point的id为key的截图到debug目录
                self.device_manager.save_screenshot(image,f"debug/fengmo_point_{current_point.id}.png")
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

    def click_tirm(self,count: int = 1,interval: float = 0.1) -> None:
        """
        点击跳过按钮，count次
        """
        for _ in range(count):
            self.device_manager.click(1100,680)
            time.sleep(interval)
        
    def rest_in_inn(self,inn_pos:list[int]) -> str:
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
            return 'not_in_world' 
        while True:
            time.sleep(0.2)
            logger.debug("打开小地图")
            self.open_minimap()
            logger.debug("等待小地图")
            in_minimap = self.in_minimap()
            if not in_minimap:
                continue
            else:
                logger.debug("在小地图中")
                break
        logger.debug("点击旅馆")
        self.device_manager.click(*inn_pos)
        logger.debug("等待旅馆")
        in_inn = sleep_until(self.in_inn)
        if not in_inn:
            logger.debug("不在旅馆中")
            return 'not_in_inn'
        logger.debug("点击旅馆老板")
        self.device_manager.click(*in_inn)
        time.sleep(1)
        logger.debug("点击跳过")
        self.click_tirm(3)
        logger.debug("点击是")
        sleep_until(lambda: self.ocr_handler.match_click_text(["是"]),function_name="旅馆 是")
        logger.debug("等待完全恢复")
        sleep_until(lambda: self.ocr_handler.match_click_text(["精力完全恢复了"]), function_name="旅馆 精力完全恢复了")
        logger.debug("等待返回城镇")
        sleep_until(self.in_world)
        logger.debug("打开小地图")
        self.open_minimap()
        logger.debug("等待小地图")
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return 'not_in_minimap'
        logger.debug("查找旅馆门口")
        door_pos = self.find_inn_door()
        if not door_pos:
            return 'not_find_inn_door'
        logger.debug("点击旅馆门口")
        self.device_manager.click(*door_pos)
        return 'rest_in_inn'

    def go_fengmo(self,depth:int,entrance_pos:list[int],wait_time:float=0.2):
        """
        前往逢魔
        """
        logger.info(f"[go_fengmo]前往逢魔入口: {entrance_pos}")
        logger.debug(f"[go_fengmo]检查是否在城镇")
        in_world = sleep_until(self.in_world)
        if not in_world:
            logger.debug("不在城镇中")
            return
        while True:
            time.sleep(0.2)
            logger.debug("打开小地图")
            self.open_minimap()
            logger.debug("等待小地图")
            in_minimap = self.in_minimap()
            if not in_minimap:
                continue
            else:
                logger.debug("在小地图中")
                break
        self.open_minimap()
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        logger.info(f"[go_fengmo]点击小地图: {entrance_pos}")
        self.device_manager.click(*entrance_pos)
        self.in_world_or_battle()
        time.sleep(wait_time)
        # 寻找逢魔入口
        fengmo_pos = sleep_until(self.find_fengmo_point,function_name=f"go_fengmo 寻找逢魔入口 {entrance_pos}")
        if fengmo_pos is None:
            return
        logger.info(f"[go_fengmo]点击逢魔入口: {fengmo_pos}")
        self.device_manager.click(*fengmo_pos[:2])
        logger.info(f"[go_fengmo]选择逢魔模式: {depth}")
        self.select_fengmo_mode(depth)
        # 涉入
        logger.info(f"[go_fengmo]涉入")
        sleep_until(lambda: self.ocr_handler.match_click_text(["涉入"],region=(760,465,835,499)),function_name="涉入")
        time.sleep(5)

    def vip_cure(self,vip_cure:bool=False):
        """
        使用vip治疗
        """
        if not vip_cure:
            return None
        logger.debug("使用vip治疗")
        self.device_manager.click(1238, 20)
        sleep_until(self.in_world)
        time.sleep(0.2)
        logger.info(f"[vip_cure]使用vip治疗")
        self.device_manager.click(1222, 525)
        def check_cure():
            screenshot = self.device_manager.get_screenshot()
            result = self.ocr_handler.recognize_text(screenshot)
            for r in result:
                if "将恢复旅团所有人的全部" in r['text']:
                    logger.info('是否月卡恢复')
                    time.sleep(1)
                    self.click_confirm_pos()
                    logger.info('点击确认')
                    return 'confirm_cure'
                if "已用完所有的全恢复次数" in r['text']:
                    logger.info('已用完所有月卡恢复次数')
                    self.click_confirm_pos()
                    return 'none_cure'
        result = sleep_until(check_cure,function_name="check_cure")
        if result == 'none_cure':
            return result
        time.sleep(5)
        sleep_until(lambda:self.ocr_handler.match_click_text(["完全恢复了"]),function_name="vip治疗 完全恢复了")
        time.sleep(1)
        return 'finish_cure'

    def select_fengmo_mode(self,depth:int):
        """
        选择逢魔模式
        """
        logger.info(f"[select_fengmo_mode]等待选择深度")
        sleep_until(lambda: self.ocr_handler.match_texts(["选择深度"]),function_name="选择深度")
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
        
    def in_world_or_battle(self, enemyName:str='', check_battle:bool=True)-> dict[str,bool]|None:
        logger.debug("[in_world_or_battle]开始检查")
        def check_in_world_or_battle():
            screenshot = self.device_manager.get_screenshot()
            if self.in_world(screenshot):
                logger.debug("[in_world_or_battle]小镇中")
                return "in_world"
            elif self.battle.in_battle(screenshot):
                logger.debug("[in_world_or_battle]战斗中")
                time.sleep(2)
                return "in_battle"
            else:
                logger.debug("[in_world_or_battle]没检查出来")  
                return None
        check_battle_command_done = False
        is_battle_success = True
        has_battle = False
        while True:
            check_in_world = sleep_until(check_in_world_or_battle)
            if check_in_world == "in_world":
                logger.debug("在城镇中")
                return { "in_world":True, "in_battle":has_battle, 'is_battle_state':is_battle_success }
            elif check_in_world == "in_battle":
                logger.debug("战斗场景中")
                if not check_battle:
                    continue
                has_battle = True
                if check_battle and not check_battle_command_done and self.battle.in_round():
                    logger.info("执行战斗场景")
                    monster = self.battle.find_enemy_ocr(self.monster_pos, self.monsters)
                    if monster is None:
                        logger.info("没有识别到敌人")
                        if enemyName:
                            logger.info(f"没有识别到敌人{enemyName},使用硬编码的映射敌人配置")
                            monster = next((x for x in self.monsters if x.name == enemyName), None)
                            if monster is None:
                                logger.info(f"没有找到硬编码的映射敌人配置{enemyName}")
                                is_battle_success = self.do_default_battle()['success']
                            else:
                                loadConfig = self.battle_executor.load_commands_from_txt(monster.battle_config)
                                if not loadConfig:
                                    logger.info(f"没有找到硬编码映射敌人的战斗配置{enemyName}")
                                    is_battle_success = self.do_default_battle()['success']
                                else:
                                    logger.info("使用硬编码映射敌人的战斗配置")
                                    is_battle_success = self.battle_executor.execute_all()
                        else:
                            logger.info("没有识别到敌人,使用默认战斗配置")
                            is_battle_success = self.do_default_battle()['success']
                    if monster:
                        loadConfig = self.battle_executor.load_commands_from_txt(monster.battle_config)
                        if not loadConfig:
                            logger.info("没有找到匹配敌人的战斗配置")
                            is_battle_success = self.do_default_battle()['success']
                        else:
                            logger.info("使用匹配敌人的战斗配置")
                            is_battle_success = self.battle_executor.execute_all()
                    check_battle_command_done = True
                if check_battle_command_done and self.battle.in_round():
                    self.battle.auto_battle()
            else:
                logger.debug("异常")
                return None
            
    def do_default_battle(self) -> dict:
        """
        执行默认战斗
        """
        loadConfig = self.battle_executor.load_commands_from_txt(self.default_battle_config)
        if not loadConfig:
            logger.info("没有默认战斗配置,使用委托战斗")
            self.battle.auto_battle()
            return { "type": "auto_battle", "success": True}
        else:
            logger.info("使用默认战斗配置")
            result = self.battle_executor.execute_all()
            return { "type": "battle_executor", "success": not result}

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

    def run_left(self):
        device = self.device_manager.device
        if device:
            device.swipe(640, 350, 590, 350, 0.05)

    def run_right(self):
        device = self.device_manager.device
        if device:
            device.swipe(640, 350, 690, 350, 0.05)

    def click_confirm_pos(self):
        self.device_manager.click(800,485)
    
    def click_confirm(self,image:Image.Image|None=None):
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/confirm.png")
        if find:
            logger.debug("检测到按钮-是")
            self.device_manager.click(find[0],find[1])
            time.sleep(0.2)
            logger.debug("点击按钮-是")
            return True
        else:
            return False
    