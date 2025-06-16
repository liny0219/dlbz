import os
import yaml
from pydantic import BaseModel
from utils.get_asset_path import get_asset_path
from typing import Dict, List, TypedDict, Optional, Union
import logging

# 兼容旧接口，返回config目录绝对路径
def get_config_dir():
    return get_asset_path('config')

class OCRConfig(BaseModel):
    lang: str = "ch"
    use_angle_cls: bool = True

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
    find_point_wait_time: float = 1.5
    wait_start_time: float = 0.8
    default_battle_config: str = ""
    vip_cure: bool = False  # 月卡恢复
    revive_on_all_dead: bool = False  # 全灭是否复活

class ItemPos(BaseModel):
    pos: List[int]
    backup_pos: List[int]

class CheckPoint(BaseModel):
    id: int
    pos: List[int]
    reset_map: bool
    next_point: bool
    item_pos: List[ItemPos]

class Monster(BaseModel):
    name: str
    battle_config: str

class CityConfig(TypedDict):
    inn_pos: List[int]
    entrance_pos: List[int]
    check_points: List[CheckPoint]
    monsters: List[Monster]
    monster_pos: List[tuple[int, int]]

class FengmoCityConfig(BaseModel):
    cities: Dict[str, CityConfig]

class NoMillisecFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        from datetime import datetime
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.fromtimestamp(record.created).strftime(datefmt)
        else:
            s = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        return s

class BattleConfig(BaseModel):
    """
    战斗配置类
    管理战斗相关的时间参数和行为设置
    """
    wait_time: float = 0.1  # 基础等待时间
    drag_press_time: float = 0.1  # 拖拽按下等待时间
    drag_release_time: float = 0.1  # 拖拽松开等待时间
    drag_wait_time: float = 0.4  # 拖拽操作等待时间
    wait_ui_time: float = 0.2  # UI响应等待时间
    recognition_time: float = 2.0  # 识别时间
    
    # 战斗相关timeout配置
    auto_battle_timeout: float = 10.0  # 自动战斗超时时间
    check_dead_timeout: float = 1.0  # 检查死亡超时时间
    reset_round_timeout: float = 10.0  # 重置回合超时时间
    exit_battle_timeout: float = 20.0  # 退出战斗超时时间
    transform_timeout: float = 15.0  # 切换形态超时时间
    cast_sp_timeout: float = 10.0  # 释放SP技能超时时间
    cast_skill_timeout: float = 10.0  # 释放技能超时时间
    attack_timeout: float = 5.0  # 攻击超时时间
    wait_in_round_timeout: float = 10.0  # 等待回合超时时间
    wait_done_timeout: float = 90.0  # 等待战斗结束超时时间
    boost_timeout: float = 15.0  # 全体加成超时时间
    switch_all_timeout: float = 5.0  # 全员交替超时时间

class Config:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = get_config_dir()
        self.ocr = OCRConfig(**self._load_yaml_with_log(os.path.join(config_dir, "ocr.yaml"), name="ocr.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="ocr"))
        self.device = DeviceConfig(**self._load_yaml_with_log(os.path.join(config_dir, "device.yaml"), name="device.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="device"))
        self.game = GameConfig(**self._load_yaml_with_log(os.path.join(config_dir, "game.yaml"), name="game.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="game"))
        self.logging = LoggingConfig(**self._load_yaml_with_log(os.path.join(config_dir, "logging.yaml"), name="logging.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="logging"))
        self.command_interval = self._load_yaml_with_log(os.path.join(config_dir, "battle.yaml"), name="battle.yaml").get("command_interval", 1.0)
        self.fengmo = FengmoConfig(**self._load_yaml_with_log(os.path.join(config_dir, "fengmo.yaml"), name="fengmo.yaml"))
        self.fengmo_cities = FengmoCityConfig(**self._load_yaml_with_log(os.path.join(config_dir, "fengmo_cities.yaml"), name="fengmo_cities.yaml")).cities
        self.battle = BattleConfig(**self._load_yaml_with_log(os.path.join(config_dir, "battle.yaml"), name="battle.yaml"))

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

    @staticmethod
    def get_logging_format_and_datefmt(log_format: str, datefmt: Optional[str] = None):
        """
        兼容loguru风格日志format，自动转换为logging风格，并提取datefmt。
        优先使用配置文件中的datefmt字段。
        返回(logging_format, datefmt)
        """
        import re
        # 优先用外部传入的datefmt
        if datefmt:
            # 只做format转换，不再从format中提取datefmt
            log_format = log_format.replace('{time}', '%(asctime)s')
            log_format = (log_format
                .replace('{level}', '%(levelname)s')
                .replace('{message}', '%(message)s')
                .replace('{name}', '%(name)s')
                .replace('{process}', '%(process)d')
                .replace('{thread}', '%(thread)d')
            )
            return log_format, datefmt
        # 兼容loguru风格{time:...}
        datefmt_auto = None
        match = re.search(r'\{time:(.*?)\}', log_format)
        if match:
            datefmt_auto = match.group(1)
            log_format = log_format.replace(match.group(0), '%(asctime)s')
        else:
            log_format = log_format.replace('{time}', '%(asctime)s')
        log_format = (log_format
            .replace('{level}', '%(levelname)s')
            .replace('{message}', '%(message)s')
            .replace('{name}', '%(name)s')
            .replace('{process}', '%(process)d')
            .replace('{thread}', '%(thread)d')
        )
        return log_format, datefmt_auto

    @staticmethod
    def get_no_millisec_formatter(log_format: str, datefmt: Optional[str] = None):
        return NoMillisecFormatter(log_format, datefmt=datefmt) if datefmt else NoMillisecFormatter(log_format)

config = Config() 