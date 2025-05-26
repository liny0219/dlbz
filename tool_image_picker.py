import cv2
import numpy as np
from src.core.device_manager import DeviceManager

class ImagePicker:
    """
    工具类：用于显示图片，支持鼠标点击选取像素坐标和RGB值。
    用法：
        picker = ImagePicker('your_image_path.png')
        picker.show()
    """

    def __init__(self, image_path):
        """
        初始化，加载图片
        :param image_path: 图片文件路径
        """
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise FileNotFoundError(f"图片文件未找到: {image_path}")
        self.clone = self.image.copy()
        self.window_name = "Image Picker"
        self.clicks = []  # 存储点击的坐标和RGB

    def mouse_callback(self, event, x, y, flags, param):
        """
        鼠标回调函数，处理点击事件
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            # 获取像素RGB值（注意OpenCV为BGR顺序）
            b, g, r = self.image[y, x]
            rgb = (int(r), int(g), int(b))
            self.clicks.append((x, y, rgb))
            print(f"点击坐标: ({x}, {y}), RGB: {rgb}")
            # 在图片上画圈和文字
            cv2.circle(self.clone, (x, y), 5, (0, 0, 255), -1)
            text = f"{x},{y} RGB:{rgb}"
            cv2.putText(self.clone, text, (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
            cv2.imshow(self.window_name, self.clone)

    def show(self):
        """
        显示图片并等待用户点击，按q退出
        """
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        cv2.imshow(self.window_name, self.clone)
        print("请在图片窗口点击，按q键退出。")
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        cv2.destroyAllWindows()
        print("所有点击记录：")
        for idx, (x, y, rgb) in enumerate(self.clicks):
            print(f"{idx+1}: 坐标=({x},{y}), RGB={rgb}")
        return self.clicks

def screenshot_and_show(adb_addr, save_path):
    """
    连接设备，截图全屏并保存，然后用ImagePicker展示
    :param adb_addr: 设备ADB地址
    :param save_path: 保存路径
    """
    dm = DeviceManager()
    if not dm.connect_device():
        print(f"[ERROR] Failed to connect to device: {adb_addr}")
        return
    img = dm.get_screenshot()  # 获取全屏截图
    if img is None:
        print("[ERROR] Failed to get screenshot.")
        return
    # 类型兼容处理
    if 'PIL' in str(type(img)):
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    elif not isinstance(img, np.ndarray):
        print(f"[ERROR] 截图类型不支持: {type(img)}")
        return
    cv2.imwrite(save_path, img)
    print(f"[INFO] Screenshot saved to {save_path}")
    picker = ImagePicker(save_path)
    picker.show()

if __name__ == "__main__":
    adb_addr = '127.0.0.1:5555'  # 可根据实际情况修改
    screenshot_path = "screenshot.png"
    screenshot_and_show(adb_addr, screenshot_path) 