import time
from common.config import CheckPoint, Monster
from core.battle_command_executor import BattleCommandExecutor
from utils import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from PIL import Image
from utils.singleton import singleton
from utils.sleep_utils import sleep_until, sleep_until_app_running

if TYPE_CHECKING:
    from core.battle import Battle

@singleton
class World:
    """
    世界地图玩法模块
    负责实现世界地图相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler, battle: 'Battle', app_manager: AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        :param battle: Battle 实例
        :param app_manager: AppManager 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.battle = battle
        self.battle_executor = BattleCommandExecutor(battle, self)
        self.monsters = []
        self.monster_pos = []
        self.default_battle_config = ""
    
    def set_monsters(self,monster_pos:list[tuple[int, int]],monsters:list[Monster],default_battle_config:str=""):
        self.monster_pos= monster_pos
        self.monsters = monsters
        self.default_battle_config = default_battle_config

    def restart_wait_in_world(self,show_log:bool=False):
        self.app_manager.close_app()
        if show_log:
            logger.info(f"[read_map_state]读取界面状态")
        max_count = 2
        count = 0
        while count < max_count:
            time.sleep(1)
            in_world = self.in_world()
            if in_world:
                count += 1
            else:
                count = 0
            if not in_world:
                self.app_manager.start_app()
                self.device_manager.click(100,100)
                if show_log:
                    logger.info('点击开始.等待进入游戏界面')
            

    def restart_wait_in_fengmo_world(self,show_log:bool=False):
        def start_app_clk():
            self.app_manager.start_app()
            self.device_manager.click(100,100)
            if show_log:
                logger.info('点击开始.等待进入游戏界面')
        return self.read_fengmo_map_state(start_app_clk,show_log)
    
          
    def read_fengmo_map_state(self, callback:Callable[[], None]|None=None,show_log:bool=False):
        if show_log:
            logger.info(f"[read_map_state]读取界面状态")
        max_count = 3
        count = 0
        while count < max_count:
            time.sleep(1)
            if self.in_world():
                count += 1
            else:
                count = 0
            if callback is not None:
                callback()
        if self.in_fengmo_map():
            if show_log:
                logger.info(f"[read_map_state]在逢魔地图中")
            time.sleep(2)
            self.open_minimap()
            sleep_until(self.in_minimap)
            if self.find_map_boss() is not None:
                logger.info(f"[read_map_state]识别到三阶段")
                self.closeUI()
                return 'boss'
            if self.find_map_treasure() is not None or self.find_map_cure() is not None or self.find_map_monster() is not None:
                logger.info(f"[read_map_state]识别到二阶段")
                self.closeUI()
                return 'box'
            logger.info(f"[read_map_state]识别到一阶段")
            self.closeUI()
            return 'collect'
        logger.info(f"[read_map_state]在城镇中")
        self.closeUI()
        return 'in_world'
        
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
        
    def in_map(self, image: Optional[Image.Image] = None) -> bool:
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否在地图中")
            return False
        points_colors = [
            (1228, 648, 'C3BCB2', 1),
            (1189, 647, 'C6C2B9', 1),
            (1221, 660, '030000', 1),
            (1205, 659, '070400', 1),
        ]
        results = self.ocr_handler.match_point_color(image, points_colors)
        if results:
            logger.debug("检测到在大地图中")
            return True
        else:
            logger.debug("不在大地图中")
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
        
    def wait_in_fengmo_map(self, timeout:float= 4):
        start_time = time.time()
        count = 0
        max_count = 3
        while count < max_count:
            if time.time() - start_time > timeout:
                return False
            if self.in_world():
                count += 1
            else:
                count = 0
            time.sleep(0.1)
        if self.in_fengmo_map() is not None:
            return True
        return False
    
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
            self.device_manager.click(1270,710)
            time.sleep(interval)

    def dclick_tirm(self,count: int = 1,interval: float = 0.1) -> None:
        """
        点击跳过按钮，count次
        """
        for _ in range(count):
            self.device_manager.double_click(1270,710)
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
        sleep_until(lambda: self.ocr_handler.match_click_text(["是"]), function_name="旅馆 是")
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
    
    def exit_fengmo(self,entrance_pos:list[int],wait_time:float=0.2,callback:Callable[[], str|None]|None = None):
        """
        退出逢魔
        """
        logger.info(f"[exit_fengmo]检查是否在城镇")
        in_world = sleep_until(self.in_world)
        if not in_world:
            logger.debug("不在城镇中")
            return False
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
            return False
        logger.info(f"[go_fengmo]点击小地图: {entrance_pos}")
        self.device_manager.click(*entrance_pos)
        self.in_world_or_battle()
        time.sleep(wait_time)
        # 寻找逢魔入口
        fengmo_pos = sleep_until(self.find_fengmo_point,function_name=f"exit_fengmo 寻找逢魔入口 {entrance_pos}")
        if fengmo_pos is None:
            return False
        logger.info(f"[go_fengmo]点击逢魔入口: {fengmo_pos}")
        self.device_manager.click(*fengmo_pos[:2])
        sleep_until(callback,function_name=f"exit_fengmo 回调 {entrance_pos}")
        self.in_world_or_battle()
        return True

    def go_fengmo(self,depth:int,entrance_pos:list[int],wait_time:float=0.2,callback:Callable[[], str|None]|None = None) -> bool:
        """
        前往逢魔
        """
        logger.info(f"[go_fengmo]前往逢魔入口: {entrance_pos}")
        logger.debug(f"[go_fengmo]检查是否在城镇")
        in_world = sleep_until(self.in_world)
        if not in_world:
            logger.debug("不在城镇中")
            return False
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
            return False
        logger.info(f"[go_fengmo]点击小地图: {entrance_pos}")
        self.device_manager.click(*entrance_pos)
        self.in_world_or_battle()
        time.sleep(wait_time)
        # 寻找逢魔入口
        fengmo_pos = sleep_until(self.find_fengmo_point,function_name=f"go_fengmo 寻找逢魔入口 {entrance_pos}")
        if fengmo_pos is None:
            return False
        logger.info(f"[go_fengmo]点击逢魔入口: {fengmo_pos}")
        self.device_manager.click(*fengmo_pos[:2])
        logger.info(f"[go_fengmo]选择逢魔模式: {depth}")
        result = self.select_fengmo_mode(depth,callback=callback)
        if result != 'success':
            return False
        # 涉入
        logger.info(f"[go_fengmo]涉入")
        sleep_until(lambda: self.ocr_handler.match_click_text(["涉入"],region=(760,465,835,499)),function_name="涉入")
        time.sleep(5)
        return True

    def vip_cure(self,vip_cure:bool=False):
        """
        使用vip治疗
        """
        if not vip_cure:
            return None
        logger.debug("使用vip治疗")
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

    def select_fengmo_mode(self,depth:int,callback:Callable[[], str|None]|None = None):
        """
        选择逢魔模式
        """
        logger.info(f"[select_fengmo_mode]等待选择深度")
        sleep_until(lambda: self.ocr_handler.match_texts(["选择深度"]),function_name="选择深度",timeout=5)
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
                if callback is not None:
                   result = callback()
                   if result is not None:
                       return result
                continue
            if current_depth < depth:
                logger.info(f"[select_fengmo_mode]当前深度: {current_depth} 目标深度: {depth} 增加深度")
                self.do_fengmo_depth("add")
            else:
                logger.info(f"[select_fengmo_mode]当前深度: {current_depth} 目标深度: {depth} 减少深度")
                self.do_fengmo_depth("sub")
        return 'success'
    
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
        
    def check_in_world_or_battle(self,image:Image.Image|None=None, callback:Callable[[Image.Image], None]|None=None):
            while True:
                if image is None:
                    image = self.device_manager.get_screenshot()
                if not self.app_manager.is_app_running():
                    return "app_not_running"
                if self.in_world(image):
                    logger.debug("[in_world_or_battle]小镇中")
                    return "in_world"
                elif self.battle.in_battle(image):
                    logger.debug("[in_world_or_battle]战斗中")
                    if self.battle.check_battle_fail(image):
                        return "battle_fail"
                    return "in_battle"
                else:
                    if callback is not None and image is not None:
                        callback(image)
                    time.sleep(0.1)
                    image = self.device_manager.get_screenshot()

        
    def in_world_or_battle(self, callback:Callable[[Image.Image], None]|None=None)-> dict[str,bool|str]|None:
        logger.debug("[in_world_or_battle]开始检查")
        
        check_battle_command_done = False
        is_battle_success = True
        has_battle = False
        while True:
            check_in_world = sleep_until_app_running(lambda: self.check_in_world_or_battle(callback=callback),
                                                     app_manager=self.app_manager, function_name="in_world_or_battle")
            if check_in_world == 'battle_fail':
                is_battle_success = False
                continue
            if check_in_world == 'app_not_running':
                return { "in_world":False, "in_battle":False,"app_alive":False, 'is_battle_success':False}
            if check_in_world == "in_world":
                logger.debug("在城镇中")
                result = { "in_world":True, "in_battle":has_battle,"app_alive":True, 'is_battle_success':is_battle_success }
                if has_battle:
                    time.sleep(0.5)
                    check_in_world = sleep_until_app_running(lambda: self.check_in_world_or_battle(callback=callback) ,app_manager=self.app_manager, function_name="in_world_or_battle")
                    if check_in_world == "in_world":
                        return result
                    else:
                        logger.debug(f"战斗场景后，识别错误到城镇中{check_in_world},重新检查")
                        return self.in_world_or_battle(callback=callback)
                else:
                    return result
            elif check_in_world == "in_battle":
                logger.debug("战斗场景中")
                has_battle = True
                if not check_battle_command_done and self.battle.in_round():
                    logger.info("执行战斗场景")
                    monster = self.battle.find_enemy_ocr(self.monster_pos, self.monsters)
                    if monster is None:
                        logger.info("没有识别到敌人,使用默认战斗配置")
                        is_battle_success = self.do_default_battle()['result']
                    if monster:
                        loadConfig = self.battle_executor.load_commands_from_txt(monster.battle_config)
                        if not loadConfig:
                            logger.info("没有找到匹配敌人的战斗配置")
                            is_battle_success = self.do_default_battle()['result']
                        else:
                            logger.info("使用匹配敌人的战斗配置")
                            is_battle_success = self.battle_executor.execute_all()['success']
                    check_battle_command_done = True
                if check_battle_command_done and self.battle.in_round():
                    self.battle.auto_battle()
            else:
                logger.info("异常")
                return None
            
    def do_default_battle(self) -> dict:
        """
        执行默认战斗
        """
        loadConfig = self.battle_executor.load_commands_from_txt(self.default_battle_config)
        if not loadConfig:
            logger.info("没有默认战斗配置,使用委托战斗")
            self.battle.auto_battle()
            return { "type": "auto_battle", "result": True}
        else:
            logger.info("使用默认战斗配置")
            result = self.battle_executor.execute_all()['success']
            return { "type": "battle_executor", "result": result}

    def open_minimap(self):
        """
        点击小地图
        """
        time.sleep(0.2)
        self.device_manager.click(1060,100)
        time.sleep(0.2)
    
    def closeUI(self):
        self.device_manager.click(1235, 25)
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
    
    def click_confirm(self, image:Image.Image|None=None, click:bool = True):
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/confirm.png")
        if find:
            logger.info("检测到按钮-是")
            if click:
                self.device_manager.click(find[0],find[1])
                time.sleep(0.2)
                logger.info("点击按钮-是")
            return True
        else:
            return False
        
    def get_map_name(self):
        sleep_until(self.in_world,timeout=5)
        time.sleep(0.5)
        self.open_minimap()
        sleep_until(self.in_minimap,timeout=5)
        count = 0
        max_count = 3
        while count < max_count:
            time.sleep(0.5)
            screenshot = self.device_manager.get_screenshot()
            result = self.ocr_handler.recognize_text(screenshot,(85, 13,385, 92))
            texts = []
            if result is None or len(result) == 0:
                logger.info("小地图位置识别失败")
                texts = []
                count += 1
            else:
                for line in result:
                    texts.append(line['text'])
                break
        self.closeUI()
        logger.info(f"当前地图在{texts}")
        return texts
    
    def openMap(self):
        logger.info("打开地图")
        self.device_manager.click(875, 613)
        time.sleep(2)

    def _search_map_text(self, map_name: str, screenshot: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        在当前截图中搜索指定地图名称并返回坐标
        
        :param map_name: 要搜索的地图名称
        :param screenshot: 可选的截图，如果不提供则自动获取
        :return: 地图坐标 (x, y) 或 None
        """
        if screenshot is None:
            screenshot = self.device_manager.get_screenshot()
            
        if screenshot is None:
            return None
            
        result = self.ocr_handler.recognize_text(screenshot)
        if result is not None and len(result) > 0:
            for line in result:
                if line['text'] == map_name:
                    x = int(sum([p[0] for p in line['box']]) / 4)
                    y = int(sum([p[1] for p in line['box']]) / 4)
                    return (x, y - 30)
        return None

    def _perform_map_swipe(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        """
        执行地图滑动操作
        
        :param start: 起始坐标 (x, y)
        :param end: 结束坐标 (x, y)
        """
        self.device_manager.press_down(start[0], start[1])
        time.sleep(0.1)
        self.device_manager.press_move(end[0], end[1])
        time.sleep(0.1)
        self.device_manager.press_up(end[0], end[1])
        time.sleep(0.5)

    def tpAnywhere(self, map_name: str) -> bool:
        """
        在地图上搜索指定地名并传送
        
        通过多个方向的滑动搜索来查找目标地图名称：
        1. 首先在当前视图搜索
        2. 向下滑动搜索
        3. 向右滑动搜索  
        4. 向上滑动搜索
        
        :param map_name: 目标地图名称
        :return: 找到的地图坐标 (x, y) 或 None
        """
        logger.info(f"开始搜索地图: {map_name}")
        
        # 检查是否在世界中
        in_world = sleep_until(self.in_world, timeout=5)
        if not in_world:
            logger.info("不在世界中，无法传送")
            return False
            
        time.sleep(1.5)
        self.openMap()
        self.nomalize_map()

        mapping = {
           "圣树之泉":{1: (469, 321)}
        }
        
        # 定义搜索策略：(起始坐标, 结束坐标, 描述)
        search_strategies = [
            (1, None, None, "初始位置"),  # 不滑动，直接搜索
            (2, (378, 75), (660, 700), "向下滑动"),
            (3, (660, 700), (1260, 700), "向右滑动"),
            (4, (660, 700), (660, 0), "向上滑动")
        ]
        
        for id, start, end, description in search_strategies:
            logger.debug(f"在{description}搜索地图: {map_name}")
            # 如果不是初始搜索，执行滑动操作
            if start is not None and end is not None:
                self._perform_map_swipe(start, end)
            if map_name in mapping.keys():
                map_id = list(mapping[map_name].keys())[0]
                if id != map_id + 1:
                    continue
                else:
                    map_pos = mapping[map_name][map_id]
                    break
            # 搜索地图文本
            map_pos = self._search_map_text(map_name)
            if map_pos is not None:
                logger.info(f"在{description}找到地图 {map_name}，坐标: {map_pos}")
                break
        if map_pos is None:
            logger.info(f"未找到地图: {map_name}")
            return False
        logger.info(f"找到地图: {map_name}，坐标: {map_pos}")
        # 点击地图
        logger.info(f"点击地图: {map_pos}")
        self.device_manager.click(map_pos[0],map_pos[1])
        time.sleep(1)
        # 前往
        logger.info(f"点击前往")
        self.device_manager.click(1153, 632)
        time.sleep(1)
        # 部分需要选择入口
        logger.info(f"点击入口")
        self.device_manager.click(631, 281)
        time.sleep(1)
        # 确认
        logger.info(f"点击确认")
        self.click_confirm_pos()
        logger.info(f"等待地图")
        result = sleep_until(self.in_world)
        if not result:
            logger.error("传送失败")
            return False
        return True

    def scale_map(self):
        logger.info("缩放地图")
        self.device_manager.click(1210, 649)
        time.sleep(1)

    def nomalize_map(self):
        logger.info("等待地图界面")
        in_map = sleep_until(self.in_map,timeout=5)
        if not in_map:
            logger.info("不在地图中，无法归一化")
            return
        self.scale_map()
        logger.info("归一化地图")
        start = 600,360
        end = 0,0
        for i in range(3):
            self.device_manager.press_down(start[0],start[1])
            self.device_manager.press_move(end[0],end[1])
            self.device_manager.press_up(end[0],end[1])
            time.sleep(0.5)

    def move_mini_map(self,x,y,save:bool=True):
        self.device_manager.click(1060,100)
        time.sleep(1)
        sleep_until(self.in_minimap,timeout=5)
        self.device_manager.click(x,y)
        time.sleep(1)
        sleep_until(self.in_world)
        if save:
            time.sleep(0.5)
            self.save_by_mini_map()
            time.sleep(0.5)

    def save_by_mini_map(self):
        self.device_manager.click(226, 607)
        time.sleep(1)
        while not self.in_world():
            time.sleep(0.5)
            self.closeUI()
            time.sleep(0.5)
    
    def check_mini_map_pos(self,x:int,y:int,color:str,range:int=1):
        self.device_manager.click(1060,100)
        time.sleep(1)
        sleep_until(self.in_minimap,timeout=5)
        screenshot = self.device_manager.get_screenshot()
        if screenshot is None:
            return False
        result = self.ocr_handler.match_point_color(screenshot,[(x,y,color,range)],0.9)
        return result