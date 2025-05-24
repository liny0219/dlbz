from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from core.game_controller import GameController
from utils.logger import setup_logger
from modes.fengmo import FengmoMode
import time
import traceback

def main():
    # 设置日志
    logger = setup_logger()
    
    try:
        # 初始化设备管理器
        logger.info("Initializing device manager...")
        device_manager = DeviceManager()
        
        # 连接设备
        if not device_manager.connect_device():
            logger.error("Failed to connect device")
            return
        
        # 初始化OCR处理器
        logger.info("Initializing OCR handler...")
        ocr_handler = OCRHandler(device_manager)
        
        # 初始化游戏控制器
        logger.info("Initializing game controller...")
        game_controller = GameController(device_manager, ocr_handler)
        
        # 初始化并运行逢魔玩法模块
        logger.info("启动逢魔玩法模块 FengmoMode ...")
        fengmo_mode = FengmoMode(device_manager, ocr_handler)
        fengmo_mode.run()
        
    except Exception as e:
        print("\n[程序发生异常]")
        traceback.print_exc()
        input("\n按回车键退出...")
        return
    input("\n程序执行完毕，按回车键退出...")

if __name__ == "__main__":
    main() 