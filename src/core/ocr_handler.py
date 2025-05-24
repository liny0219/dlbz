import time
from paddleocr import PaddleOCR
from loguru import logger
import yaml
import cv2
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Any, Union, Optional, Tuple
import os
from core.device_manager import DeviceManager
from common.config import config
from utils.get_asset_path import get_asset_path

class OCRHandler:
    def __init__(self, device_manager: DeviceManager) -> None:
        # 初始化OCR
        self.ocr = PaddleOCR(
            use_angle_cls=config.ocr.use_angle_cls,
            lang=config.ocr.lang,
            show_log=False
        )
        self.threshold = config.ocr.threshold
        self.device_manager = device_manager
        logger.info("OCR handler initialized")

    def match_texts(
        self,
        keywords: List[str],
        image: Union[Image.Image, np.ndarray, str,None] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8
    ) -> bool:
        """
        检查截图OCR结果中是否全部匹配给定文案数组
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param keywords: 需要匹配的文案字符串数组
        :param threshold: 可信度阈值（可选，默认用配置）
        :param region: (x1, y1, x2, y2) 可选，指定识别区域坐标，默认全屏
        :return: bool，是否全部匹配
        """
        try:
            if image is None:
                image = self.device_manager.get_screenshot()
            # 裁剪区域
            if region is not None:
                if isinstance(image, Image.Image):
                    image = image.crop(region)
                elif isinstance(image, np.ndarray):
                    x1, y1, x2, y2 = region
                    image = image[y1:y2, x1:x2]
                else:
                    logger.warning("region参数仅支持PIL.Image或np.ndarray类型图片裁剪")
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            result = self.ocr.ocr(image, cls=True)
            if not result:
                logger.warning("OCR无结果")
                return False
            detected_texts = set()
            all_texts = []
            for line in result:
                for item in line:
                    text = item[1][0]
                    confidence = item[1][1]
                    all_texts.append((text, confidence))
                    if confidence >= threshold:
                        detected_texts.add(text)
            logger.info(f"OCR识别文本及置信度: {[f'{t}:{c:.2f}' for t,c in all_texts]}")
            for kw in keywords:
                if not any(kw in t for t in detected_texts):
                    logger.info(f"未检测到关键词: {kw}")
                    return False
            logger.info(f"全部关键词匹配: {keywords}")
            return True
        except Exception as e:
            logger.error(f"OCR匹配失败: {str(e)}")
            return False

    def match_click_text(
        self,
        keywords: List[str],
        image: Union[Image.Image, np.ndarray, str, None] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8
    ) -> bool:
        """
        检查截图OCR结果中是否全部匹配给定文案数组，若匹配则点击第一个匹配到的文本中心点。
        :param keywords: 需要匹配的文案字符串数组
        :param image: 可选，PIL.Image、OpenCV numpy.ndarray、图片路径，默认自动截图
        :param region: 可选，(x1, y1, x2, y2) 指定识别区域坐标，默认全屏
        :param threshold: 可信度阈值
        :return: bool，是否全部匹配并点击
        """
        try:
            # 自动截图
            if image is None:
                if not hasattr(self, "device_manager"):
                    logger.error("OCRHandler未绑定device_manager，无法截图")
                    return False
                image = self.device_manager.get_screenshot()
            if image is None:
                logger.warning("无法获取截图，无法进行文本匹配点击")
                return False

            # 区域裁剪
            offset_x, offset_y = 0, 0
            if region is not None:
                if isinstance(image, Image.Image):
                    image = image.crop(region)
                    offset_x, offset_y = region[0], region[1]
                elif isinstance(image, np.ndarray):
                    x1, y1, x2, y2 = region
                    image = image[y1:y2, x1:x2]
                    offset_x, offset_y = x1, y1
                else:
                    logger.warning("region参数仅支持PIL.Image或np.ndarray类型图片裁剪")
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            # OCR识别
            result = self.ocr.ocr(image, cls=True)
            if not result:
                logger.warning("OCR无结果")
                return False

            detected_texts = []
            for line in result:
                for item in line:
                    text = item[1][0]
                    confidence = item[1][1]
                    box = item[0]
                    if confidence >= threshold:
                        detected_texts.append((text, box, confidence))

            # 检查所有关键词是否都匹配
            for kw in keywords:
                if not any(kw in t for t, _, _ in detected_texts):
                    logger.info(f"未检测到关键词: {kw}")
                    return False

            # 点击第一个匹配到的文本中心
            first_kw = keywords[0]
            for text, box, confidence in detected_texts:
                if first_kw in text:
                    # box: 4点坐标，需加region偏移
                    x = int(sum([p[0] for p in box]) / 4) + offset_x
                    y = int(sum([p[1] for p in box]) / 4) + offset_y
                    if hasattr(self, "device_manager"):
                        self.device_manager.click(x, y)
                        logger.info(f"点击文本 '{text}' 的中心点 ({x},{y})，置信度{confidence:.2f} (已加region偏移)")
                        return True
                    else:
                        logger.warning("OCRHandler未绑定device_manager，无法点击")
                        return False
            logger.info("所有关键词匹配，但未找到可点击的文本区域")
            return False
        except Exception as e:
            logger.error(f"match_click_text 执行异常: {e}")
            return False

    def recognize_text(self, image:Union[Image.Image, np.ndarray, str, None] = None, region: Optional[Tuple[int, int, int, int]] = None):
        """
        识别图片中的文字，可指定识别区域。
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param region: (x1, y1, x2, y2) 可选，指定识别区域坐标，默认全图
        :return: 识别结果列表
        """
        try:
            if image is None:
                image = self.device_manager.get_screenshot()
            # 区域裁剪前，若指定region，保存画红框的调试图片
            if region is not None:
                # 只支持PIL.Image调试保存
                if isinstance(image, Image.Image):
                    os.makedirs("debug", exist_ok=True)
                    img_copy = image.copy()
                    draw = ImageDraw.Draw(img_copy)
                    draw.rectangle(region, outline="red", width=2)
                    filename = f"debug/ocr_region.png"
                    img_copy.save(filename)
                    logger.info(f"已保存OCR裁剪区域调试图: {filename}")
                # 裁剪
                if isinstance(image, Image.Image):
                    image = image.crop(region)
                elif isinstance(image, np.ndarray):
                    x1, y1, x2, y2 = region
                    image = image[y1:y2, x1:x2]
                else:
                    logger.warning("region参数仅支持PIL.Image或np.ndarray类型图片裁剪")
            # 如果是 PIL.Image，先转成 OpenCV 格式（BGR）
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            result = self.ocr.ocr(image, cls=True)
            
            if result is None or not result:
                logger.warning("OCR无结果")
                return []
            
            processed_results = []
            for line in result:
                for item in line:
                    confidence = item[1][1]
                    if confidence >= self.threshold:
                        logger.info(f"OCR识别文本: {item[1][0]}，置信度: {confidence:.2f}") 
                        processed_results.append({
                            'text': item[1][0],
                            'box': item[0],
                            'confidence': confidence
                        })
            return processed_results
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {str(e)}")
            return []

    def match_image(
        self,
        image: Union[Image.Image, np.ndarray, str, None],
        template_path: str,
        threshold: float = 0.95,
        region: Optional[Tuple[int, int, int, int]] = None,
        gray: bool = False,
        debug: bool = False,
    ) -> Optional[Tuple[int, int]]:
        """
        使用模板匹配，判断image中指定区域是否包含template_path指定的图片，返回匹配到的左上角坐标。
        检查模板文件名是否匹配规则xxx__x1_y1_x2_y2.png，若匹配则自动提取region坐标，否则region为None。
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param template_path: 模板图片路径
        :param threshold: 匹配阈值，默认0.8
        :param region: (x1, y1, x2, y2) 匹配区域，默认全图
        :param debug: 是否保存调试图片，保存到debug目录
        :return: (x, y) 匹配到的左上角坐标，未匹配返回None
        """
        try:
            # 1. 读取主图像，转为BGR格式
            if image is None:
                logger.error("Input image is None")
                return None
            if isinstance(image, str):
                image = cv2.imread(get_asset_path(image))
            elif isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            orig_image = image.copy()  # 保存原始图片

            # 2. 读取模板
            base, ext = os.path.splitext(template_path)
            if "__" in base:
                region_str = base.split("__")[-1]
                region_tuple = tuple(map(int, region_str.split("_")))
                if len(region_tuple) == 4:
                    region = region_tuple
                    logger.info(f"自动提取region坐标: {region}")
            # 读取模板始终用get_asset_path
            template = cv2.imread(get_asset_path(template_path))
            if template is None:
                logger.error(f"模板图片读取失败: {template_path}")
                return None
            th, tw = template.shape[:2]

            # 3. 匹配区域裁剪
            if region is not None:
                x1, y1, x2, y2 = region
                image_crop = image[y1:y2, x1:x2]
            else:
                x1, y1, x2, y2 = 0, 0, 0, 0
                image_crop = image

            # 4. 灰度化
            if gray:
                img_proc = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
                template_proc = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                img_proc = image_crop
                template_proc = template

            # 5. 模板匹配
            res = cv2.matchTemplate(img_proc, template_proc, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            # logger.info(f"模板匹配最大相关系数: {max_val:.3f}")

            # 6. debug保存图片，画出匹配区域
            if debug:
                os.makedirs("debug", exist_ok=True)
                debug_img = orig_image.copy()
                # 匹配区域左上角坐标
                match_x = max_loc[0] + (region[0] if region else 0)
                match_y = max_loc[1] + (region[1] if region else 0)
                # 画矩形框
                cv2.rectangle(debug_img, (match_x, match_y), (match_x + tw, match_y + th), (0, 0, 255), 2)
                cv2.imwrite("debug/match_image_result.png", debug_img)
                logger.info(f"匹配区域已保存到debug/match_image_result.png")

            # 7. 匹配结果坐标
            if max_val >= threshold:
                match_x = max_loc[0] + (region[0] if region else 0)
                match_y = max_loc[1] + (region[1] if region else 0)
                # logger.info(f"模板匹配成功，坐标: ({match_x}, {match_y})")
                return (match_x, match_y)
            else:
                logger.info("模板未匹配成功")
                return None
        except Exception as e:
            logger.error(f"模板匹配失败: {str(e)}")
            return None

    @staticmethod
    def save_with_region(image, save_path: str, region: Optional[Tuple[int, int, int, int]] = None,is_append:bool=True) -> str:
        """
        按region拼接保存路径，保存图片。
        :param image: 要保存的图片（numpy数组或PIL.Image）
        :param save_path: 原始保存路径，如'asset/world/inn.png'
        :param region: (x1, y1, x2, y2) 区域，若为None则不拼接
        :return: 实际保存的路径
        """
        import os
        import numpy as np
        import cv2
        from PIL import Image
        # 转换为OpenCV格式
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        if region is not None:
            x1, y1, x2, y2 = region
            base, ext = os.path.splitext(save_path)
            if is_append:
                save_path = f"{base}__{x1}_{y1}_{x2}_{y2}{ext}"
        cv2.imwrite(save_path, image)
        return save_path 

    def FindColor(
        self, 
        image: Image.Image, 
        x1: int, y1: int, x2: int, y2: int, 
        color: str, 
        sim: float, 
        dir: int
    ) -> Tuple[int, Optional[int], Optional[int]]:
        """
        在指定区域查找指定颜色，支持多色和偏色。
        :param image: PIL.Image，原始图片
        :param x1, y1, x2, y2: 区域左上和右下坐标
        :param color: 颜色字符串，格式"BBGGRR"，支持多色和偏色
        :param sim: 相似度，0~1
        :param dir: 查找方向，0~4
        :return: (序号, x, y)，没找到返回(-1, None, None)
        """
        def parse_colors(color_str):
            color_list = []
            for part in color_str.split('|'):
                if '-' in part:
                    base, bias = part.split('-')
                    color_list.append((base, bias))
                else:
                    color_list.append((part, None))
            return color_list

        def hex_to_bgr(hexstr):
            # "BBGGRR" -> (B, G, R)
            return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

        def bgr_to_hex(bgr):
            # (B, G, R) -> "BBGGRR"
            return '{:02X}{:02X}{:02X}'.format(bgr[0], bgr[1], bgr[2])

        color_defs = parse_colors(color)
        region = image.crop((x1, y1, x2, y2)).convert('RGB')
        width, height = region.size
        pixels = region.load()
        if pixels is None:
            return -1, None, None

        def gen_coords(w, h, dir):
            if dir == 0:  # 左上到右下
                for y in range(h):
                    for x in range(w):
                        yield x, y
            elif dir == 1:  # 中心向四周
                cx, cy = w // 2, h // 2
                for r in range(max(w, h)):
                    for dx in range(-r, r+1):
                        for dy in range(-r, r+1):
                            x, y = cx + dx, cy + dy
                            if 0 <= x < w and 0 <= y < h:
                                yield x, y
            elif dir == 2:  # 右下到左上
                for y in reversed(range(h)):
                    for x in reversed(range(w)):
                        yield x, y
            elif dir == 3:  # 左下到右上
                for y in reversed(range(h)):
                    for x in range(w):
                        yield x, y
            elif dir == 4:  # 右上到左下
                for y in range(h):
                    for x in reversed(range(w)):
                        yield x, y

        def color_sim(c1, c2, bias=None):
            # c1, c2: (B, G, R)
            if bias:
                bias_bgr = hex_to_bgr(bias)
                c2 = tuple(min(255, max(0, c2[i] + bias_bgr[i])) for i in range(3))
            dist = sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
            return 1 - dist / (3 * 255)
        
        # 4. 遍历查找
        checked_pixels = 0
        for idx, (col_hex, bias) in enumerate(color_defs):
            target_bgr = hex_to_bgr(col_hex)
            for x, y in gen_coords(width, height, dir):
                pix = pixels[x, y][:3]
                similarity = color_sim(pix, target_bgr, bias)
                checked_pixels += 1
                if similarity >= sim:
                    # logger.info(f"FindColor: 匹配成功 idx={idx}, 坐标=({x1 + x},{y1 + y}), 像素={bgr_to_hex(pix)}, 目标={bgr_to_hex(target_bgr)}, 相似度={similarity:.3f}")
                    return idx, x1 + x, y1 + y
        return -1, None, None

    def match_point_color(
        self, image: Image.Image, x: int, y: int, color, range_: int, ambiguity: float = 0.95, dir: int = 0
    ) -> bool:
        """
        判断指定点(x, y)附近区域是否存在指定颜色。
        :param image: PIL.Image，原始图片
        :param x: 检查点的x坐标
        :param y: 检查点的y坐标
        :param color: 颜色字符串（"BBGGRR"）或RGB列表/元组([B,G,R])
        :param range_: 匹配范围
        :param ambiguity: 相似度
        :param dir: 查找方向
        :return: bool
        """
        x1 = x - range_
        y1 = y - range_
        x2 = x + range_
        y2 = y + range_
        # 支持两种格式
        if isinstance(color, (list, tuple)) and len(color) == 3:
            # 直接比对RGB
            def color_sim(c1, c2):
                dist = sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
                return 1 - dist / (3 * 255)
            region = image.crop((x1, y1, x2, y2)).convert('RGB')
            width, height = region.size
            pixels = region.load()
            if pixels is None:
                return False
            for dx in range(width):
                for dy in range(height):
                    pix = pixels[dx, dy][:3]
                    if color_sim(pix, color) >= ambiguity:
                        return True
            return False
        else:
            # 走原有16进制字符串逻辑，确保color为str
            if not isinstance(color, str):
                color = '{:02X}{:02X}{:02X}'.format(*color)
            idx, intX, intY = self.FindColor(image, x1, y1, x2, y2, color, ambiguity, dir)
            return intX is not None and intY is not None and intX > -1 and intY > -1

    def match_image_multi(
        self,
        image: Union[Image.Image, np.ndarray, str, None],
        template_path: str,
        threshold: float = 0.95,
        region: Optional[Tuple[int, int, int, int]] = None,
        gray: bool = False,
    ) -> list[tuple[int, int, float]]:
        """
        多模板匹配，返回所有相关系数大于等于阈值的点坐标及分数，并将所有匹配区域画框保存到debug目录。
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param template_path: 模板图片路径
        :param threshold: 匹配阈值，默认0.8
        :param region: (x1, y1, x2, y2) 匹配区域，默认全图
        :param gray: 是否灰度匹配
        :return: [(x, y, score), ...]，所有匹配点的左上角坐标及分数
        """
        import numpy as np
        try:
            # 1. 读取主图像，转为BGR格式
            if image is None:
                logger.error("Input image is None")
                return []
            if isinstance(image, str):
                image = cv2.imread(get_asset_path(image))
            elif isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            orig_image = image.copy()

            # 2. 读取模板
            base, ext = os.path.splitext(template_path)
            if "__" in base:
                region_str = base.split("__")[-1]
                region_tuple = tuple(map(int, region_str.split("_")))
                if len(region_tuple) == 4:
                    region = region_tuple
                    logger.info(f"自动提取region坐标: {region}")
            template = cv2.imread(get_asset_path(template_path))
            if template is None:
                logger.error(f"模板图片读取失败: {template_path}")
                return []
            th, tw = template.shape[:2]

            # 3. 匹配区域裁剪
            offset_x, offset_y = 0, 0
            if region is not None:
                x1, y1, x2, y2 = region
                image_crop = image[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1
            else:
                image_crop = image

            # 4. 灰度化
            if gray:
                img_proc = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
                template_proc = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                img_proc = image_crop
                template_proc = template

            # 5. 模板匹配
            res = cv2.matchTemplate(img_proc, template_proc, cv2.TM_CCOEFF_NORMED)
            y_idxs, x_idxs = np.where(res >= threshold)
            matches = []
            debug_img = orig_image.copy()
            for (x, y) in zip(x_idxs, y_idxs):
                score = float(res[y, x])
                abs_x, abs_y = x + offset_x, y + offset_y
                matches.append((abs_x, abs_y, score))
                # 画矩形框
                cv2.rectangle(debug_img, (abs_x, abs_y), (abs_x + tw, abs_y + th), (0, 0, 255), 2)
            # 保存debug图片
            os.makedirs("debug", exist_ok=True)
            cv2.imwrite("debug/match_image_multi_result.png", debug_img)
            return matches
        except Exception as e:
            logger.error(f"match_image_multi 执行异常: {e}")
            return [] 

    @staticmethod
    def save_debug_rect(image: Image.Image, rect: tuple, save_path: str, outline: str = "red", width: int = 2) -> None:
        """
        在图片指定区域画框并保存到指定路径，常用于调试截图。
        :param image: PIL.Image对象
        :param rect: (x1, y1, x2, y2) 矩形区域
        :param save_path: 保存路径
        :param outline: 框线颜色，默认红色
        :param width: 框线宽度，默认2
        """
        import os
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        draw.rectangle(rect, outline=outline, width=width)
        img_copy.save(save_path) 

    def match_point_color_mult(self, image: Image.Image, points: list[tuple[int, int]], color, range_: int, ambiguity: float = 0.95, dir: int = 0) -> list[tuple[int, int]]:
        """
        支持多点颜色匹配，返回所有匹配的点坐标。
        :param image: PIL.Image，原始图片
        :param points: [(x, y), ...]，待检测的点坐标列表
        :param color: 颜色字符串（"BBGGRR"）或RGB列表/元组([B,G,R])
        :param range_: 匹配范围
        :param ambiguity: 相似度
        :param dir: 查找方向
        :return: 匹配成功的点坐标列表
        """
        matched_points = []
        for x, y in points:
            if self.match_point_color(image, x, y, color, range_, ambiguity, dir):
                matched_points.append((x, y))
        return matched_points 