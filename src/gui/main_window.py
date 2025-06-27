import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import logging
import atexit
import multiprocessing
from typing import Optional
from utils import logger
from common.config import get_config_dir
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from modes.fengmo import FengmoMode
from modes.farming import FarmingMode
from utils.mark_coord import mark_coord
from utils.logger import setup_logger
from gui.settings_panel import SettingsPanel
from utils.process_manager import get_process_manager
from utils.game_mutex_manager import get_game_mutex_manager

# 默认配置文件列表
DEFAULT_CONFIG_FILES = [
    ("fengmo.yaml", "逢魔玩法"),
    ("device.yaml", "设备"),
    ("battle.yaml", "战斗设置"),
    ("logging.yaml", "日志"),
    ("ocr.yaml", "OCR"),
]

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class MainWindow(tk.Tk):
    """
    主窗口，包含主界面和设置界面，玩法主流程用子进程启动/终止，支持日志级别动态调整
    """
    def __init__(self, title:str, config_files=DEFAULT_CONFIG_FILES):
        super().__init__()
        self.title(title)
        self.geometry("800x600")
        self.minsize(800, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # 通过setup_logger注册GUI日志Handler，禁用主进程文件日志写入
        self.logger = setup_logger(self.append_log, enable_file_log=False)
        
        # 同时配置默认logger，使其也使用GUI Handler（用于其他主进程模块）
        from utils.logger import logger as default_logger
        # 清除默认logger的所有handlers
        default_logger.handlers.clear()
        # 添加GUI Handler
        gui_handler = GuiLogHandler(self.append_log)
        gui_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        default_logger.addHandler(gui_handler)
        # 添加控制台Handler（如果有stdout）
        if sys.stdout is not None:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            default_logger.addHandler(console_handler)
        default_logger.setLevel(logging.INFO)
        
        # 使用进程管理器
        self.process_manager = get_process_manager()
        self.game_mutex_manager = get_game_mutex_manager()
        
        # 注册退出时的清理函数
        atexit.register(self._cleanup_on_exit)
        
        self.fengmo_process: Optional[multiprocessing.Process] = None
        self.log_queue: Optional[multiprocessing.Queue] = None
        self.log_level_var = tk.StringVar(value="INFO")
        # 设备管理器只初始化一次
        self.device_manager = DeviceManager()
        self.device_manager.connect_device()
        
        # 初始化服务定位器并注册核心组件
        self._init_service_locator()
        
        self._build_menu()
        self._build_main_frame()
        self.settings_panel = SettingsPanel(self, config_files, self.save_settings)
        self.show_main()
        # 绑定日志级别下拉框事件
        self.loglevel_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)
        # 启动时同步一次日志级别
        self.on_log_level_change()
        
        # 启动定期僵尸进程清理
        self.schedule_zombie_cleanup()
        
        # 定期检查运行中的进程状态
        self.after(5000, self.check_running_processes)
        
        # 启动内存监控
        self.start_memory_monitoring()
        
        # 启动自动内存优化
        self.start_memory_optimization()

    def _init_service_locator(self):
        """初始化服务定位器并注册核心组件"""
        try:
            from utils.service_locator import register_service
            from core.ocr_handler import OCRHandler
            from common.app import AppManager
            from core.battle import Battle
            from common.world import World
            
            # 创建并注册核心组件
            self.ocr_handler = OCRHandler(self.device_manager)
            self.app_manager = AppManager(self.device_manager)
            
            # 注册到服务定位器
            register_service("device_manager", self.device_manager, DeviceManager)
            register_service("ocr_handler", self.ocr_handler, OCRHandler)
            register_service("app_manager", self.app_manager, AppManager)
            
            # 创建Battle和World实例（它们会自动注册到服务定位器）
            self.battle = Battle(self.device_manager, self.ocr_handler, self.app_manager)
            self.world = World(self.device_manager, self.ocr_handler, self.app_manager)
            
            # 设置Battle的World依赖（保持向后兼容）
            self.battle.set_world(self.world)
            
            self.logger.info("服务定位器初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化服务定位器失败: {e}")
            raise

    def start_memory_monitoring(self):
        """启动内存监控"""
        try:
            from utils.memory_monitor import start_memory_monitoring
            start_memory_monitoring(check_interval=60, threshold_mb=200.0)  # 每分钟检查，200MB阈值
            self.logger.info("内存监控已启动")
        except Exception as e:
            self.logger.error(f"启动内存监控失败: {e}")

    def start_memory_optimization(self):
        """启动自动内存优化"""
        try:
            from utils.memory_optimizer import start_auto_memory_optimization
            start_auto_memory_optimization(interval=300)  # 每5分钟优化一次
            self.logger.info("自动内存优化已启动")
        except Exception as e:
            self.logger.error(f"启动内存优化失败: {e}")

    def _cleanup_on_exit(self):
        """程序退出时的清理函数"""
        self.logger.info("程序退出，清理所有资源...")
        
        # 清理文件句柄
        try:
            from utils.file_handle_manager import cleanup_file_handle_manager
            cleanup_file_handle_manager()
        except Exception as e:
            self.logger.error(f"清理文件句柄失败: {e}")
        
        # 停止内存监控
        try:
            from utils.memory_monitor import stop_memory_monitoring
            stop_memory_monitoring()
        except Exception as e:
            self.logger.error(f"停止内存监控失败: {e}")
        
        # 停止内存优化
        try:
            from utils.memory_optimizer import stop_auto_memory_optimization, cleanup_memory_optimizer
            stop_auto_memory_optimization()
            cleanup_memory_optimizer()
        except Exception as e:
            self.logger.error(f"停止内存优化失败: {e}")
        
        self.process_manager.stop_all_processes()
        self.process_manager.cleanup_zombie_processes()

    def schedule_zombie_cleanup(self):
        """定期清理僵尸进程"""
        try:
            zombie_count = self.process_manager.cleanup_zombie_processes()
            if zombie_count > 0:
                self.append_log(f"定期清理了 {zombie_count} 个僵尸进程")
        except Exception as e:
            self.logger.error(f"定期清理僵尸进程时发生异常: {e}")
        
        # 每30秒检查一次
        self.after(30000, self.schedule_zombie_cleanup)

    def append_log(self, msg):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def update_report_data(self, report_str):
        """更新统计数据显示 - 恢复原始文字版"""
        self.report_text.configure(state='normal')
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report_str)
        self.report_text.configure(state='disabled')

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        menubar.add_command(label="逢魔玩法", command=self.show_main)
        menubar.add_command(label="自动刷野", command=self.show_farming_editor)
        menubar.add_command(label="追忆之书", command=self.show_memory_editor)
        menubar.add_command(label="日常", command=self.show_daily_editor)
        menubar.add_command(label="设置", command=self.show_settings)

    def _build_main_frame(self):
        self.main_frame = ttk.Frame(self)
        # 顶部按钮区
        self.start_btn = ttk.Button(self.main_frame, text="启动逢魔", command=self.on_start)
        self.start_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.stop_btn = ttk.Button(self.main_frame, text="停止玩法", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.coord_btn = ttk.Button(self.main_frame, text="标记坐标", command=self.on_mark_coord)
        self.coord_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.status_label = ttk.Label(self.main_frame, text="状态: 等待启动")
        self.status_label.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        ttk.Label(self.main_frame, text="日志级别:").grid(row=0, column=4, padx=5, sticky="e")
        self.loglevel_combo = ttk.Combobox(self.main_frame, textvariable=self.log_level_var, values=LOG_LEVELS, width=10, state="readonly")
        self.loglevel_combo.grid(row=0, column=5, padx=5, sticky="e")
        
        # 逢魔玩法统计区块 - 恢复原始文字版
        self.report_frame = ttk.LabelFrame(self.main_frame, text="逢魔玩法统计", padding=(5, 5))
        self.report_frame.grid(row=1, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")
        self.report_text = tk.Text(self.report_frame, height=7, width=120, state='disabled', font=("Consolas", 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志区块
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=120, height=20, state='disabled', font=("Consolas", 10))
        self.log_text.grid(row=2, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")
        # 拉伸自适应
        self.main_frame.rowconfigure(1, weight=0)  # 统计区块高度固定
        self.main_frame.rowconfigure(2, weight=1)  # 日志区块随窗体拉伸
        for i in range(6):
            self.main_frame.columnconfigure(i, weight=1)

    def _build_settings_frame(self, config_files):
        pass  # 已迁移到SettingsPanel

    def show_main(self):
        if hasattr(self, 'settings_panel'):
            self.settings_panel.pack_forget()
        if hasattr(self, 'memory_editor_panel'):
            self.memory_editor_panel.pack_forget()
        if hasattr(self, 'daily_editor_panel'):
            self.daily_editor_panel.pack_forget()
        if hasattr(self, 'farming_editor_panel'):
            self.farming_editor_panel.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_settings(self):
        self.main_frame.pack_forget()
        if hasattr(self, 'memory_editor_panel'):
            self.memory_editor_panel.pack_forget()
        if hasattr(self, 'daily_editor_panel'):
            self.daily_editor_panel.pack_forget()
        if hasattr(self, 'farming_editor_panel'):
            self.farming_editor_panel.pack_forget()
        self.settings_panel.pack(fill=tk.BOTH, expand=True)

    def show_memory_editor(self):
        """显示追忆之书界面"""
        self.main_frame.pack_forget()
        if hasattr(self, 'settings_panel'):
            self.settings_panel.pack_forget()
        if hasattr(self, 'daily_editor_panel'):
            self.daily_editor_panel.pack_forget()
        if hasattr(self, 'farming_editor_panel'):
            self.farming_editor_panel.pack_forget()
        if not hasattr(self, 'memory_editor_panel'):
            from gui.memory_panel import MemoryPanel
            self.memory_editor_panel = MemoryPanel(self)
        self.memory_editor_panel.pack(fill=tk.BOTH, expand=True)

    def show_daily_editor(self):
        """显示日常界面"""
        self.main_frame.pack_forget()
        if hasattr(self, 'settings_panel'):
            self.settings_panel.pack_forget()
        if hasattr(self, 'memory_editor_panel'):
            self.memory_editor_panel.pack_forget()
        if hasattr(self, 'farming_editor_panel'):
            self.farming_editor_panel.pack_forget()
        if not hasattr(self, 'daily_editor_panel'):
            from gui.daily_panel import DailyPanel
            self.daily_editor_panel = DailyPanel(self)
        self.daily_editor_panel.pack(fill=tk.BOTH, expand=True)

    def show_farming_editor(self):
        """显示自动刷野界面"""
        self.main_frame.pack_forget()
        if hasattr(self, 'settings_panel'):
            self.settings_panel.pack_forget()
        if hasattr(self, 'memory_editor_panel'):
            self.memory_editor_panel.pack_forget()
        if hasattr(self, 'daily_editor_panel'):
            self.daily_editor_panel.pack_forget()
        if not hasattr(self, 'farming_editor_panel'):
            from gui.farming_panel import FarmingPanel
            self.farming_editor_panel = FarmingPanel(self)
        self.farming_editor_panel.pack(fill=tk.BOTH, expand=True)

    def on_log_level_change(self, event=None):
        """日志级别下拉框变更时，动态设置主进程logger级别，并同步所有Handler"""
        level = self.log_level_var.get().upper()
        log_level = getattr(logging, level, logging.INFO)
        
        # 更新主logger
        self.logger.setLevel(log_level)
        for h in self.logger.handlers:
            h.setLevel(log_level)
            
        # 同时更新默认logger（用于其他主进程模块）
        from utils.logger import logger as default_logger
        default_logger.setLevel(log_level)
        for h in default_logger.handlers:
            h.setLevel(log_level)

    def check_running_processes(self):
        """检查运行中的进程状态"""
        try:
            # 使用游戏互斥管理器检查
            running_games = self.game_mutex_manager.get_running_games()
            if running_games:
                self.status_label.config(text=f"状态: {', '.join(running_games)}运行中...")
            else:
                self.status_label.config(text="状态: 未运行")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
            
            # 继续定期检查
            self.after(5000, self.check_running_processes)
        except Exception as e:
            self.append_log(f"检查进程状态失败: {e}")

    def stop_all_processes(self):
        """停止所有进程"""
        try:
            # 使用游戏互斥管理器停止所有游戏
            stopped_count = self.game_mutex_manager.stop_all_games()
            
            # 清理本地引用
            self.fengmo_process = None
            self.log_queue = None
            
            # 更新UI状态
            self.status_label.config(text="状态: 已停止")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            return stopped_count
        except Exception as e:
            self.append_log(f"停止所有进程失败: {e}")
            return 0

    def on_start(self):
        """启动逢魔玩法"""
        # 使用游戏互斥管理器安全启动
        log_level = self.log_level_var.get()
        success, process, queue = self.game_mutex_manager.start_game_safely(
            game_key="fengmo_process",
            target_func=run_fengmo_main,
            args=(None, log_level),  # 先传None，启动后会设置正确的队列
            parent_widget=self,
            log_callback=self.append_log
        )
        
        if success:
            self.fengmo_process = process
            self.log_queue = queue
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="状态: 逢魔玩法运行中... (点击停止可终止)")
            self.after(100, self.poll_log_queue)
        else:
            # 启动失败，恢复UI状态
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="状态: 启动失败")

    def poll_log_queue(self):
        try:
            if self.log_queue:
                while True:
                    try:
                        msg = self.log_queue.get_nowait()
                        if msg.startswith("REPORT_DATA__"):
                            self.update_report_data(msg[len("REPORT_DATA__"):])
                        else:
                            self.append_log(msg)
                    except Exception:
                        break
            if self.fengmo_process and self.fengmo_process.is_alive():
                self.after(100, self.poll_log_queue)
        except Exception:
            self.append_log("日志队列已关闭。")
            return

    def on_stop(self):
        """停止逢魔玩法"""
        success = self.game_mutex_manager.stop_game_safely(
            game_key="fengmo_process",
            log_callback=self.append_log
        )
        
        if success:
            # 清理引用
            self.fengmo_process = None
            self.log_queue = None
            
            # 更新UI状态
            self.status_label.config(text="状态: 已停止")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
        else:
            self.append_log("玩法进程未运行")
            self.status_label.config(text="状态: 未运行")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def save_settings(self):
        """保存所有配置到文件"""
        config_dir = get_config_dir()
        for fname, _ in DEFAULT_CONFIG_FILES:
            if fname == "fengmo_cities.yaml":
                continue
            fpath = os.path.join(config_dir, fname)
            # 迁移后：应从SettingsPanel/tabs获取数据并保存
            pass
        messagebox.showinfo("提示", "所有设置已保存！")
        self.append_log("所有设置已保存！")

    def on_close(self):
        # 移除GUI Handler，防止内存泄漏
        self.logger.handlers = [h for h in self.logger.handlers if h.__class__.__name__ != 'GuiLogHandler']
        
        # 检查是否有游戏在运行
        if self.game_mutex_manager.is_any_game_running():
            if not messagebox.askokcancel("退出", "有游戏正在运行，确定要强制退出吗？"):
                return
            
            # 使用游戏互斥管理器清理所有游戏
            stopped_count = self.game_mutex_manager.stop_all_games()
            self.append_log(f"已终止 {stopped_count} 个游戏")
        
        # 清理僵尸进程
        zombie_count = self.process_manager.cleanup_zombie_processes()
        if zombie_count > 0:
            self.append_log(f"清理了 {zombie_count} 个僵尸进程")
        
        self.destroy()
        os._exit(0)

    def on_mark_coord(self):
        """
        调用 utils.mark_coord 工具函数，弹窗取点，控制台输出坐标
        """
        try:
            mark_coord()
        except Exception as e:
            self.append_log(f"调用标记坐标工具失败: {e}")

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

class GuiLogHandler(logging.Handler):
    """
    自定义日志Handler，将日志推送到GUI日志区
    """
    def __init__(self, append_log_func):
        super().__init__()
        self.append_log_func = append_log_func
    def emit(self, record):
        try:
            msg = self.format(record)
            # 直接推送到GUI日志区
            self.append_log_func(msg)
        except Exception:
            pass

def fix_stdio_if_none():
    import sys
    if sys.stdout is None:
        import io
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        import io
        sys.stderr = io.StringIO()

def run_fengmo_main(log_queue, log_level):
    import logging
    from common.config import config
    from utils.logger import get_log_file_path
    import os
    import time
    import signal
    import sys
    fix_stdio_if_none()
    
    # 注册信号处理器
    def cleanup_and_exit(signum, frame):
        logger.info(f"子进程收到信号 {signum}，正在清理资源...")
        # 清理资源
        if 'device_manager' in locals():
            try:
                device_manager.cleanup()
            except:
                pass
        if 'ocr_handler' in locals():
            try:
                ocr_handler.cleanup()
            except:
                pass
        if 'fengmo_mode' in locals():
            try:
                fengmo_mode.cleanup()
            except:
                pass
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)
    
    # 先移除所有 root logger handler，防止默认 handler 的 stream 为 None
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    # 读取配置文件的日志格式，并转换，传入datefmt参数
    log_format, datefmt = config.get_logging_format_and_datefmt(config.logging.format, getattr(config.logging, 'datefmt', None))
    formatter = config.get_no_millisec_formatter(log_format, datefmt)
    
    # 配置队列handler（发送到主进程GUI）
    queue_handler = QueueLogHandler(log_queue)
    queue_handler.setLevel(logging.NOTSET)
    queue_handler.setFormatter(formatter)
    root_logger.addHandler(queue_handler)
    
    # 配置文件handler（写入本地日志文件）
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = get_log_file_path(logs_dir, "fengmo")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 日志级别
    level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger.setLevel(level)
    
    # 关键：同步dldbz logger的level和handler
    logger = logging.getLogger("dldbz")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = True
    
    try:
        logger.info(f"[子进程] 日志级别: {log_level}")
        logger.info("玩法子进程已启动，等待业务执行...")
        logger.info("Initializing device manager...")
        device_manager = DeviceManager()
        if not device_manager.connect_device():
            logger.error("Failed to connect device")
            if log_queue:
                log_queue.put("设备连接失败")
            return
        logger.info("Initializing OCR handler...")
        ocr_handler = OCRHandler(device_manager)
        logger.info("启动逢魔玩法模块 FengmoMode ...")
        fengmo_mode = FengmoMode(device_manager, ocr_handler, log_queue)
        fengmo_mode.run()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}")
    finally:
        # 确保资源被清理
        cleanup_and_exit(None, None)

def run_farming_main(log_queue, log_level):
    """
    刷野玩法主函数，在子进程中运行
    负责初始化设备管理器、OCR处理器和刷野模式，并启动刷野主循环
    
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
    
    # 读取配置文件的日志格式，并转换，传入datefmt参数
    log_format, datefmt = config.get_logging_format_and_datefmt(config.logging.format, getattr(config.logging, 'datefmt', None))
    formatter = config.get_no_millisec_formatter(log_format, datefmt)
    
    # 配置队列handler（发送到主进程GUI）
    queue_handler = QueueLogHandler(log_queue)
    queue_handler.setLevel(logging.NOTSET)
    queue_handler.setFormatter(formatter)
    root_logger.addHandler(queue_handler)
    
    # 配置文件handler（写入本地日志文件）
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = get_log_file_path(logs_dir, "farming")
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
        logger.info(f"[刷野子进程] 日志级别: {log_level}")
        logger.info("刷野子进程已启动，等待业务执行...")
        
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
        
        # 启动刷野模式
        logger.info("启动刷野玩法模块 FarmingMode ...")
        farming_mode = FarmingMode(device_manager, ocr_handler, log_queue)
        
        # 运行刷野模式
        farming_mode.run()
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[刷野子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}") 