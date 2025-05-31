import uiautomator2 as u2
from utils import logger
import time
from PIL import Image
import cv2
import numpy as np
import os
from typing import Optional
from common.config import config
import traceback

class DeviceManager:
    def __init__(self):
        self.device = None
        self.config = config.device
        self.adb_address = self.config.adb_address
        self.screenshot_cache = None
    
    def connect_device(self, device_id: Optional[str] = None) -> bool:
        """
        连接设备，优先级：device_id参数 > adb_address参数 > 配置文件
        :param device_id: 可选，直接指定设备ID/地址
        :return: 是否连接成功
        """
        try:
            retry_count = self.config.retry_count
            config_adb_address = self.config.adb_address
            
            for i in range(retry_count):
                try:
                    # 优先级：device_id > self.adb_address > config_adb_address
                    target_id = device_id or self.adb_address or config_adb_address
                    if target_id:
                        self.device = u2.connect(target_id)
                    else:
                        self.device = u2.connect()
                    
                    # 测试连接
                    self.device.info
                    logger.info(f"Successfully connected to device: {self.device.info}")
                    return True
                except Exception as e:
                    logger.warning(f"Connection attempt {i+1} failed: {str(e)}\n{traceback.format_exc()}")
                    if i < retry_count - 1:
                        time.sleep(2)
                    continue
            
            logger.error("Failed to connect to device after all retries")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to device: {str(e)}\n{traceback.format_exc()}")
            return False
        
    def get_current_screenshot(self) -> Optional[Image.Image]:
        """
        获取当前屏幕截图，返回PIL.Image对象
        :return: PIL.Image 或 None
        """
        return self.screenshot_cache
    
    def get_screenshot(self) -> Optional[Image.Image]:
        """
        获取当前屏幕截图，返回PIL.Image对象
        :return: PIL.Image 或 None
        """
        try:
            if self.device:
                # uiautomator2 支持 format='opencv' 或 'pil'
                img = self.device.screenshot(format='opencv')
                if img is not None:
                    # OpenCV格式(BGR)转PIL(RGB)
                    if isinstance(img, np.ndarray):
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(img_rgb)
                        self.screenshot_cache = pil_img
                        return pil_img
                    elif isinstance(img, Image.Image):
                        self.screenshot_cache = img
                        return img
                    else:
                        logger.error("Unknown screenshot image type")
                        return None
            return None
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}\n{traceback.format_exc()}")
            return None 

    def get_screenshot_region(self, x1: int, y1: int, x2: int, y2: int) -> Optional[Image.Image]:
        """
        获取指定区域的屏幕截图，返回PIL.Image对象
        :param x1: 区域左上角x
        :param y1: 区域左上角y
        :param x2: 区域右下角x
        :param y2: 区域右下角y
        :return: PIL.Image 或 None
        """
        img = self.get_screenshot()
        if img is None:
            logger.error("No screenshot available for region crop.")
            return None
        try:
            region = img.crop((x1, y1, x2, y2))
            return region
        except Exception as e:
            logger.error(f"Failed to crop screenshot region: {str(e)}\n{traceback.format_exc()}")
            return None

    def save_image(self, img: Image.Image, save_path: str) -> None:
        """
        保存PIL.Image对象到指定路径
        :param img: PIL.Image对象
        :param save_path: 保存路径
        """
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path)
            logger.info(f"Image saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}\n{traceback.format_exc()}")

    def click(self, x: int, y: int) -> None:
        """
        点击指定坐标，并输出日志
        :param x: 横坐标
        :param y: 纵坐标
        """
        try:
            if self.device:
                logger.debug(f"点击坐标 ({x}, {y})")
                self.device.click(x, y)
            else:
                logger.error("设备未连接，无法点击")
        except Exception as e:
            logger.error(f"点击坐标 ({x}, {y}) 失败: {str(e)}\n{traceback.format_exc()}") 