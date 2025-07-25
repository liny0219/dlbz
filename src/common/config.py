import os
import yaml
from pydantic import BaseModel
from utils.get_asset_path import get_asset_path
from typing import Dict, List, TypedDict, Optional, Union
import logging
import time
from utils import logger

# 兼容旧接口，返回config目录绝对路径
def get_config_dir():
    return get_asset_path('config')

# 配置缓存类
class ConfigCache:
    """配置缓存管理器，避免重复读取配置文件"""
    
    def __init__(self, cache_ttl=300, max_cache_size=50):  # 5分钟缓存时间，最大50个文件
        self._cache = {}
        self._cache_times = {}
        self._cache_ttl = cache_ttl
        self._max_cache_size = max_cache_size
    
    def get(self, file_path: str) -> Optional[Dict]:
        """获取缓存的配置"""
        if file_path in self._cache:
            # 检查缓存是否过期
            if time.time() - self._cache_times[file_path] < self._cache_ttl:
                return self._cache[file_path]
            else:
                # 缓存过期，删除
                del self._cache[file_path]
                del self._cache_times[file_path]
        return None
    
    def set(self, file_path: str, data: Dict) -> None:
        """设置缓存数据"""
        # 检查缓存大小，如果超过限制，清理更多旧条目
        if len(self._cache) >= self._max_cache_size:
            # 清理一半的缓存条目，而不是只清理一个
            items_to_remove = len(self._cache) // 2
            sorted_items = sorted(self._cache_times.items(), key=lambda x: x[1])
            for i in range(items_to_remove):
                oldest_file = sorted_items[i][0]
                del self._cache[oldest_file]
                del self._cache_times[oldest_file]
            logger.debug(f"配置缓存清理了 {items_to_remove} 个旧条目")
        
        self._cache[file_path] = data
        self._cache_times[file_path] = time.time()
    
    def _evict_oldest(self):
        """淘汰最旧的缓存条目"""
        if not self._cache_times:
            return
        
        # 找到最旧的条目
        oldest_file = min(self._cache_times.keys(), key=lambda k: self._cache_times[k])
        del self._cache[oldest_file]
        del self._cache_times[oldest_file]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._cache_times.clear()
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            'cache_size': len(self._cache),
            'max_cache_size': self._max_cache_size,
            'cache_ttl': self._cache_ttl,
            'cached_files': list(self._cache.keys())
        }

# 全局配置缓存实例
_config_cache = ConfigCache()

class OCRConfig(BaseModel):
    lang: str = "ch"
    use_angle_cls: bool = True
    ocr_confidence_threshold: float = 0.8  # OCR识别置信度阈值
    image_template_match_threshold: float = 0.95  # 图像模板匹配阈值
    debug_mode: bool = False  # 是否开启调试模式

class DeviceConfig(BaseModel):
    connection_timeout: int = 30
    retry_count: int = 3
    adb_address: str = "127.0.0.1:5555"
    app_packages: str = "com.netease.ma167"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "{time} {level} {message}"

class FengmoConfig(BaseModel):
    depth: int = 1
    rest_in_inn: bool = True
    city: str = "newdelsta"
    find_point_wait_time: float = 1.5
    wait_map_time: float = 0.8
    wait_ui_time: float = 0.2  # UI响应等待时间
    difficulty_delay: float = 0.5  # 难度选择延时
    involve_match_threshold: float = 0.8  # 涉入按钮匹配度
    default_battle_config: str = ""
    vip_cure: bool = False  # 月卡恢复

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
    boost_timeout: float = 0.5  # 全体加成超时时间
    switch_all_timeout: float = 5.0  # 全员交替超时时间

class Config:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = get_config_dir()
        # 兼容旧字段
        ocr_raw = self._load_yaml_with_log(os.path.join(config_dir, "recognition_config.yaml"), name="recognition_config.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="ocr")
        # 字段兼容处理
        if "ocr_confidence_threshold" not in ocr_raw and "confidence_threshold" in ocr_raw:
            ocr_raw["ocr_confidence_threshold"] = ocr_raw["confidence_threshold"]
        if "image_template_match_threshold" not in ocr_raw and "image_match_threshold" in ocr_raw:
            ocr_raw["image_template_match_threshold"] = ocr_raw["image_match_threshold"]
        if "debug_mode" not in ocr_raw:
            ocr_raw["debug_mode"] = ocr_raw.get("ocr_debug", False)
        self.ocr = OCRConfig(**ocr_raw)
        self.device = DeviceConfig(**self._load_yaml_with_log(os.path.join(config_dir, "device.yaml"), name="device.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="device"))
        self.logging = LoggingConfig(**self._load_yaml_with_log(os.path.join(config_dir, "logging.yaml"), name="logging.yaml", fallback=os.path.join(config_dir, "battle.yaml"), key="logging"))
        self.command_interval = self._load_yaml_with_log(os.path.join(config_dir, "battle.yaml"), name="battle.yaml").get("command_interval", 1.0)
        self.fengmo = FengmoConfig(**self._load_yaml_with_log(os.path.join(config_dir, "fengmo.yaml"), name="fengmo.yaml"))
        self.fengmo_cities = FengmoCityConfig(**self._load_yaml_with_log(os.path.join(config_dir, "fengmo_cities.yaml"), name="fengmo_cities.yaml")).cities
        self.battle = BattleConfig(**self._load_yaml_with_log(os.path.join(config_dir, "battle.yaml"), name="battle.yaml"))

    def _load_yaml_with_log(self, path, name=None, fallback=None, key=None):
        # 首先尝试从缓存获取
        cached_data = _config_cache.get(path)
        if cached_data is not None:
            print(f"[Config] 从缓存加载配置: {name or path}")
            if key:
                return cached_data.get(key, {})
            return cached_data
        
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
                    # 缓存结果
                    _config_cache.set(path, data)
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
                    # 缓存结果
                    _config_cache.set(fallback, data)
                    return data
                except Exception as e:
                    print(f"[Config] 回退YAML解析异常: {e}")
                    return {}
        else:
            print(f"[Config] 文件不存在！")
            return {}

    @staticmethod
    def clear_cache():
        """清空配置缓存"""
        _config_cache.clear()
        print("[Config] 配置缓存已清空")

    @staticmethod
    def get_cache_info():
        """获取缓存信息"""
        return _config_cache.get_cache_info()

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