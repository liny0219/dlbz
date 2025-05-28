from utils import logger
import numpy as np
import time
from typing import Any
import traceback

class GameController:
    def __init__(self, device_manager: Any, ocr_handler: Any) -> None:
        self.device_manager = device_manager
        self.ocr_handler = ocr_handler
        self.device = device_manager.device
    
    def swipe(self, fx: int, fy: int, tx: int, ty: int, duration: float = 0.1) -> bool:
        """滑动操作"""
        try:
            self.device.swipe(fx, fy, tx, ty, duration=duration)
            logger.info(f"Swiped from ({fx}, {fy}) to ({tx}, {ty})")
            return True
        except Exception as e:
            logger.error(f"Swipe operation failed: {str(e)}\n{traceback.format_exc()}")
            return False 