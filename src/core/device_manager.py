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
import threading

class DeviceManager:
    def __init__(self):
        """
        初始化设备管理器
        """
        self.device = None
        self.config = config.device
        self.adb_address = self.config.adb_address
        self.screenshot_cache = None
        self._screenshot_lock = threading.Lock()
        self._cache_in_use = 0

    def _cleanup_cache(self):
        """清理截图缓存，防止内存泄漏"""
        if self.screenshot_cache is not None:
            self.screenshot_cache.close()
            self.screenshot_cache = None
        gc.collect()  # 强制垃圾回收
        logger.debug("截图缓存已清理")
    
    def cleanup(self):
        """清理设备管理器资源"""
        logger.info("清理设备管理器资源...")
        self._cleanup_cache()
        if self.device:
            try:
                # 关闭设备连接
                self.device = None
            except Exception as e:
                logger.warning(f"关闭设备连接时发生异常: {e}")
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
        
    def get_cache_screenshot(self):
        """
        获取截图缓存上下文管理器 - 专为子线程设计
        
        设计意图：
        - 避免主线程和子线程之间的截图竞争
        - 主线程使用 get_screenshot() 获取新截图并更新缓存
        - 子线程使用此方法获取缓存的截图副本
        
        使用场景：
        - 子线程需要频繁检查屏幕状态（如 check_info 线程）
        - 避免与主线程的截图操作产生竞争条件
        - 减少设备截图调用频率，提高性能
        
        线程安全机制：
        - 使用 _screenshot_lock 保护缓存访问
        - 使用 _cache_in_use 引用计数防止缓存被过早释放
        - 返回缓存的副本，避免多线程同时修改同一图像
        
        错误修复历史：
        - 之前错误：在缓存为空时调用 get_screenshot() 导致竞争条件
        - 修复方案：缓存为空时返回None，由调用方处理
        - 原因：get_screenshot() 会获取新截图，与主线程产生竞争
        
        :return: CacheContext 上下文管理器，使用 with 语句获取截图
        """
        # 不在这里调用get_screenshot()，避免竞争条件
        # 缓存为空时返回None，由调用方处理
        return self.CacheContext(self)

    def get_screenshot(self) -> Optional[Image.Image]:
        """
        获取当前屏幕截图，返回PIL.Image对象 - 主线程专用
        
        设计意图：
        - 主线程获取新截图的主要方法
        - 同时更新缓存供子线程使用
        - 智能管理缓存生命周期
        
        线程安全机制：
        - 使用 _screenshot_lock 保护缓存更新
        - 检查 _cache_in_use 引用计数
        - 只有在没有子线程使用时才释放旧缓存
        
        缓存管理策略：
        - 如果 _cache_in_use == 0：释放旧缓存，设置新缓存
        - 如果 _cache_in_use > 0：保留旧缓存，设置新缓存
        - 确保子线程始终能获取到有效的截图副本
        
        错误修复历史：
        - 之前错误：CacheContext 返回的对象类型不正确
        - 修复方案：确保返回 PIL.Image 对象而不是 CacheContext 对象
        - 原因：OCR 和其他图像处理函数需要 PIL.Image 类型
        
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
                    with self._screenshot_lock:
                        # 如果没有子线程在用，释放旧cache
                        if self._cache_in_use == 0 and self.screenshot_cache is not None:
                            self.screenshot_cache = None
                        self.screenshot_cache = pil_img
                    return pil_img
                elif isinstance(img, Image.Image):
                    with self._screenshot_lock:
                        # 如果没有子线程在用，释放旧cache
                        if self._cache_in_use == 0 and self.screenshot_cache is not None:
                            self.screenshot_cache = None
                        self.screenshot_cache = img
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

    def double_click(self, x: int, y: int) -> None:
        """
        点击指定坐标，并输出日志
        :param x: 横坐标
        :param y: 纵坐标
        """
        try:
            if self.device:
                logger.debug(f"双击坐标 ({x}, {y})")
                self.device.double_click(x, y)
            else:
                logger.error("设备未连接，无法点击")
        except Exception as e:
            logger.error(f"点击坐标 ({x}, {y}) 失败: {str(e)}\n{traceback.format_exc()}") 
    
    def long_click(self, x: int, y: int, duration: float = 0.5):
        """
        长按指定坐标
        :param x: 横坐标
        :param y: 纵坐标
        :param duration: 长按时间 (秒)
        """
        if not self.device:
            logger.error("设备未连接，无法长按")
            return
        logger.debug(f"长按: {duration} 秒")
        self.device.long_click(x, y, duration)
    
    def press_down(self, x: int, y: int):
        """
        按下指定坐标
        :param x: 横坐标
        :param y: 纵坐标
        """
        if self.device is None:
            logger.error("设备未连接，无法按下")
            return
        logger.info(f"按下: {x}, {y}")
        self.device.touch.down(x, y)

    def press_move(self, x: int, y: int):
        """
        按下并移动指定坐标
        :param x: 横坐标
        :param y: 纵坐标
        """
        if self.device is None:
            logger.error("设备未连接，无法按下并移动")
            return
        self.device.touch.move(x, y)

    def press_up(self, x: int, y: int):
        """
        抬起指定坐标
        :param x: 横坐标
        :param y: 纵坐标
        """
        if self.device is None:
            logger.error("设备未连接，无法抬起")
            return
        logger.info(f"抬起: {x}, {y}")
        self.device.touch.up(x, y)

    def press_and_drag_step(self, start:tuple, end:tuple,drag_press_time:float=0.1,drag_wait_time:float=0.3):
        """
        长按和拖动指定坐标
        :param start: 起始坐标 (x, y)
        :param end: 结束坐标 (x, y)
        :param drag_press_time: 长按时间 (秒)
        :param drag_wait_time: 拖动时间 (秒)
        :param duration: 拖动时间 (秒)
        """
        if not self.device:
            logger.error("设备未连接，无法长按和拖动")
            return
        start_x, start_y = start
        end_x, end_y = end
        logger.debug(f"长按: {drag_press_time} 秒")
        self.device.touch.down(start_x, start_y)
        time.sleep(drag_press_time)
        logger.debug(f"拖动: {start} -> {end} {drag_wait_time} 秒")
        self.device.touch.move(end_x, end_y)
        time.sleep(drag_wait_time)
        self.device.touch.up(end_x, end_y)

    def save_screenshot(self, img_or_path: Union[Image.Image, str], save_path: Optional[str] = None) -> None:
        """
        保存截图到指定路径。
        - 如果只传一个参数（img_or_path为str），则获取当前截图并保存到该路径。
        - 如果传入PIL.Image对象和路径，则保存该图片到路径。
        :param img_or_path: PIL.Image对象 或 保存路径（str）
        :param save_path: 保存路径（可选）
        """
        if save_path is None and isinstance(img_or_path, str):
            # 只传了路径，自动截图
            save_path = img_or_path
            img = self.get_screenshot()
        else:
            img = img_or_path
        if isinstance(img, Image.Image) and save_path is not None:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path)
            logger.info(f"Screenshot saved to {save_path}")
        else:
            logger.error("Failed to save screenshot: image is not a PIL.Image.Image or path is None")

    class CacheContext:
        """
        截图缓存上下文管理器 - 线程安全的缓存访问
        
        设计意图：
        - 为子线程提供线程安全的缓存访问机制
        - 使用引用计数确保缓存不会被过早释放
        - 返回缓存的副本，避免多线程数据竞争
        
        工作原理：
        1. __enter__: 增加引用计数，返回缓存副本
        2. __exit__: 减少引用计数，允许缓存被释放
        
        线程安全保证：
        - 使用 _screenshot_lock 保护引用计数操作
        - 引用计数确保缓存在使用期间不会被释放
        - 返回副本避免多线程同时修改同一图像
        
        错误修复历史：
        - 之前错误：直接返回缓存对象，导致多线程竞争
        - 修复方案：返回缓存的 copy() 副本
        - 原因：PIL.Image 的 copy() 方法创建独立副本
        
        使用示例：
        with device_manager.get_cache_screenshot() as screenshot:
            if screenshot is not None:
                # 处理截图
                process_image(screenshot)
        """
        def __init__(self, manager):
            """
            初始化缓存上下文管理器
            
            :param manager: DeviceManager 实例
            """
            self.manager = manager
            self.img = None
            
        def __enter__(self):
            """
            进入上下文，获取缓存截图副本
            
            线程安全操作：
            - 获取锁保护引用计数
            - 增加引用计数
            - 返回缓存副本
            
            :return: PIL.Image 或 None
            """
            with self.manager._screenshot_lock:
                self.manager._cache_in_use += 1
                if self.manager.screenshot_cache is not None:
                    # 使用PIL.Image的copy()方法创建副本
                    self.img = self.manager.screenshot_cache.copy()
                else:
                    # 缓存为空，返回None
                    self.img = None
            return self.img
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            退出上下文，减少引用计数
            
            线程安全操作：
            - 获取锁保护引用计数
            - 减少引用计数
            - 允许缓存被释放（如果引用计数为0）
            
            :param exc_type: 异常类型
            :param exc_val: 异常值
            :param exc_tb: 异常追踪信息
            """
            with self.manager._screenshot_lock:
                self.manager._cache_in_use -= 1