# System Patterns

## 架构设计
- 设备管理（DeviceManager）与截图、OCR、自动化操作解耦，单一职责。
- 截图、图片处理均基于 PIL，便于后续集成 OCR、UI 测试等。
- 工具脚本（如 screenshot_util.py）通过核心模块调用，保证一致性。

## 关键技术决策
- 设备连接优先级：device_id > adb_address > 配置文件。
- 截图采用 uiautomator2 + OpenCV 转 PIL，兼容性强。
- 打包采用 PyInstaller，spec 文件自动收集 DLL。
- 日志采用 loguru，异常处理全链路覆盖。 