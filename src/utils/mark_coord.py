import cv2
import numpy as np
from core.device_manager import DeviceManager
from utils import logger

def mark_coord():
    """
    标记坐标工具函数：
    - 自动连接设备，获取截图
    - 弹出窗口，点击后输出坐标和颜色到控制台
    - ESC 关闭窗口
    """
    logger.debug("[mark_coord] 正在连接设备...")
    device_manager = DeviceManager()
    if not device_manager.connect_device():
        logger.debug("[mark_coord] 设备未连接，无法标记坐标")
        return
    img = device_manager.get_screenshot()
    if img is None:
        logger.debug("[mark_coord] 无法获取设备截图，无法标记坐标")
        return
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    wnd = "ClickWnd"
    logger.debug("[mark_coord] 请在弹出窗口点击需要标记的坐标，ESC关闭窗口")
    def on_EVENT_LBUTTONDOWN(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            b, g, r = img_cv[y, x, :]
            # 十六进制的RGB
            rgb_hex = f"#{r:02X}{g:02X}{b:02X}"
            msg = [x, y, rgb_hex, 50]
            logger.info(f"标记坐标:\n{msg}, [{r}, {g}, {b}])")
            cv2.putText(img_cv, f"({x},{y})", (x, y), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
            cv2.imshow(wnd, img_cv)
    cv2.namedWindow(wnd, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(wnd, on_EVENT_LBUTTONDOWN)
    cv2.imshow(wnd, img_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows() 