import sys
import os
from src.core.device_manager import DeviceManager

# 示例参数（可根据实际需求修改）
adb_addr = '127.0.0.1:5555'  # 模拟器/设备的ADB地址
x1, y1, x2, y2 = 100, 200, 400, 600  # 截图区域坐标
save_path = 'output/crop.png'  # 图片保存路径

def screenshot_and_save(adb_addr, x1, y1, x2, y2, save_path):
    """
    连接设备，截图指定区域并保存
    :param adb_addr: 设备ADB地址
    :param x1, y1, x2, y2: 截图区域坐标
    :param save_path: 保存路径
    """
    dm = DeviceManager(adb_address=adb_addr)
    if not dm.connect_device():
        print(f"[ERROR] Failed to connect to device: {adb_addr}")
        return
    img = dm.get_screenshot_region(x1, y1, x2, y2)
    if img is None:
        print("[ERROR] Failed to get screenshot region.")
        return
    dm.save_image(img, save_path)
    print(f"[INFO] Cropped screenshot saved to {save_path}")

if __name__ == '__main__':
    # 直接运行脚本时的示例调用
    screenshot_and_save(adb_addr, x1, y1, x2, y2, save_path) 