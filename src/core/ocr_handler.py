import os
import gc
import cv2
import threading
import traceback
from typing import List, Optional, Tuple, Union, Any
import numpy as np
from PIL import Image, ImageDraw
from utils.frozen_fix import fix_frozen_environment, safe_import_paddleocr
from utils import logger
from utils.get_asset_path import get_asset_path
import concurrent.futures
import sys

class OCRHandler:
    def __init__(self, device_manager, model_dir: Optional[str] = None, show_logger:bool = False) -> None:
        """
        初始化OCR处理器
        :param device_manager: 设备管理器实例
        :param model_dir: 模型目录路径，如果为None则使用默认路径
        :param show_logger: 是否显示OCR日志
        """
        self.device_manager = device_manager
        
        # 修复打包环境问题
        fix_frozen_environment()
        
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ocr", "model")
        
        try:
            # 安全导入PaddleOCR
            PaddleOCR = safe_import_paddleocr()
            
            # 初始化PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                det_model_dir=os.path.join(model_dir, "whl", "det", "ch", "ch_PP-OCRv4_det_infer"),
                rec_model_dir=os.path.join(model_dir, "whl", "rec", "ch", "ch_PP-OCRv4_rec_infer"),
                cls_model_dir=os.path.join(model_dir, "whl", "cls", "ch_ppocr_mobile_v2.0_cls_infer"),
                show_log=False
            )
            
            # 初始化数字识别模型
            self.ocr_digit = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                det_model_dir=os.path.join(model_dir, "whl", "det", "en", "en_PP-OCRv3_det_infer"),
                rec_model_dir=os.path.join(model_dir, "whl", "rec", "en", "en_PP-OCRv3_rec_infer"),
                cls_model_dir=os.path.join(model_dir, "whl", "cls", "ch_ppocr_mobile_v2.0_cls_infer"),
                show_log=False
            )
            
            logger.info("OCR模型初始化成功")
            
        except Exception as e:
            logger.error(f"OCR模型初始化失败: {e}")
            # 如果是打包环境，尝试更简单的初始化方式
            if getattr(sys, 'frozen', False):
                try:
                    logger.info("尝试使用简化模式初始化OCR...")
                    # 使用默认参数，不指定具体模型路径
                    PaddleOCR = safe_import_paddleocr()
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                    self.ocr_digit = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                    logger.info("OCR模型简化模式初始化成功")
                except Exception as e2:
                    logger.error(f"OCR模型简化模式初始化也失败: {e2}")
                    raise e2
            else:
                raise
        
        self.ocr_lock = threading.Lock()  # 新增：OCR推理锁

    def cleanup(self):
        """清理OCR处理器资源"""
        logger.info("清理OCR处理器资源...")
        
        # 清理OCR模型（PaddleOCR没有显式的清理方法，但可以删除引用）
        if hasattr(self, 'ocr'):
            del self.ocr
        if hasattr(self, 'ocr_digit'):
            del self.ocr_digit
        
        # 强制垃圾回收
        gc.collect()
        logger.info("OCR处理器资源清理完成")

    def match_texts(
        self,
        keywords: List[str],
        image: Union[Image.Image, np.ndarray, str,None] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8
    ) -> bool:
        """
        检查截图OCR结果中是否全部匹配给定文案数组
        :param keywords: 需要匹配的文案字符串数组
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param region: 可选，(x1, y1, x2, y2) 指定识别区域坐标，默认全屏
        :param threshold: 可信度阈值
        :return: bool，是否全部匹配
        """
        original_image = image
        processed_image = None
        
        try:
            # 自动截图
            if image is None:
                if not hasattr(self, "device_manager"):
                    logger.error("OCRHandler未绑定device_manager，无法截图")
                    return False
                image = self.device_manager.get_screenshot()
            if image is None:
                logger.warning("无法获取截图，无法进行文本匹配")
                return False

            # 区域裁剪
            if region is not None:
                if isinstance(image, Image.Image):
                    processed_image = image.crop(region)
                elif isinstance(image, np.ndarray):
                    x1, y1, x2, y2 = region
                    processed_image = image[y1:y2, x1:x2]
                else:
                    logger.warning("region参数仅支持PIL.Image或np.ndarray类型图片裁剪")
                    processed_image = image
            else:
                processed_image = image
                
            if isinstance(processed_image, Image.Image):
                processed_image = cv2.cvtColor(np.array(processed_image), cv2.COLOR_RGB2BGR)
            with self.ocr_lock:
                result = self.ocr.ocr(processed_image, cls=True)
            if not result:
                logger.warning("OCR无结果")
                return False
            detected_texts = set()
            all_texts = []
            for line in result:
                if line is None:
                    continue
                for item in line:
                    text = item[1][0]
                    confidence = item[1][1]
                    all_texts.append((text, confidence))
                    if confidence >= threshold:
                        detected_texts.add(text)
            # logger.debug(f"OCR识别文本及置信度: {[f'{t}:{c:.2f}' for t,c in all_texts]}")
            for kw in keywords:
                if not any(kw in t for t in detected_texts):
                    logger.debug(f"未检测到关键词: {kw}")
                    return False
            logger.debug(f"全部关键词匹配: {keywords}")
            return True
        except Exception as e:
            logger.error(f"OCR匹配失败: {str(e)}\n{traceback.format_exc()}")
            return False
        finally:
            # 及时释放图像对象，避免内存泄漏
            if processed_image is not None and processed_image is not original_image:
                del processed_image
            # 强制垃圾回收图像相关对象
            if 'processed_image' in locals():
                del processed_image

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
            with self.ocr_lock:
                result = self.ocr.ocr(image, cls=True)
            if not result:
                logger.warning("OCR无结果")
                return False

            detected_texts = []
            for line in result:
                if line is None:
                    continue
                for item in line:
                    text = item[1][0]
                    confidence = item[1][1]
                    box = item[0]
                    if confidence >= threshold:
                        detected_texts.append((text, box, confidence))

            # 检查所有关键词是否都匹配
            for kw in keywords:
                if not any(kw in t for t, _, _ in detected_texts):
                    logger.debug(f"未检测到关键词: {kw}")
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
                        logger.debug(f"点击文本 '{text}' 的中心点 ({x},{y})，置信度{confidence:.2f} (已加region偏移)")
                        return True
                    else:
                        logger.warning("OCRHandler未绑定device_manager，无法点击")
                        return False
            logger.debug("所有关键词匹配，但未找到可点击的文本区域")
            return False
        except Exception as e:
            logger.error(f"match_click_text 执行异常: {e}\n{traceback.format_exc()}")
            return False

    def recognize_text(self, image:Union[Image.Image, np.ndarray, str, None] = None, region: Optional[Tuple[int, int, int, int]] = None, rec_char_type: str = 'all', scale: int = 2):
        """
        识别图片中的文字，可指定识别区域。
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :param region: (x1, y1, x2, y2) 可选，指定识别区域坐标，默认全图
        :param rec_char_type: 'all' 或 'digit'
        :param scale: region有值时放大倍数，默认2
        :return: 识别结果列表
        """
        try:
            if image is None:
                image = self.device_manager.get_screenshot()
            # 区域裁剪前，若指定region，保存画红框的调试图片
            if region is not None:
                # 只支持PIL.Image调试保存
                # if isinstance(image, Image.Image):
                #     os.makedirs("debug", exist_ok=True)
                #     img_copy = image.copy()
                #     draw = ImageDraw.Draw(img_copy)
                #     draw.rectangle(region, outline="red", width=2)
                #     filename = f"debug/ocr_region.png"
                #     img_copy.save(filename)
                #     logger.debug(f"已保存OCR裁剪区域调试图: {filename}")
                # 裁剪
                if isinstance(image, Image.Image):
                    image = image.crop(region)
                    # 放大
                    if scale > 1:
                        w, h = image.size
                        from PIL import Image as PILImage
                        image = image.resize((w * scale, h * scale), PILImage.Resampling.LANCZOS)
                elif isinstance(image, np.ndarray):
                    x1, y1, x2, y2 = region
                    image = image[y1:y2, x1:x2]
                    # 放大
                    if scale > 1:
                        image = cv2.resize(image, ((x2-x1)*scale, (y2-y1)*scale), interpolation=cv2.INTER_LANCZOS4)
                else:
                    logger.warning("region参数仅支持PIL.Image或np.ndarray类型图片裁剪")
            # 如果是 PIL.Image，先转成 OpenCV 格式（BGR）
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            with self.ocr_lock:
                if rec_char_type == 'digit':
                    result = self.ocr_digit.ocr(image, cls=True)
                else:
                    result = self.ocr.ocr(image, cls=True)
            
            if result is None or not result:
                logger.warning("OCR无结果")
                return []
            
            processed_results = []
            for line in result:          
                if line is None:
                    continue
                for item in line:
                    confidence = item[1][1]
                    if confidence >= 0.8:  # 使用固定阈值
                        # logger.debug(f"OCR识别文本: {item[1][0]}，置信度: {confidence:.2f}") 
                        processed_results.append({
                            'text': item[1][0],
                            'box': item[0],
                            'confidence': confidence
                        })
            return processed_results
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {str(e)}\n{traceback.format_exc()}")
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
            # logger.debug(f"模板匹配最大相关系数: {max_val:.3f}")

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
                logger.debug(f"匹配区域已保存到debug/match_image_result.png")

            # 7. 匹配结果坐标
            if max_val >= threshold:
                match_x = max_loc[0] + (region[0] if region else 0)
                match_y = max_loc[1] + (region[1] if region else 0)
                # logger.debug(f"模板匹配成功，坐标: ({match_x}, {match_y})")
                return (match_x, match_y)
            else:
                logger.debug("模板未匹配成功")
                return None
        except Exception as e:
            logger.error(f"模板匹配失败: {str(e)}\n{traceback.format_exc()}")
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
            hexstr = str(hexstr).lstrip('#')
            if len(hexstr) != 6:
                logger.error(f"Invalid color hex: {hexstr}")
                return None
            try:
                return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))
            except Exception as e:
                logger.error(f"hex_to_bgr error: {hexstr}, {e}")
                return None

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
                if bias_bgr is not None:
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
                    # logger.debug(f"FindColor: 匹配成功 idx={idx}, 坐标=({x1 + x},{y1 + y}), 像素={bgr_to_hex(pix)}, 目标={bgr_to_hex(target_bgr)}, 相似度={similarity:.3f}")
                    return idx, x1 + x, y1 + y
        return -1, None, None


    def match_point_color(self, image: Image.Image, points: list[tuple[int, int, str, int]], 
                                ambiguity: float = 0.95, dir: int = 0, debug = False) -> bool:
        """
        高性能多点颜色匹配：所有点都需匹配成功才返回True
        :param image: PIL.Image，原始图片
        :param points: [(x, y, color, range_), ...]，待检测的点坐标列表
        :param ambiguity: 相似度
        :param dir: 查找方向
        :return: bool，所有点都匹配才返回True
        """
        try:
            # 5. 支持多点并行（默认多线程并行，避免多进程pickle问题）
            # 预处理：将所有点的区域crop出来，避免重复读取
            regions = []  # [(region_img, x, y, color, range_)]
            for x, y, color, range_ in points:
                x1 = x - range_
                y1 = y - range_
                x2 = x + range_
                y2 = y + range_
                region = image.crop((x1, y1, x2, y2)).convert('RGB')
                regions.append((region, x, y, color, range_))

            # 定义单点匹配函数（多线程可用闭包）
            def check_point(region_img, color, ambiguity):
                width, height = region_img.size
                pixels = region_img.load()
                if pixels is None:
                    return False
                if isinstance(color, (list, tuple)) and len(color) == 3:
                    def color_sim(c1, c2):
                        dist = sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
                        return 1 - dist / (3 * 255)
                    for dx in range(width):
                        for dy in range(height):
                            pix = pixels[dx, dy][:3]
                            if color_sim(pix, color) >= ambiguity:
                                return True
                    return False
                else:
                    # 先确保color为str并去除#前缀
                    if not isinstance(color, str):
                        color = '{:02X}{:02X}{:02X}'.format(*color)
                    color = str(color).lstrip('#')
                    def hex_to_bgr(hexstr):
                        hexstr = str(hexstr).lstrip('#')
                        if len(hexstr) != 6:
                            logger.error(f"Invalid color hex: {hexstr}")
                            return None
                        try:
                            return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))
                        except Exception as e:
                            logger.error(f"hex_to_bgr error: {hexstr}, {e}")
                            return None
                    target_bgr = hex_to_bgr(color)
                    if target_bgr is None:
                        return False
                    def color_sim(c1, c2):
                        dist = sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
                        return 1 - dist / (3 * 255)
                    for dx in range(width):
                        for dy in range(height):
                            pix = pixels[dx, dy][:3]
                            if color_sim(pix, target_bgr) >= ambiguity:
                                return True
                    return False

            # 多线程并行检查所有点
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_region_pairs = [
                    (executor.submit(check_point, region_img, color, ambiguity), (region_img, x, y, color, range_))
                    for region_img, x, y, color, range_ in regions
                ]
                all_passed = True
                for future, (region_img, x, y, color, range_) in future_region_pairs:
                    result = future.result()
                    if not result:
                        all_passed = False
                if not all_passed:
                    return False
            return True
        except Exception as e:
            logger.error(f"match_point_color_mult 执行异常: {e}\n{traceback.format_exc()}")
            return False

    def match_image_multi(
        self,
        image: Union[Image.Image, np.ndarray, str, None],
        template_path: str,
        threshold: float = 0.95,
        region: Optional[Tuple[int, int, int, int]] = None,
        gray: bool = False,
        debug: bool = False,
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
            if debug:
                os.makedirs("debug", exist_ok=True)
                cv2.imwrite("debug/match_image_multi_result.png", debug_img)
            return matches
        except Exception as e:
            logger.error(f"match_image_multi 执行异常: {e}\n{traceback.format_exc()}")
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

