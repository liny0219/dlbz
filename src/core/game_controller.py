from loguru import logger
import numpy as np
import time

class GameController:
    def __init__(self, device_manager, ocr_handler):
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.device = device_manager.device
    
    def find_and_click_text(self, text, max_retries=3):
        """查找并点击文字"""
        try:
            for i in range(max_retries):
                # 获取屏幕截图
                screenshot = self.device_manager.get_screenshot()
                if screenshot is None:
                    continue
                
                # 识别文字
                results = self.ocr_handler.recognize_text(screenshot)
                
                # 查找匹配的文字
                for result in results:
                    if text in result['text']:
                        # 计算点击位置（文字框的中心）
                        box = np.array(result['box'])
                        center_x = int(np.mean(box[:, 0]))
                        center_y = int(np.mean(box[:, 1]))
                        
                        # 点击
                        self.device.click(center_x, center_y)
                        logger.info(f"Clicked text '{text}' at ({center_x}, {center_y})")
                        return True
                
                if i < max_retries - 1:
                    logger.warning(f"Text '{text}' not found, retrying...")
                    time.sleep(1)
            
            logger.warning(f"Text '{text}' not found after {max_retries} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error in find_and_click_text: {str(e)}")
            return False
    
    def swipe(self, fx, fy, tx, ty, duration=0.1):
        """滑动操作"""
        try:
            self.device.swipe(fx, fy, tx, ty, duration=duration)
            logger.info(f"Swiped from ({fx}, {fy}) to ({tx}, {ty})")
            return True
        except Exception as e:
            logger.error(f"Swipe operation failed: {str(e)}")
            return False 