import uiautomator2 as u2
from utils import logger
import time
from PIL import Image
import cv2
import numpy as np
import os
from typing import Optional, Union
from common.config import config
import traceback
import gc

class DeviceManager:
    def __init__(self):
        """
        初始化设备管理器
        """
        self.device = None
        self.config = config.device
        self.adb_address = self.config.adb_address

    def cleanup(self):
        """清理设备管理器资源"""
        logger.info("清理设备管理器资源...")
        try:
            if self.device:
                # 关闭设备连接
                try:
                    # 尝试停止所有应用
                    if hasattr(self.device, 'app_stop_all'):
                        self.device.app_stop_all()
                except Exception as e:
                    logger.warning(f"停止应用时发生异常: {e}")
                
                # 清理设备引用
                self.device = None
            
            # 清理配置引用
            if hasattr(self, 'config'):
                del self.config
            
            # 强制垃圾回收
            gc.collect()
            
        except Exception as e:
            logger.warning(f"清理设备管理器资源时发生异常: {e}")
        finally:
            logger.info("设备管理器资源清理完成")
    
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
        
    def get_screenshot(self) -> Optional[Image.Image]:
        """
        获取当前屏幕截图，返回PIL.Image对象
        :return: PIL.Image 或 None
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return None
            
            # 使用uiautomator2获取截图
            img = self.device.screenshot()
            
            if img is not None:
                if isinstance(img, np.ndarray):
                    # OpenCV格式转换为PIL格式
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    return pil_img
                elif isinstance(img, Image.Image):
                    return img
                else:
                    logger.error(f"Unexpected image type: {type(img)}")
                    return None
            else:
                logger.error("Failed to get screenshot")
                return None
                
        except Exception as e:
            logger.error(f"Error getting screenshot: {e}")
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
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path)
            logger.info(f"Image saved to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}\n{traceback.format_exc()}")

    def click(self, x: int, y: int) -> None:
        """
        点击指定坐标
        :param x: x坐标
        :param y: y坐标
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.click(x, y)
            logger.debug(f"Clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to click at ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def double_click(self, x: int, y: int) -> None:
        """
        双击指定坐标
        :param x: x坐标
        :param y: y坐标
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.double_click(x, y)
            logger.debug(f"Double clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to double click at ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def long_click(self, x: int, y: int, duration: float = 0.5):
        """
        长按指定坐标
        :param x: x坐标
        :param y: y坐标
        :param duration: 长按持续时间（秒）
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.long_click(x, y, duration=duration)
            logger.debug(f"Long clicked at ({x}, {y}) for {duration}s")
        except Exception as e:
            logger.error(f"Failed to long click at ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def press_down(self, x: int, y: int):
        """
        按下指定坐标
        :param x: x坐标
        :param y: y坐标
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.long_click(x, y, duration=0.1)
            logger.debug(f"Pressed down at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to press down at ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def press_move(self, x: int, y: int):
        """
        移动到指定坐标
        :param x: x坐标
        :param y: y坐标
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.swipe(x, y, x, y, duration=0.1)
            logger.debug(f"Moved to ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to move to ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def press_up(self, x: int, y: int):
        """
        在指定坐标释放
        :param x: x坐标
        :param y: y坐标
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            # 这里可能需要根据具体的uiautomator2 API调整
            logger.debug(f"Released at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to release at ({x}, {y}): {str(e)}\n{traceback.format_exc()}")

    def press_and_drag_step(self, start:tuple, end:tuple,drag_press_time:float=0.1,drag_wait_time:float=0.3):
        """
        拖拽操作
        :param start: 起始坐标 (x, y)
        :param end: 结束坐标 (x, y)
        :param drag_press_time: 按下时间
        :param drag_wait_time: 拖拽等待时间
        """
        try:
            if self.device is None:
                logger.error("Device not connected")
                return
            self.device.drag(start[0], start[1], end[0], end[1], duration=drag_press_time)
            time.sleep(drag_wait_time)
            logger.debug(f"Dragged from {start} to {end}")
        except Exception as e:
            logger.error(f"Failed to drag from {start} to {end}: {str(e)}\n{traceback.format_exc()}")

    def save_screenshot(self, img_or_path: Union[Image.Image, str], save_path: Optional[str] = None) -> None:
        """
        保存截图到指定路径
        :param img_or_path: PIL.Image对象或截图路径
        :param save_path: 保存路径，如果为None则使用img_or_path
        """
        try:
            if isinstance(img_or_path, str):
                # 如果传入的是路径，直接复制文件
                if save_path is None:
                    save_path = img_or_path
                import shutil
                shutil.copy2(img_or_path, save_path)
                logger.info(f"Screenshot copied to: {save_path}")
            elif isinstance(img_or_path, Image.Image):
                # 如果传入的是PIL.Image对象，保存图像
                if save_path is None:
                    save_path = f"screenshot_{int(time.time())}.png"
                self.save_image(img_or_path, save_path)
            else:
                logger.error(f"Invalid image type: {type(img_or_path)}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}\n{traceback.format_exc()}")