"""
梦境模式界面
提供梦境玩法的独立界面，包含配置选项、启动/停止控制、日志显示和统计信息
"""

import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import os
import datetime
import logging
import sys

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.config import get_config_dir
from utils.process_manager import get_process_manager
from utils.game_mutex_manager import get_game_mutex_manager


class DreamPanel(ttk.Frame):
    """
    梦境模式界面
    """
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config_file = "dream.yaml"
        
        # 初始化进程管理器和游戏互斥管理器
        self.process_manager = get_process_manager()
        self.game_mutex_manager = get_game_mutex_manager()
        
        # 进程相关
        self.dream_process = None
        self.log_queue = None
        
        # 统计信息
        self.reset_dream_stats()
        
        # 加载配置 - 在构建界面之前加载
        self.load_config()
        
        # 构建界面
        self._build_widgets()

    def reset_dream_stats(self):
        """重置梦境统计数据"""
        self.dream_stats = {
            "total_loops": 0,
            "successful_recruits": 0,
            "successful_battles": 0,
            "successful_events": 0,
            "total_awards": 0,  # 总奖励积分
            "total_time": 0.0,
            "current_session_time": 0.0
        }

    def load_config(self):
        """加载梦境配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 默认配置 - 只保留基本配置项
        self.config_data = {
            "enabled": True,
            "max_loops": 10000,
            "loop_delay": 0.1,
            "image_threshold": 0.8,
            "battle_threshold": 0.7,
            "settlement_threshold": 0.6,
            "click_wait_interval": 0.5
        }
        
        # 如果配置文件存在，加载配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    self.config_data.update(loaded_config)
                        
            except Exception as e:
                self.log_status(f"加载梦境配置失败: {e}")

    def save_config(self):
        """保存梦境配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 只保存基本配置项
        config_data = {
            "enabled": self.enabled_var.get(),
            "max_loops": self.max_loops_var.get(),
            "loop_delay": self.loop_delay_var.get(),
            "image_threshold": self.config_data.get("image_threshold", 0.8),
            "battle_threshold": self.config_data.get("battle_threshold", 0.7),
            "settlement_threshold": self.config_data.get("settlement_threshold", 0.6),
            "click_wait_interval": self.click_wait_interval_var.get()
        }
        
        try:
            from utils.yaml_helper import save_yaml_with_type
            save_yaml_with_type(config_path, config_data)
            self.log_status("梦境配置已保存")
        except Exception as e:
            self.log_status(f"保存梦境配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _build_widgets(self):
        """构建界面组件"""
        # 梦境配置区域
        dream_frame = ttk.LabelFrame(self, text="梦境模式配置", padding=(10, 10))
        dream_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        # 梦境说明
        info_frame = ttk.Frame(dream_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="梦境模式需要进入到梦境开始按钮界面,设置战斗为智能模式", 
                 wraplength=400, font=("TkDefaultFont", 9)).pack(pady=5)

        # 配置选项
        config_frame = ttk.Frame(dream_frame)
        config_frame.pack(fill=tk.X, pady=5)
        
        # 启用梦境模式
        self.enabled_var = tk.BooleanVar(value=self.config_data.get("enabled", True))
        enabled_check = ttk.Checkbutton(config_frame, text="启用梦境模式", variable=self.enabled_var)
        enabled_check.pack(side=tk.LEFT, padx=(0, 20))
        
        # 最大循环次数
        ttk.Label(config_frame, text="最大循环次数:").pack(side=tk.LEFT, padx=(0, 5))
        self.max_loops_var = tk.IntVar(value=self.config_data.get("max_loops", 10000))
        max_loops_spin = tk.Spinbox(config_frame, from_=1, to=99999, increment=100, 
                                   textvariable=self.max_loops_var, width=10)
        max_loops_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        # 循环延迟
        ttk.Label(config_frame, text="循环延迟(秒):").pack(side=tk.LEFT, padx=(0, 5))
        self.loop_delay_var = tk.DoubleVar(value=self.config_data.get("loop_delay", 0.1))
        loop_delay_spin = tk.Spinbox(config_frame, from_=0.01, to=1.0, increment=0.01, 
                                    textvariable=self.loop_delay_var, width=8, format="%.2f")
        loop_delay_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        # 点击等待间隔
        ttk.Label(config_frame, text="点击等待间隔(秒):").pack(side=tk.LEFT, padx=(0, 5))
        self.click_wait_interval_var = tk.DoubleVar(value=self.config_data.get("click_wait_interval", 1))
        click_wait_spin = tk.Spinbox(config_frame, from_=0.6, to=2.0, increment=0.1, 
                                    textvariable=self.click_wait_interval_var, width=8, format="%.1f")
        click_wait_spin.pack(side=tk.LEFT)

        # 按钮区域
        button_frame = ttk.Frame(dream_frame)
        button_frame.pack(fill=tk.X, pady=(10, 5))

        # 开始梦境按钮
        self.start_dream_btn = ttk.Button(button_frame, text="开始梦境", 
                                         command=self.start_dream, style="Accent.TButton")
        self.start_dream_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止梦境按钮
        self.stop_dream_btn = ttk.Button(button_frame, text="停止梦境", 
                                        command=self.stop_dream, state=tk.DISABLED)
        self.stop_dream_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存配置按钮
        save_config_btn = ttk.Button(button_frame, text="保存配置", 
                                    command=self.save_config)
        save_config_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 重置统计按钮
        reset_stats_btn = ttk.Button(button_frame, text="重置统计", 
                                    command=self.reset_stats)
        reset_stats_btn.pack(side=tk.LEFT)

        # 统计信息展示区域
        stats_frame = ttk.LabelFrame(self, text="梦境统计", padding=(10, 10))
        stats_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.stats_text = tk.Text(stats_frame, height=6, width=80, font=("Consolas", 11), state='disabled')
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # 状态区域
        status_frame = ttk.LabelFrame(self, text="运行日志", padding=(10, 10))
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))

        self.status_text = tk.Text(status_frame, height=15, width=80, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 初始化统计显示
        self.update_stats()
        self.log_status("梦境模式面板已初始化")
        self.log_status("点击开始梦境即可启动自动化梦境玩法")

    def start_dream(self):
        """开始梦境模式"""
        # 在启动玩法前检查并清理日志目录
        try:
            from utils.logger import cleanup_logs_dir
            cleanup_logs_dir()
        except Exception as e:
            self.log_status(f"清理日志目录失败: {e}")
        
        # 自动保存配置
        self.save_config()
        
        self.log_status("=" * 50)
        self.log_status("梦境模式进程启动中...")
        self.log_status("自动化梦境玩法: 将自动处理开始游戏、招募、丢骰子、战斗等流程")
        
        # 重置统计数据
        self.reset_dream_stats()
        self.update_stats()
        
        # 传递配置参数
        config_params = {
            "enabled": self.enabled_var.get(),
            "max_loops": self.max_loops_var.get(),
            "loop_delay": self.loop_delay_var.get(),
            "image_threshold": self.config_data.get("image_threshold", 0.8),
            "battle_threshold": self.config_data.get("battle_threshold", 0.7),
            "settlement_threshold": self.config_data.get("settlement_threshold", 0.6),
            "click_wait_interval": self.click_wait_interval_var.get()
        }
        
        # 获取日志级别
        log_level = getattr(self.parent, 'log_level_var', tk.StringVar(value="INFO")).get()
        
        # 使用游戏互斥管理器启动
        success, process, queue = self.game_mutex_manager.start_game_safely(
            game_key="dream_process",
            target_func=run_dream_main,
            args=(config_params, None, log_level),  # 先传None，启动后会设置正确的队列
            parent_widget=self.parent,
            log_callback=self.log_status
        )
        
        if success:
            self.dream_process = process
            self.log_queue = queue
            # 更新按钮状态
            self._set_dream_running_state()
            self.log_status("梦境模式进程已启动，正在连接设备...")
            # 开始轮询日志队列
            self.after(100, self.poll_log_queue)
        else:
            self.log_status("梦境模式进程启动失败")

    def poll_log_queue(self):
        """
        轮询日志队列，处理来自子进程的日志和统计数据
        """
        try:
            if self.log_queue:
                while True:
                    try:
                        msg = self.log_queue.get_nowait()
                        if msg.startswith("REPORT_DATA__"):
                            # 处理统计数据更新
                            self.update_report_data(msg[len("REPORT_DATA__"):])
                        else:
                            # 处理普通日志消息
                            self.log_status(msg)
                    except Exception:
                        break
            
            # 检查进程是否还在运行
            if self.dream_process and self.dream_process.is_alive():
                self.after(100, self.poll_log_queue)
            else:
                # 进程已结束
                if self.dream_process:
                    self.log_status("梦境模式进程已结束")
                    self._cleanup_dream()
        except Exception as e:
            self.log_status(f"日志队列处理异常: {e}")
            self._cleanup_dream()

    def update_report_data(self, report_str):
        """
        更新统计数据显示
        处理来自梦境模式的统计信息
        """
        try:
            lines = report_str.strip().split('\n')
            for line in lines:
                if line.startswith("总循环次数:"):
                    loop_count = int(line.split(':')[1].strip().replace('次', ''))
                    self.dream_stats["total_loops"] = loop_count
                elif line.startswith("成功招募:"):
                    recruit_count = int(line.split(':')[1].strip().replace('次', ''))
                    self.dream_stats["successful_recruits"] = recruit_count
                elif line.startswith("成功战斗:"):
                    battle_count = int(line.split(':')[1].strip().replace('次', ''))
                    self.dream_stats["successful_battles"] = battle_count
                elif line.startswith("成功事件:"):
                    event_count = int(line.split(':')[1].strip().replace('次', ''))
                    self.dream_stats["successful_events"] = event_count
                elif line.startswith("总奖励积分:"):
                    award_count = int(line.split(':')[1].strip().replace('分', ''))
                    self.dream_stats["total_awards"] = award_count
                elif line.startswith("总用时:"):
                    time_str = line.split(':')[1].strip().replace('分钟', '')
                    try:
                        time_minutes = float(time_str)
                        self.dream_stats["total_time"] = time_minutes * 60  # 转换为秒
                    except ValueError:
                        pass
            
            # 更新统计显示
            self.update_stats()
            
        except Exception as e:
            self.log_status(f"更新统计数据失败: {e}")

    def stop_dream(self):
        """停止梦境模式"""
        success = self.game_mutex_manager.stop_game_safely(
            game_key="dream_process",
            log_callback=self.log_status
        )
        
        if success:
            self._cleanup_dream()

    def _set_dream_running_state(self):
        """设置梦境运行状态"""
        self.start_dream_btn.config(state=tk.DISABLED)
        self.stop_dream_btn.config(state=tk.NORMAL)

    def _set_idle_state(self):
        """设置空闲状态"""
        self.start_dream_btn.config(state=tk.NORMAL)
        self.stop_dream_btn.config(state=tk.DISABLED)

    def _cleanup_dream(self):
        """清理梦境状态"""
        self.dream_process = None
        self.log_queue = None
        self._set_idle_state()

    def update_stats(self):
        """更新统计信息显示"""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        stats_content = f"""总循环次数: {self.dream_stats["total_loops"]} 次
成功招募: {self.dream_stats["successful_recruits"]} 次
成功战斗: {self.dream_stats["successful_battles"]} 次
成功事件: {self.dream_stats["successful_events"]} 次
总奖励积分: {self.dream_stats["total_awards"]} 分
总用时: {self.format_time(self.dream_stats["total_time"])}"""
        
        self.stats_text.insert(tk.END, stats_content)
        self.stats_text.config(state='disabled')

    def reset_stats(self):
        """重置统计数据"""
        if messagebox.askyesno("确认", "确定要重置所有统计数据吗？"):
            self.reset_dream_stats()
            self.update_stats()
            self.log_status("梦境统计数据已重置")

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


# 子进程日志Handler
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

def run_dream_main(config_params, log_queue, log_level):
    """
    梦境模式主函数，在子进程中运行
    负责初始化设备管理器、OCR处理器和梦境模式，并启动梦境主循环
    
    :param config_params: 配置参数字典
    :param log_queue: 日志队列，用于向主进程发送日志消息
    :param log_level: 日志级别
    """
    import logging
    from common.config import config
    from utils.logger import get_log_file_path
    import os
    import time
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
    log_file_path = get_log_file_path(logs_dir, "dream")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger.setLevel(level)
    
    logger = logging.getLogger("dldbz")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = True
    
    try:
        logger.info(f"[梦境子进程] 日志级别: {log_level}")
        logger.info("梦境子进程已启动，等待业务执行...")
        logger.info(f"配置参数: {config_params}")
        
        # 初始化设备管理器
        logger.info("初始化设备管理器...")
        from core.device_manager import DeviceManager
        device_manager = DeviceManager()
        if not device_manager.connect_device():
            logger.error("设备连接失败")
            if log_queue:
                log_queue.put("设备连接失败")
            return
        
        # 初始化OCR处理器
        logger.info("初始化OCR处理器...")
        from core.ocr_handler import OCRHandler
        ocr_handler = OCRHandler(device_manager)
        
        # 启动梦境模式
        logger.info("启动梦境模式模块 DreamMode ...")
        from modes.dream_mode import DreamMode
        dream_mode = DreamMode(device_manager, ocr_handler, log_queue)
        
        # 运行梦境模式
        dream_mode.run(config_params)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[梦境子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}") 