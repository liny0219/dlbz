from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from core.game_controller import GameController
from utils.logger import setup_logger
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
        ocr_handler = OCRHandler()
        
        # 初始化游戏控制器
        logger.info("Initializing game controller...")
        game_controller = GameController(device_manager, ocr_handler)
        
        # Demo操作示例
        logger.info("Starting demo operations...")
        
        # 示例1：查找并点击文字
        game_controller.find_and_click_text("歧路旅人")
        time.sleep(2)
        
        # 示例3：OCR识别当前屏幕
        screenshot = device_manager.get_screenshot()
        if screenshot is not None:
            screenshot.save("debug_screenshot.png")  # 保存截图到本地
            results = ocr_handler.recognize_text(screenshot)
            logger.info("OCR Results:")
            for result in results:
                logger.info(f"Text: {result['text']}, Confidence: {result['confidence']:.2f}")
        else:
            print("截图失败，未获取到图片")
        
    except Exception as e:
        print("\n[程序发生异常]")
        traceback.print_exc()
        input("\n按回车键退出...")
        return
    input("\n程序执行完毕，按回车键退出...")

if __name__ == "__main__":
    main() 