import time
from loguru import logger
from common.app import AppManager
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from typing import Optional, Tuple
from PIL import Image
from utils.singleton import singleton
import glob
from utils.sleep_utils import sleep_until

@singleton
class World:
    """
    世界地图玩法模块
    负责实现世界地图相关的自动化逻辑
    """
    def __init__(self, device_manager: DeviceManager, ocr_handler: OCRHandler,app_manager:AppManager) -> None:
        """
        :param device_manager: DeviceManager 实例
        :param ocr_handler: OCRHandler 实例
        """
        self.app_manager = app_manager
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler

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
            (73, 632, "E8EBF0", 1),
            (68, 575, "F6F5F6", 1),
        ]
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results):
            logger.info("检测到在世界中")
            return True
        else:
            logger.info("不在世界中")
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
        results = [self.ocr_handler.match_point_color(image, x, y, color, rng) for x, y, color, rng in points_colors]
        if all(results):
            logger.info("检测到在小地图中")
            return True
        else:
            logger.info("不在小地图中")
            return False
        
    def in_inn(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆中。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_bed.png")
        if find:
            logger.info("检测到在旅馆中")
            return find
        else:
            logger.info("不在旅馆中")
            return None
    
    def find_inn_door(self, image: Optional[Image.Image] = None) -> Optional[Tuple[int, int]] | None:
        """
        判断当前是否在旅馆门口。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/inn_door.png")
        if find:
            logger.info("检测到在旅馆门口")
            return find
        else:
            logger.info("不在旅馆门口")
            return None
    
    def find_fengmo_point(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]] | None:
        """
        判断当前是否有逢魔点(逢魔入口也是这个,判断感叹号)。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/fengmo_point.png", debug=True)
        forbidden_range = (936,36,1208,195)
        # 如果find在禁止范围内,则返回None
        if find:
            if forbidden_range[0] <= find[0] <= forbidden_range[2] and forbidden_range[1] <= find[1] <= forbidden_range[3]:
                logger.info("检测到逢魔点,但在禁止范围内")
                return None
            else:
                logger.info("检测到逢魔点")
                return find
        else:
            logger.info("没有逢魔点")
            return None
        
    def find_fengmo_point_treasure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的宝箱点。
        支持多模板批量匹配，只要任意模板有颜色匹配点即返回。
        :param image: 可选，外部传入截图
        :return: 匹配的点坐标列表，若无则返回None
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        if image is None:
            logger.warning("无法获取截图，无法判断是否已发现的宝箱点")
            return None

        # 自动发现所有相关模板文件
        template_files = sorted(glob.glob("assets/fengmo_point_treasure_*.png"))

        # 只做一次RGB转换和像素访问对象
        rgb_img = image.convert('RGB')
        pixels = rgb_img.load()
        if pixels is None:
            logger.warning("像素访问对象为None，图片可能无效")
            return None
        width, height = rgb_img.size

        def color_sim(c1, c2):
            dist = sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
            return 1 - dist / (3 * 255)

        target_color = (220, 220, 220)
        tolerance = 10  # 匹配范围

        for template_path in template_files:
            candidates = self.ocr_handler.match_image_multi(image, template_path, threshold=0.75)
            if not candidates:
                continue
            points = [(x, y) for x, y, _ in candidates]
            matched_points:tuple[int,int]|None = None
            for x, y in points:
                found = False
                # 只在(x, y)为中心，tolerance为半径的正方形区域内查找
                for dx in range(-tolerance, tolerance + 1):
                    for dy in range(-tolerance, tolerance + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            pix = pixels[nx, ny]
                            if color_sim(pix, target_color) >= 0.95:
                                matched_points = (int(x), int(y))
                                found = True
                                break
                    if found:
                        break
            if matched_points and len(matched_points) > 0:
                # logger.info(f"模板 {template_path} 检测到已发现的宝箱点: {matched_points}")
                # for x, y in matched_points:
                #     filename = f"debug/treasure.png"
                #     rect = (x, y, x + 20, y + 20)
                #     self.ocr_handler.save_debug_rect(image, rect, filename, outline="red", width=2)
                #     break
                return matched_points

        logger.info("所有模板均未检测到已发现的宝箱点")
        return None
    
    def find_fengmo_point_cure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的治疗点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/fengmo_point_cure.png")
        if find:
            logger.info("检测到治疗点")
            return find
        else:
            logger.info("没有治疗点")
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

    def open_minimap(self):
        """
        打开小地图
        """
        self.device_manager.click(1060,100)

    def go_newdelsta_inn(self):
        """
        前往新德尔斯塔旅馆
        """
        self.device_manager.click(645,573)

    def click_tirm(self,count: int = 1,interval: float = 0.1) -> None:
        """
        点击跳过按钮，count次
        """
        for _ in range(count):
            logger.info("点击跳过按钮")
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
            logger.info("不在城镇中")
            return
        self.open_minimap()
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        self.device_manager.click(*inn_pos)
        in_inn = sleep_until(self.in_inn)
        if not in_inn:
            return
        logger.info("点击旅馆老板")
        self.device_manager.click(*in_inn)
        logger.info("等待欢迎光临")
        sleep_until(lambda: self.ocr_handler.match_click_text(["欢迎光临"]))
        logger.info("点击跳过")
        self.click_tirm(3)
        logger.info("点击是")
        sleep_until(lambda: self.ocr_handler.match_click_text(["是"]))
        logger.info("等待完全恢复")
        sleep_until(lambda: self.ocr_handler.match_click_text(["精力完全恢复了"]))
        logger.info("等待返回城镇")
        sleep_until(self.in_world)
        logger.info("打开小地图")
        self.open_minimap()
        logger.info("等待小地图")
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        logger.info("查找旅馆门口")
        door_pos = self.find_inn_door()
        if not door_pos:
            return
        logger.info("点击旅馆门口")
        self.device_manager.click(*door_pos)

    def go_fengmo(self,depth:int,entrance_pos:list[int]):
        """
        前往逢魔
        """
        in_world = sleep_until(self.in_world)
        if not in_world:
            logger.info("不在城镇中")
            return
        self.open_minimap()
        in_minimap = sleep_until(self.in_minimap)
        if not in_minimap:
            return
        # 点击地图逢魔入口
        self.device_manager.click(entrance_pos[0],entrance_pos[1])
        in_world = sleep_until(self.in_world)
        if not in_world:
            return
        # 寻找逢魔入口
        fengmo_pos = sleep_until(self.find_fengmo_point)
        if fengmo_pos is None:
            return
        self.device_manager.click(*fengmo_pos)
        self.select_fengmo_mode(depth)
        # 涉入
        sleep_until(lambda: self.ocr_handler.match_click_text(["涉入"],region=(760,465,835,499)))

    def select_fengmo_mode(self,depth:int):
        """
        选择逢魔模式
        """
        sleep_until(lambda: self.ocr_handler.match_texts(["选择深度"]))
        current_depth = self.read_fengmo_depth()
        while current_depth != depth:
            time.sleep(0.1)
            current_depth = self.read_fengmo_depth()
            if current_depth==depth:
                break
            if current_depth is None:
                continue
            if current_depth < depth:
                self.do_fengmo_depth("add")
            else:
                self.do_fengmo_depth("sub")
    
    def find_map_treasure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图宝箱点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_treasure.png")
        if find:
            logger.info("发现的地图宝箱点")
            return find
        else:
            logger.info("未发现地图宝箱点")
            return None
        
    def find_map_cure(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图治疗点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_cure.png")
        if find:
            logger.info("发现的地图治疗点")
            return find
        else:
            logger.info("未发现地图治疗点")
            return None
        
    def find_map_monster(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图怪物点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_monster.png")
        if find:
            logger.info("发现的地图怪物点")
            return find
        else:
            logger.info("未发现地图怪物点")
            return None
        
    def find_map_boss(self, image: Optional[Image.Image] = None) -> Optional[tuple[int, int]]:
        """
        判断当前是否已发现的地图Boss点。
        """
        if image is None:
            image = self.device_manager.get_screenshot()
        find = self.ocr_handler.match_image(image, "assets/map_boss.png")
        if find:
            logger.info("发现的地图Boss点")
            return find
        else:
            logger.info("未发现地图Boss点")
            return None