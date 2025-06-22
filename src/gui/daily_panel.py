import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import multiprocessing
import datetime
import time
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type
import yaml
import logging
import os
import traceback
import time
from common.config import config
from utils.logger import get_log_file_path
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler

class DailyPanel(ttk.Frame):
    """
    日常功能面板
    统一的日常玩法，包含花田与果炎功能
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config_file = "daily.yaml"
        
        # 进程管理
        self.daily_process = None
        self.log_queue = None
        
        # 分别统计花田和果炎的数据
        self.huatian_stats = {
            "huatian1": {
                "restart_count": 0,  # 重启次数
                "total_time": 0.0,   # 总耗时（秒）
                "target_found": False,  # 是否找到目标
            },
            "huatian2": {
                "restart_count": 0,  # 重启次数
                "total_time": 0.0,   # 总耗时（秒）
                "target_found": False,  # 是否找到目标
            }
        }
        
        self.guoyan_stats = {
            "restart_count": 0,  # 重启次数
            "total_time": 0.0,   # 总耗时（秒）
            "target_found": False,  # 是否找到目标
        }
        
        self.load_config()
        self._build_widgets()

    def load_config(self):
        """加载日常配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 默认配置
        self.config_data = {
            "huatian": {
                "enabled": True,
                "huatian1_enabled": True,
                "huatian2_enabled": True,
                "target_count": 10
            },
            "guoyan": {
                "enabled": True,
                "target_count": 10
            }
        }
        
        # 如果配置文件存在，加载配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    self.config_data.update(loaded_config)
                    
                    # 确保所有必要的键存在
                    for section in ["huatian", "guoyan"]:
                        if section not in self.config_data:
                            self.config_data[section] = {}
                        
                        # 花田配置的默认值
                        if section == "huatian":
                            huatian_defaults = {
                                "enabled": True,
                                "huatian1_enabled": True,
                                "huatian2_enabled": True,
                                "target_count": 10
                            }
                            for key, default_value in huatian_defaults.items():
                                if key not in self.config_data[section]:
                                    self.config_data[section][key] = default_value
                        
                        # 果炎配置的默认值
                        elif section == "guoyan":
                            guoyan_defaults = {
                                "enabled": True,
                                "target_count": 10
                            }
                            for key, default_value in guoyan_defaults.items():
                                if key not in self.config_data[section]:
                                    self.config_data[section][key] = default_value
                            
            except Exception as e:
                print(f"加载日常配置失败: {e}")

    def save_config(self):
        """保存日常配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 更新配置数据
        self.config_data["huatian"]["enabled"] = self.huatian_enabled_var.get()
        self.config_data["huatian"]["huatian1_enabled"] = self.huatian1_enabled_var.get()
        self.config_data["huatian"]["huatian2_enabled"] = self.huatian2_enabled_var.get()
        self.config_data["huatian"]["target_count"] = self.huatian_target_var.get()
        
        self.config_data["guoyan"]["enabled"] = self.guoyan_enabled_var.get()
        self.config_data["guoyan"]["target_count"] = self.guoyan_target_var.get()
        
        try:
            save_yaml_with_type(config_path, self.config_data)
            self.log_status("配置已保存到文件")
        except Exception as e:
            print(f"保存配置失败: {e}")
            self.log_status(f"保存配置失败: {e}")

    def _build_widgets(self):
        """构建界面组件"""
        # 日常配置区域
        config_frame = ttk.LabelFrame(self, text="日常配置", padding=(10, 10))
        config_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        # 配置区域主框架 - 使用grid布局将花田和果炎放在同一行
        config_main_frame = ttk.Frame(config_frame)
        config_main_frame.pack(fill=tk.X, pady=(0, 10))
        config_main_frame.columnconfigure(0, weight=1)  # 花田配置区域
        config_main_frame.columnconfigure(1, weight=1)  # 果炎配置区域

        # 花田配置区域
        huatian_main_frame = ttk.LabelFrame(config_main_frame, text="花田配置", padding=(5, 5))
        huatian_main_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 花田启用选项
        huatian_enabled_frame = ttk.Frame(huatian_main_frame)
        huatian_enabled_frame.pack(fill=tk.X, pady=2)
        
        self.huatian_enabled_var = tk.BooleanVar(value=self.config_data["huatian"]["enabled"])
        huatian_check = ttk.Checkbutton(huatian_enabled_frame, text="启用花田", variable=self.huatian_enabled_var)
        huatian_check.pack(side=tk.LEFT)

        # 花田1和花田2选项
        huatian_sub_frame = ttk.Frame(huatian_main_frame)
        huatian_sub_frame.pack(fill=tk.X, pady=2)
        
        # 添加缩进
        ttk.Label(huatian_sub_frame, text="    ", width=3).pack(side=tk.LEFT)
        
        self.huatian1_enabled_var = tk.BooleanVar(value=self.config_data["huatian"]["huatian1_enabled"])
        huatian1_check = ttk.Checkbutton(huatian_sub_frame, text="花田1", variable=self.huatian1_enabled_var)
        huatian1_check.pack(side=tk.LEFT, padx=(0, 20))
        
        self.huatian2_enabled_var = tk.BooleanVar(value=self.config_data["huatian"]["huatian2_enabled"])
        huatian2_check = ttk.Checkbutton(huatian_sub_frame, text="花田2", variable=self.huatian2_enabled_var)
        huatian2_check.pack(side=tk.LEFT)

        # 花田目标数量
        huatian_target_frame = ttk.Frame(huatian_main_frame)
        huatian_target_frame.pack(fill=tk.X, pady=2)
        
        # 添加缩进
        ttk.Label(huatian_target_frame, text="    ", width=3).pack(side=tk.LEFT)
        
        ttk.Label(huatian_target_frame, text="目标数量:", width=8, anchor="w").pack(side=tk.LEFT)
        
        self.huatian_target_var = tk.IntVar(value=self.config_data["huatian"]["target_count"])
        huatian_target_spin = tk.Spinbox(huatian_target_frame, from_=1, to=999, increment=1, 
                                        textvariable=self.huatian_target_var, width=8)
        huatian_target_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(huatian_target_frame, text="个(基础值的最大3倍)", anchor="w").pack(side=tk.LEFT, padx=(2, 0))

        # 果炎配置区域
        guoyan_main_frame = ttk.LabelFrame(config_main_frame, text="果炎配置", padding=(5, 5))
        guoyan_main_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # 果炎启用选项
        guoyan_enabled_frame = ttk.Frame(guoyan_main_frame)
        guoyan_enabled_frame.pack(fill=tk.X, pady=2)
        
        self.guoyan_enabled_var = tk.BooleanVar(value=self.config_data["guoyan"]["enabled"])
        guoyan_check = ttk.Checkbutton(guoyan_enabled_frame, text="启用果炎", variable=self.guoyan_enabled_var)
        guoyan_check.pack(side=tk.LEFT)

        # 果炎目标数量
        guoyan_target_frame = ttk.Frame(guoyan_main_frame)
        guoyan_target_frame.pack(fill=tk.X, pady=2)
        
        # 添加缩进
        ttk.Label(guoyan_target_frame, text="    ", width=3).pack(side=tk.LEFT)
        
        ttk.Label(guoyan_target_frame, text="目标数量:", width=8, anchor="w").pack(side=tk.LEFT)
        
        self.guoyan_target_var = tk.IntVar(value=self.config_data["guoyan"]["target_count"])
        guoyan_target_spin = tk.Spinbox(guoyan_target_frame, from_=1, to=999, increment=1, 
                                       textvariable=self.guoyan_target_var, width=8)
        guoyan_target_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(guoyan_target_frame, text="个(最大100)", anchor="w").pack(side=tk.LEFT, padx=(2, 0))

        # 按钮区域
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=(10, 5))

        # 开始日常按钮
        self.start_daily_btn = ttk.Button(button_frame, text="开始日常", 
                                         command=self.start_daily, style="Accent.TButton")
        self.start_daily_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止日常按钮
        self.stop_daily_btn = ttk.Button(button_frame, text="停止日常", 
                                        command=self.stop_daily, state=tk.DISABLED)
        self.stop_daily_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存配置按钮
        save_config_btn = ttk.Button(button_frame, text="保存配置", 
                                    command=self.save_config)
        save_config_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 重置统计按钮
        reset_stats_btn = ttk.Button(button_frame, text="重置统计", 
                                    command=self.reset_stats)
        reset_stats_btn.pack(side=tk.LEFT)

        # 统计信息展示区域
        stats_frame = ttk.LabelFrame(self, text="日常统计", padding=(10, 10))
        stats_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.stats_text = tk.Text(stats_frame, height=3, width=80, font=("Consolas", 11), state='disabled')
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # 状态区域
        status_frame = ttk.LabelFrame(self, text="运行日志", padding=(10, 10))
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))

        self.status_text = tk.Text(status_frame, height=15, width=80, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 初始化统计和状态信息
        self.update_stats()
        self.log_status("日常面板已初始化")
        self.log_status("请选择要启用的日常功能，然后点击开始日常")

    def start_daily(self):
        """开始日常玩法"""
        # 检查是否至少启用了一个功能
        huatian_any_enabled = (self.huatian_enabled_var.get() and 
                              (self.huatian1_enabled_var.get() or self.huatian2_enabled_var.get()))
        guoyan_enabled = self.guoyan_enabled_var.get()
        
        if not huatian_any_enabled and not guoyan_enabled:
            messagebox.showwarning("提示", "请至少启用一个日常功能！")
            return
            
        if self.daily_process and self.daily_process.is_alive():
            messagebox.showwarning("提示", "日常玩法已在运行中！")
            return
        
        # 自动保存配置
        self.save_config()
        
        self.log_status("=" * 50)
        self.log_status("日常玩法进程启动中...")
        
        enabled_features = []
        if huatian_any_enabled:
            huatian_details = []
            if self.huatian1_enabled_var.get():
                huatian_details.append("花田1")
            if self.huatian2_enabled_var.get():
                huatian_details.append("花田2")
            enabled_features.append(f"花田({'+'.join(huatian_details)}, 目标:{self.huatian_target_var.get()}个)")
        if guoyan_enabled:
            enabled_features.append(f"果炎(目标:{self.guoyan_target_var.get()}个)")
        
        self.log_status(f"启用的功能: {', '.join(enabled_features)}")
        
        # 更新按钮状态
        self._set_daily_running_state()
        
        # 创建日志队列和启动进程
        self.log_queue = multiprocessing.Queue()
        log_level = getattr(self.parent, 'log_level_var', tk.StringVar(value="INFO")).get()
        
        # 传递配置参数
        config_params = {
            "huatian_enabled": self.huatian_enabled_var.get(),
            "huatian1_enabled": self.huatian1_enabled_var.get(),
            "huatian2_enabled": self.huatian2_enabled_var.get(),
            "huatian_target_count": self.huatian_target_var.get(),
            "guoyan_enabled": self.guoyan_enabled_var.get(),
            "guoyan_target_count": self.guoyan_target_var.get()
        }
        
        self.daily_process = multiprocessing.Process(
            target=run_daily_main,
            args=(config_params, self.log_queue, log_level)
        )
        self.daily_process.start()
        
        # 开始轮询日志队列
        self.after(100, self.poll_daily_log_queue)

    def poll_daily_log_queue(self):
        """轮询日常日志队列"""
        try:
            if self.log_queue:
                while True:
                    try:
                        msg = self.log_queue.get_nowait()
                        if msg.startswith("STATS_UPDATE__"):
                            # 处理统计数据更新
                            self._handle_stats_update(msg)
                        else:
                            self.log_status(msg)
                    except Exception:
                        break
            
            # 如果进程还在运行，继续轮询
            if self.daily_process and self.daily_process.is_alive():
                self.after(100, self.poll_daily_log_queue)
            else:
                # 进程结束，清理状态
                self.log_status("日常玩法进程已结束")
                self._cleanup_daily()
        except Exception:
            self.log_status("日常玩法日志队列已关闭")

    def stop_daily(self):
        """停止日常玩法"""
        if not self.daily_process or not self.daily_process.is_alive():
            self.log_status("日常玩法未在运行")
            self._cleanup_daily()
            return
            
        self.log_status("用户请求停止日常玩法")
        
        # 强制终止进程
        self.daily_process.terminate()
        self.daily_process.join()
        
        self.log_status("日常玩法进程已终止")
        self._cleanup_daily()

    def _set_daily_running_state(self):
        """设置日常运行状态"""
        self.start_daily_btn.config(state=tk.DISABLED)
        self.stop_daily_btn.config(state=tk.NORMAL)

    def _set_idle_state(self):
        """设置空闲状态"""
        self.start_daily_btn.config(state=tk.NORMAL)
        self.stop_daily_btn.config(state=tk.DISABLED)

    def _cleanup_daily(self):
        """清理日常状态"""
        self.daily_process = None
        self._set_idle_state()

    def _handle_stats_update(self, msg):
        """处理统计数据更新消息"""
        try:
            # 消息格式: STATS_UPDATE__type:huatian1,time:12.5,restart_count:3,target_found:true
            stats_data = msg[len("STATS_UPDATE__"):]
            
            # 解析统计数据
            stats_info = {}
            for item in stats_data.split(","):
                if ":" in item:
                    key, value = item.split(":", 1)
                    stats_info[key] = value
            
            activity_type = stats_info.get("type", "")
            elapsed_time = float(stats_info.get("time", "0"))
            restart_count = int(stats_info.get("restart_count", "0"))
            target_found = stats_info.get("target_found", "false").lower() == "true"
            
            if activity_type in ["huatian1", "huatian2"]:
                self.update_huatian_stats(activity_type, elapsed_time=elapsed_time, restart_count=restart_count, target_found=target_found)
            elif activity_type == "guoyan":
                self.update_guoyan_stats(elapsed_time=elapsed_time, restart_count=restart_count, target_found=target_found)
                
        except Exception as e:
            self.log_status(f"处理统计更新失败: {e}")

    def update_huatian_stats(self, huatian_type, elapsed_time=0.0, restart_count=None, target_found=None):
        """更新花田统计数据"""
        if huatian_type in self.huatian_stats:
            if restart_count is not None:
                self.huatian_stats[huatian_type]["restart_count"] = restart_count
            if elapsed_time > 0:
                self.huatian_stats[huatian_type]["total_time"] = elapsed_time  # 直接赋值，不累加
            if target_found is not None:
                self.huatian_stats[huatian_type]["target_found"] = target_found
        
        self.update_stats()

    def update_guoyan_stats(self, elapsed_time=0.0, restart_count=None, target_found=None):
        """更新果炎统计数据"""
        if restart_count is not None:
            self.guoyan_stats["restart_count"] = restart_count
        if elapsed_time > 0:
            self.guoyan_stats["total_time"] = elapsed_time  # 直接赋值，不累加
        if target_found is not None:
            self.guoyan_stats["target_found"] = target_found
        
        self.update_stats()

    def increment_huatian_stats(self, elapsed_time=0.0):
        """增加花田统计数据（保持向后兼容）"""
        # 为了向后兼容，默认更新花田1
        self.update_huatian_stats("huatian1", elapsed_time=elapsed_time)

    def increment_guoyan_stats(self, elapsed_time=0.0):
        """增加果炎统计数据（保持向后兼容）"""
        self.update_guoyan_stats(elapsed_time=elapsed_time)

    def reset_stats(self):
        """重置统计数据"""
        if messagebox.askyesno("确认", "确定要重置所有统计数据吗？"):
            self.huatian_stats = {
                "huatian1": {
                    "restart_count": 0,
                    "total_time": 0.0,
                    "target_found": False,
                },
                "huatian2": {
                    "restart_count": 0,
                    "total_time": 0.0,
                    "target_found": False,
                }
            }
            
            self.guoyan_stats = {
                "restart_count": 0,
                "total_time": 0.0,
                "target_found": False,
            }
            
            self.update_stats()
            self.log_status("统计数据已重置")

    def format_time(self, seconds):
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.0f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}时{minutes}分{secs:.0f}秒"

    def log_status(self, message):
        """记录状态信息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, log_line)
        self.status_text.see(tk.END)
        self.status_text.update()

    def update_stats(self):
        """更新统计信息显示"""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        # 直接显示统计数据，不进行实时计算
        huatian1_current_time = self.huatian_stats["huatian1"]["total_time"]
        huatian2_current_time = self.huatian_stats["huatian2"]["total_time"]
        guoyan_current_time = self.guoyan_stats["total_time"]
        
        # 格式化目标找到状态
        huatian1_status = "已找到" if self.huatian_stats["huatian1"]["target_found"] else "未找到"
        huatian2_status = "已找到" if self.huatian_stats["huatian2"]["target_found"] else "未找到"
        guoyan_status = "已找到" if self.guoyan_stats["target_found"] else "未找到"
        
        stats_content = f"""花田1: 重启次数: {self.huatian_stats["huatian1"]["restart_count"]} | 耗时: {self.format_time(huatian1_current_time)} | 目标: {huatian1_status}
花田2: 重启次数: {self.huatian_stats["huatian2"]["restart_count"]} | 耗时: {self.format_time(huatian2_current_time)} | 目标: {huatian2_status}
果炎: 重启次数: {self.guoyan_stats["restart_count"]} | 耗时: {self.format_time(guoyan_current_time)} | 目标: {guoyan_status}
"""
        
        self.stats_text.insert(tk.END, stats_content)
        self.stats_text.config(state='disabled')

# 子进程日志Handler（与memory_panel中的相同）
class QueueLogHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put(msg)
        except Exception:
            pass

def fix_stdio_if_none():
    """修复stdio为None的问题"""
    import sys
    import io
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

def run_daily_main(config_params, log_queue, log_level):
    """
    日常玩法主函数，在子进程中运行
    统一处理花田和果炎功能
    
    :param config_params: 配置参数字典
    :param log_queue: 日志队列，用于向主进程发送日志消息
    :param log_level: 日志级别
    """

    # 注意：这里需要创建一个统一的日常模式类
    # from modes.daily import DailyMode
    fix_stdio_if_none()
    
    # 配置日志系统
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    # 读取配置文件的日志格式
    log_format, datefmt = config.get_logging_format_and_datefmt(
        config.logging.format, 
        getattr(config.logging, 'datefmt', None)
    )
    formatter = config.get_no_millisec_formatter(log_format, datefmt)
    
    # 配置队列handler（发送到主进程GUI）
    queue_handler = QueueLogHandler(log_queue)
    queue_handler.setLevel(logging.NOTSET)
    queue_handler.setFormatter(formatter)
    root_logger.addHandler(queue_handler)
    
    # 配置文件handler（写入本地日志文件）
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = get_log_file_path(logs_dir, "daily")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger.setLevel(level)
    
    logger = logging.getLogger("dldbz")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = True
    
    def send_stats_update(activity_type, elapsed_time):
        """发送统计更新消息"""
        if log_queue:
            try:
                stats_msg = f"STATS_UPDATE__type:{activity_type},time:{elapsed_time:.2f}"
                log_queue.put(stats_msg)
            except Exception as e:
                logger.error(f"发送统计更新失败: {e}")
    
    try:
        logger.info(f"[日常子进程] 日志级别: {log_level}")
        logger.info("日常子进程已启动，等待业务执行...")
        logger.info(f"配置参数: {config_params}")
        
        # 初始化设备管理器
        logger.info("初始化设备管理器...")
        device_manager = DeviceManager()
        if not device_manager.connect_device():
            logger.error("设备连接失败")
            if log_queue:
                log_queue.put("设备连接失败")
            return
        
        # 初始化OCR处理器
        logger.info("初始化OCR处理器...")
        ocr_handler = OCRHandler(device_manager)
        
        # 启动日常模式
        logger.info("启动日常玩法模块 DailyMode ...")
        from modes.daily import DailyMode
        daily_mode = DailyMode(device_manager, ocr_handler, log_queue)
        daily_mode.run(config_params)
        
        logger.info("日常玩法执行完成")
        
    except Exception as e:
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[日常子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}") 