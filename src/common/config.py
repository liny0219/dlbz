from calendar import c
import os
import sys
import yaml
from pydantic import BaseModel
import logging
from utils.get_asset_path import get_asset_path

# 兼容旧接口，返回config目录绝对路径
def get_config_dir():
    return get_asset_path('config')

class OCRConfig(BaseModel):
    lang: str = "ch"
    use_angle_cls: bool = True
    threshold: float = 0.5

class DeviceConfig(BaseModel):
    connection_timeout: int = 30
    retry_count: int = 3
    adb_address: str = "127.0.0.1:5555"

class GameConfig(BaseModel):
    package_name: str = "com.netease.ma167"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "{time} {level} {message}"

class FengmoConfig(BaseModel):
    depth: int = 1
    rest_in_inn: bool = True
    city: str = "newdelsta"

class Config:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = get_config_dir()
        self.ocr = OCRConfig(**self._load_yaml_with_log(os.path.join(config_dir, "ocr.yaml"), name="ocr.yaml", fallback=os.path.join(config_dir, "settings.yaml"), key="ocr"))
        self.device = DeviceConfig(**self._load_yaml_with_log(os.path.join(config_dir, "device.yaml"), name="device.yaml", fallback=os.path.join(config_dir, "settings.yaml"), key="device"))
        self.game = GameConfig(**self._load_yaml_with_log(os.path.join(config_dir, "game.yaml"), name="game.yaml", fallback=os.path.join(config_dir, "settings.yaml"), key="game"))
        self.logging = LoggingConfig(**self._load_yaml_with_log(os.path.join(config_dir, "logging.yaml"), name="logging.yaml", fallback=os.path.join(config_dir, "settings.yaml"), key="logging"))
        self.command_interval = self._load_yaml_with_log(os.path.join(config_dir, "settings.yaml"), name="settings.yaml").get("command_interval", 1.0)
        # 兼容fengmo等其他配置
        self.fengmo = FengmoConfig(**self._load_yaml_with_log(os.path.join(config_dir, "fengmo.yaml"), name="fengmo.yaml"))
        self.fengmo_cities = self._load_yaml_with_log(os.path.join(config_dir, "fengmo_cities.yaml"), name="fengmo_cities.yaml")

    def _load_yaml_with_log(self, path, name=None, fallback=None, key=None):
        print(f"[Config] 加载配置文件: {name or path}")
        print(f"[Config] 路径: {path}")
        if os.path.exists(path):
            print(f"[Config] 文件存在，开始读取...")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"[Config] 文件内容:\n{content}")
                try:
                    data = yaml.safe_load(content) or {}
                    print(f"[Config] 解析结果: {data}")
                    return data
                except Exception as e:
                    print(f"[Config] YAML解析异常: {e}")
                    return {}
        elif fallback and os.path.exists(fallback):
            print(f"[Config] 主文件不存在，尝试回退到: {fallback}")
            with open(fallback, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"[Config] 回退文件内容:\n{content}")
                try:
                    data = yaml.safe_load(content) or {}
                    if key:
                        data = data.get(key, {})
                    print(f"[Config] 回退解析结果: {data}")
                    return data
                except Exception as e:
                    print(f"[Config] 回退YAML解析异常: {e}")
                    return {}
        else:
            print(f"[Config] 文件不存在！")
            return {}

config = Config() 