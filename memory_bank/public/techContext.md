# Tech Context

## 技术栈
- Python 3.x
- uiautomator2
- paddlepaddle
- paddleocr
- opencv-python
- pillow
- pyyaml
- loguru

## 依赖管理
- requirements.txt 统一管理依赖。
- build.py 脚本自动化打包。
- spec 文件自动收集 paddle/libs DLL。

## 开发与打包约束
- 代码需兼容 Windows 平台。
- 打包后 dist 目录下需包含所有运行所需 DLL。
- 配置文件与资源自动同步。 