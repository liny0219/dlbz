# Active Context

## 当前工作焦点
- 设备连接与截图功能的专业化、解耦与接口标准化。
- 项目级截图工具脚本的实现与集成。

## 近期变更
- DeviceManager 支持 adb_address 参数，截图返回 PIL.Image。
- 新增 get_screenshot_region、save_image 方法。
- 根目录新增 screenshot_util.py，调用核心模块实现截图。

## 下一步计划
- 支持批量截图、自动命名等高级功能。
- 完善配置文件参数化与多设备支持。 