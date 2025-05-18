from paddleocr import PaddleOCR
from loguru import logger
import yaml
import cv2
import numpy as np
from PIL import Image

class OCRHandler:
    def __init__(self):
        # 加载配置
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 初始化OCR
        self.ocr = PaddleOCR(
            use_angle_cls=config["ocr"]["use_angle_cls"],
            lang=config["ocr"]["lang"],
            show_log=False
        )
        self.threshold = config["ocr"]["threshold"]
        logger.info("OCR handler initialized")
    
    def recognize_text(self, image):
        """
        识别图片中的文字
        :param image: 支持 PIL.Image、OpenCV numpy.ndarray、图片路径
        :return: 识别结果列表
        """
        try:
            if image is None:
                logger.error("Input image is None")
                return []

            # 如果是 PIL.Image，先转成 OpenCV 格式（BGR）
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            result = self.ocr.ocr(image, cls=True)
            
            if not result:
                return []
            
            processed_results = []
            for line in result:
                for item in line:
                    confidence = item[1][1]
                    if confidence >= self.threshold:
                        processed_results.append({
                            'text': item[1][0],
                            'box': item[0],
                            'confidence': confidence
                        })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {str(e)}")
            return [] 