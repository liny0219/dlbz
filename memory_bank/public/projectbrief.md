# Project Brief

## 项目目标
开发一个可打包为 exe 的 Python 工具，支持 Android 游戏自动化，具备 OCR（PaddleOCR）、自动化操作（uiautomator2）、OpenCV 能力，能在 Windows 上独立运行。

## 核心需求
- 支持通过配置或参数指定 adb 端口（如 127.0.0.1:5555）连接安卓设备/模拟器。
- 支持全屏与区域截图，图片处理基于 PIL。
- 支持 OCR 识别、自动化点击、滑动等操作。
- 所有功能均可自动化调用，便于集成和扩展。
- 打包后 exe 需自动收集所有依赖 DLL，保证即点即用。

## 主要依赖
- uiautomator2
- paddlepaddle
- paddleocr
- opencv-python
- pillow
- pyyaml
- loguru

## 打包与自动化
- 统一 build.py 脚本自动打包、资源整理。
- spec 文件自动收集 paddle/libs 下所有 DLL。
- 配置文件自动复制到 dist/config。
- 支持无控制台和调试模式切换。 