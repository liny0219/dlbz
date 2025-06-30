import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import datetime
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type
import yaml
import logging
from utils.process_manager import get_process_manager
from utils.game_mutex_manager import get_game_mutex_manager

class MemoryPanel(ttk.Frame):
    """
    追忆之书功能面板
    包含战斗脚本文件路径配置和测试按钮
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config_file = "memory_test.yaml"
        
        # 初始化进程管理器和游戏互斥管理器
        self.process_manager = get_process_manager()
        self.game_mutex_manager = get_game_mutex_manager()
        
        # 初始化变量
        self.memory_test_process = None
        self.battle_test_process = None
        self.log_queue = None
        
        # 统计数据（只记录追忆之书相关）
        self.memory_total = 0
        self.memory_successful = 0
        self.memory_failed = 0
        
        # 配置变量
        self.memory_script_var = tk.StringVar()
        self.battle_script_var = tk.StringVar()
        self.battle_count_var = tk.StringVar(value="1")
        self.click_x_var = tk.StringVar(value="640")
        self.click_y_var = tk.StringVar(value="360")
        self.ui_wait_time_var = tk.StringVar(value="2")
        
        self.load_config()
        self._build_widgets()

    def load_config(self):
        """加载追忆之书配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 默认配置
        self.config_data = {
            "battle_script_path": "",
            "memory_config": {
                "battle_count": 1,
                "click_x": 1100,
                "click_y": 200,
                "ui_wait_time": 0.5
            }
        }
        
        # 如果配置文件存在，加载配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    self.config_data.update(loaded_config)
                    
                    # 确保memory_config存在所有必要的键
                    if "memory_config" not in self.config_data:
                        self.config_data["memory_config"] = {}
                    
                    # 合并默认值
                    default_memory = {
                        "battle_count": 1,
                        "click_x": 1100, 
                        "click_y": 200,
                        "ui_wait_time": 0.5
                    }
                    for key, value in default_memory.items():
                        if key not in self.config_data["memory_config"]:
                            self.config_data["memory_config"][key] = value
                            
            except Exception as e:
                print(f"加载追忆之书配置失败: {e}")

    def save_config(self):
        """保存追忆之书配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, self.config_file)
        
        # 更新配置数据
        self.config_data["battle_script_path"] = self.battle_script_var.get()
        self.config_data["memory_config"]["battle_count"] = self.battle_count_var.get()
        self.config_data["memory_config"]["click_x"] = self.click_x_var.get()
        self.config_data["memory_config"]["click_y"] = self.click_y_var.get()
        self.config_data["memory_config"]["ui_wait_time"] = self.ui_wait_time_var.get()
        
        try:
            save_yaml_with_type(config_path, self.config_data)
            self.log_status("配置已保存到文件")
        except Exception as e:
            print(f"保存配置失败: {e}")
            self.log_status(f"保存配置失败: {e}")

    def _build_widgets(self):
        """构建界面组件"""
        # 追忆之书配置区域（整合后的配置区域）
        memory_frame = ttk.LabelFrame(self, text="追忆之书配置", padding=(10, 10))
        memory_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        # 战斗脚本文件路径（移动到追忆之书配置中）
        script_frame = ttk.Frame(memory_frame)
        script_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(script_frame, text="战斗脚本文件路径:", width=18, anchor="w").pack(side=tk.LEFT)
        
        self.battle_script_var = tk.StringVar(value=self.config_data.get("battle_script_path", ""))
        script_entry = ttk.Entry(script_frame, textvariable=self.battle_script_var, width=50)
        script_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(script_frame, text="浏览", width=8, command=self.browse_script_file)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        edit_btn = ttk.Button(script_frame, text="编辑", width=8, command=self.edit_script_file)
        edit_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 战斗次数配置
        battle_count_frame = ttk.Frame(memory_frame)
        battle_count_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(battle_count_frame, text="战斗次数:", width=12, anchor="w").pack(side=tk.LEFT)
        
        self.battle_count_var = tk.IntVar(value=self.config_data["memory_config"]["battle_count"])
        battle_count_spin = tk.Spinbox(battle_count_frame, from_=1, to=999, increment=1, 
                                      textvariable=self.battle_count_var, width=10)
        battle_count_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(battle_count_frame, text="次", width=3, anchor="w").pack(side=tk.LEFT, padx=(5, 0))

        # 点击阅读坐标配置
        coord_frame = ttk.Frame(memory_frame)
        coord_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(coord_frame, text="点击阅读坐标:", width=12, anchor="w").pack(side=tk.LEFT)
        
        # X坐标
        ttk.Label(coord_frame, text="X:", width=2, anchor="w").pack(side=tk.LEFT, padx=(5, 0))
        self.click_x_var = tk.IntVar(value=self.config_data["memory_config"]["click_x"])
        x_spin = tk.Spinbox(coord_frame, from_=0, to=1920, increment=1, 
                           textvariable=self.click_x_var, width=8)
        x_spin.pack(side=tk.LEFT, padx=(2, 5))
        
        # Y坐标
        ttk.Label(coord_frame, text="Y:", width=2, anchor="w").pack(side=tk.LEFT, padx=(5, 0))
        self.click_y_var = tk.IntVar(value=self.config_data["memory_config"]["click_y"])
        y_spin = tk.Spinbox(coord_frame, from_=0, to=1080, increment=1, 
                           textvariable=self.click_y_var, width=8)
        y_spin.pack(side=tk.LEFT, padx=(2, 0))
        
        # 坐标说明
        ttk.Label(coord_frame, text="(用于点击追忆之书阅读按钮)", 
                 foreground="gray", font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=(10, 0))

        # UI等待时间配置
        ui_wait_frame = ttk.Frame(memory_frame)
        ui_wait_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ui_wait_frame, text="UI等待时间:", width=12, anchor="w").pack(side=tk.LEFT)
        
        self.ui_wait_time_var = tk.DoubleVar(value=self.config_data["memory_config"]["ui_wait_time"])
        ui_wait_spin = tk.Spinbox(ui_wait_frame, from_=0.1, to=5.0, increment=0.1, 
                                 textvariable=self.ui_wait_time_var, width=10, format="%.1f")
        ui_wait_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(ui_wait_frame, text="秒", width=3, anchor="w").pack(side=tk.LEFT, padx=(5, 0))
        
        # UI等待时间说明
        ttk.Label(ui_wait_frame, text="(操作间隔等待时间)", 
                 foreground="gray", font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=(10, 0))

        # 第一行按钮区域（追忆之书相关）
        memory_button_frame1 = ttk.Frame(memory_frame)
        memory_button_frame1.pack(fill=tk.X, pady=(10, 5))

        # 开始追忆按钮
        self.start_memory_btn = ttk.Button(memory_button_frame1, text="开始追忆", 
                                          command=self.start_memory, style="Accent.TButton")
        self.start_memory_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止追忆按钮
        self.stop_memory_btn = ttk.Button(memory_button_frame1, text="停止追忆", 
                                         command=self.stop_memory, state=tk.DISABLED)
        self.stop_memory_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存配置按钮
        save_config_btn = ttk.Button(memory_button_frame1, text="保存配置", 
                                    command=self.save_config)
        save_config_btn.pack(side=tk.LEFT)

        # 第二行按钮区域（单次战斗测试相关）
        memory_button_frame2 = ttk.Frame(memory_frame)
        memory_button_frame2.pack(fill=tk.X, pady=(5, 0))

        # 单次战斗测试按钮
        self.start_test_btn = ttk.Button(memory_button_frame2, text="单次测试", command=self.start_test, 
                                        style="Accent.TButton")
        self.start_test_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止测试按钮
        self.stop_test_btn = ttk.Button(memory_button_frame2, text="停止测试", command=self.stop_test, 
                                       state=tk.DISABLED)
        self.stop_test_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 指令说明按钮
        help_btn = ttk.Button(memory_button_frame2, text="指令说明", width=8, command=self.on_battle_help)
        help_btn.pack(side=tk.LEFT, padx=(0, 15))

        # 添加说明标签（移到指令说明按钮同一行后面）
        info_label = ttk.Label(memory_button_frame2, text="⚠️ 请确保游戏处于战斗界面后再开始测试", 
                              foreground="orange", font=("TkDefaultFont", 9))
        info_label.pack(side=tk.LEFT, padx=(0, 0))

        # 统计信息展示区域
        stats_frame = ttk.LabelFrame(self, text="追忆之书统计", padding=(10, 10))
        stats_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.stats_text = tk.Text(stats_frame, height=2, width=80, font=("Consolas", 11), state='disabled')
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # 状态区域
        status_frame = ttk.LabelFrame(self, text="运行日志", padding=(10, 10))
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))

        self.status_text = tk.Text(status_frame, height=12, width=80, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 初始化统计和状态信息
        self.update_stats()
        self.log_status("追忆之书面板已初始化")
        self.log_status("请配置战斗脚本文件路径，然后选择相应的功能")

    def browse_script_file(self):
        """浏览选择战斗脚本文件"""
        config_dir = get_config_dir()
        default_dir = os.path.join(config_dir, 'battle_scripts')
        
        filetypes = [
            ("文本文件", "*.txt"),
            ("所有文件", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="选择战斗脚本文件",
            initialdir=default_dir if os.path.exists(default_dir) else config_dir,
            filetypes=filetypes
        )
        
        if filepath:
            self.battle_script_var.set(filepath)
            self.log_status(f"已选择战斗脚本文件: {filepath}")

    def edit_script_file(self):
        """编辑战斗脚本文件"""
        script_path = self.battle_script_var.get().strip()
        
        if not script_path:
            messagebox.showwarning("提示", "请先选择战斗脚本文件！")
            return
        
        # 检查文件是否存在
        if not os.path.isabs(script_path):
            config_dir = get_config_dir()
            # 尝试在config目录下查找
            try_path = os.path.join(config_dir, script_path)
            if os.path.exists(try_path):
                script_path = try_path
            else:
                # 尝试在battle_scripts目录下查找
                try_path2 = os.path.join(config_dir, 'battle_scripts', script_path)
                if os.path.exists(try_path2):
                    script_path = try_path2
        
        if not os.path.exists(script_path):
            messagebox.showwarning("提示", f"文件不存在: {script_path}")
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(script_path)
            else:  # Linux/Mac
                subprocess.Popen(['xdg-open', script_path])
            self.log_status(f"已打开文件编辑器: {script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {script_path}\n{e}")

    def start_test(self):
        """开始单次战斗测试"""
        # 使用游戏互斥管理器安全启动
        script_path = self.battle_script_var.get().strip()
        if not script_path:
            messagebox.showwarning("提示", "请先配置战斗脚本文件路径！")
            return
        
        # 自动保存配置
        self.save_config()
        
        self.log_status("=" * 50)
        self.log_status("单次战斗测试进程启动中...")
        self.log_status(f"使用战斗脚本: {script_path}")
        
        # 获取日志级别
        log_level = getattr(self.parent, 'log_level_var', tk.StringVar(value="INFO")).get()
        
        # 使用游戏互斥管理器启动
        success, process, queue = self.game_mutex_manager.start_game_safely(
            game_key="battle_test_process",
            target_func=run_battle_test_main,
            args=(script_path, None, log_level),  # 先传None，启动后会设置正确的队列
            parent_widget=self.parent,
            log_callback=self.log_status
        )
        
        if success:
            self.battle_test_process = process
            self.log_queue = queue
            # 更新按钮状态
            self._set_test_running_state()
            self._set_battle_running_state()
            # 开始轮询日志队列
            self.after(100, self.poll_battle_test_log_queue)
        else:
            self.log_status("单次战斗测试启动失败")

    def poll_battle_test_log_queue(self):
        """轮询单次战斗测试日志队列"""
        try:
            if self.log_queue:
                while True:
                    try:
                        msg = self.log_queue.get_nowait()
                        if msg.startswith("REPORT_DATA__"):
                            # 处理报告数据（如果需要）
                            pass
                        else:
                            self.log_status(msg)
                    except Exception:
                        break
            
            # 如果进程还在运行，继续轮询
            if self.battle_test_process and self.battle_test_process.is_alive():
                self.after(100, self.poll_battle_test_log_queue)
            else:
                # 进程结束，清理状态
                self.log_status("单次战斗测试进程已结束")
                self._cleanup_battle_test()
        except Exception:
            self.log_status("单次战斗测试日志队列已关闭")

    def _cleanup_battle_test(self):
        """清理单次战斗测试状态"""
        self.battle_test_process = None
        self._set_test_idle_state()

    def _is_any_test_running(self):
        """检查是否有任何测试在运行"""
        battle_running = self.battle_test_process and self.battle_test_process.is_alive()
        memory_running = self.memory_test_process and self.memory_test_process.is_alive()
        return battle_running or memory_running

    def _set_test_running_state(self):
        """设置测试运行状态 - 禁用所有开始按钮"""
        # 禁用所有开始按钮，实现互斥
        self.start_memory_btn.config(state=tk.DISABLED)
        self.start_test_btn.config(state=tk.DISABLED)

    def _set_memory_running_state(self):
        """设置追忆测试运行状态"""
        self.start_memory_btn.config(state=tk.DISABLED)
        self.stop_memory_btn.config(state=tk.NORMAL)

    def _set_battle_running_state(self):
        """设置单次战斗测试运行状态"""
        self.stop_test_btn.config(state=tk.NORMAL)

    def _set_test_idle_state(self):
        """设置测试空闲状态 - 启用开始按钮，禁用停止按钮"""
        self.start_memory_btn.config(state=tk.NORMAL)
        self.start_test_btn.config(state=tk.NORMAL)
        self.stop_memory_btn.config(state=tk.DISABLED)
        self.stop_test_btn.config(state=tk.DISABLED)

    def stop_test(self):
        """停止单次战斗测试"""
        success = self.game_mutex_manager.stop_game_safely(
            game_key="battle_test_process",
            log_callback=self.log_status
        )
        
        if success:
            self._cleanup_battle_test()

    def on_battle_help(self):
        """打开战斗指令说明文件"""
        config_dir = get_config_dir()
        help_path = os.path.join(config_dir, 'readme.txt')
        
        if not os.path.exists(help_path):
            messagebox.showwarning("提示", f"未找到说明文件: {help_path}")
            self.log_status(f"未找到说明文件: {help_path}")
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(help_path)
            else:  # Linux/Mac
                subprocess.Popen(['xdg-open', help_path])
            self.log_status(f"已打开战斗指令说明文件: {help_path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开说明文件: {help_path}\n{e}")
            self.log_status(f"打开说明文件失败: {e}")

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
        
        # 计算成功率
        success_rate = (self.memory_successful / self.memory_total * 100) if self.memory_total > 0 else 0
        
        stats_content = f"""追忆之书总次数: {self.memory_total} 次    成功: {self.memory_successful} 次    失败: {self.memory_failed} 次    成功率: {success_rate:.1f}%
"""
        
        self.stats_text.insert(tk.END, stats_content)
        self.stats_text.config(state='disabled')

    def increment_memory_stats(self, success=True):
        """增加追忆之书统计数据"""
        self.memory_total += 1
        if success:
            self.memory_successful += 1
        else:
            self.memory_failed += 1
        self.update_stats()

    def reset_stats(self):
        """重置追忆之书统计数据"""
        self.memory_total = 0
        self.memory_successful = 0
        self.memory_failed = 0
        self.update_stats()
        self.log_status("追忆之书统计数据已重置")

    def _handle_stats_update(self, msg):
        """处理统计数据更新消息"""
        try:
            # 消息格式: STATS_UPDATE__success:true 或 STATS_UPDATE__success:false
            stats_data = msg[len("STATS_UPDATE__"):]
            if "success:true" in stats_data:
                self.increment_memory_stats(success=True)
            elif "success:false" in stats_data:
                self.increment_memory_stats(success=False)
        except Exception as e:
            self.log_status(f"处理统计更新失败: {e}")

    def start_memory(self):
        """开始追忆之书测试"""
        # 使用游戏互斥管理器安全启动
        script_path = self.battle_script_var.get().strip()
        if not script_path:
            messagebox.showwarning("提示", "请先配置追忆之书脚本文件路径！")
            return
        
        try:
            battle_count = int(self.battle_count_var.get())
            click_x = int(self.click_x_var.get())
            click_y = int(self.click_y_var.get())
            ui_wait_time = float(self.ui_wait_time_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值！")
            return
        
        # 自动保存配置
        self.save_config()
        
        self.log_status("=" * 50)
        self.log_status("追忆之书测试进程启动中...")
        self.log_status(f"使用脚本: {script_path}")
        self.log_status(f"战斗次数: {battle_count}")
        self.log_status(f"点击坐标: ({click_x}, {click_y})")
        self.log_status(f"UI等待时间: {ui_wait_time}秒")
        
        # 获取日志级别
        log_level = getattr(self.parent, 'log_level_var', tk.StringVar(value="INFO")).get()
        
        # 使用游戏互斥管理器启动
        success, process, queue = self.game_mutex_manager.start_game_safely(
            game_key="memory_test_process",
            target_func=run_memory_test_main,
            args=(script_path, battle_count, click_x, click_y, ui_wait_time, None, log_level),  # 先传None，启动后会设置正确的队列
            parent_widget=self.parent,
            log_callback=self.log_status
        )
        
        if success:
            self.memory_test_process = process
            self.log_queue = queue
            # 更新按钮状态
            self._set_test_running_state()
            self._set_memory_running_state()
            # 开始轮询日志队列
            self.after(100, self.poll_memory_test_log_queue)
        else:
            self.log_status("追忆之书测试启动失败")

    def poll_memory_test_log_queue(self):
        """轮询追忆之书测试日志队列"""
        try:
            if self.log_queue:
                while True:
                    try:
                        msg = self.log_queue.get_nowait()
                        if msg.startswith("STATS_UPDATE__"):
                            # 处理统计数据更新
                            self._handle_stats_update(msg)
                        elif msg.startswith("REPORT_DATA__"):
                            # 处理报告数据（如果需要）
                            pass
                        else:
                            self.log_status(msg)
                    except Exception:
                        break
            
            # 如果进程还在运行，继续轮询
            if self.memory_test_process and self.memory_test_process.is_alive():
                self.after(100, self.poll_memory_test_log_queue)
            else:
                # 进程结束，清理状态
                self.log_status("追忆之书测试进程已结束")
                self._cleanup_memory_test()
        except Exception:
            self.log_status("追忆之书测试日志队列已关闭")

    def _cleanup_memory_test(self):
        """清理追忆之书测试状态"""
        self.memory_test_process = None
        self._set_test_idle_state()

    def stop_memory(self):
        """停止追忆之书测试"""
        success = self.game_mutex_manager.stop_game_safely(
            game_key="memory_test_process",
            log_callback=self.log_status
        )
        
        if success:
            self._cleanup_memory_test()

# 子进程日志Handler（与main_window中的相同）
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

def run_battle_test_main(script_path, log_queue, log_level):
    """
    单次战斗测试主函数，在子进程中运行
    
    :param script_path: 战斗脚本文件路径
    :param log_queue: 日志队列，用于向主进程发送日志消息
    :param log_level: 日志级别
    """
    import logging
    import os
    import traceback
    from common.config import config
    from utils.logger import get_log_file_path
    from core.device_manager import DeviceManager
    from core.ocr_handler import OCRHandler
    from modes.battle_test import BattleTestMode
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
    log_file_path = get_log_file_path(logs_dir, "battle_test")
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
        logger.info(f"[单次战斗测试子进程] 日志级别: {log_level}")
        logger.info("单次战斗测试子进程已启动，等待业务执行...")
        
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
        
        # 启动单次战斗测试模式
        logger.info("启动单次战斗测试模块 BattleTestMode ...")
        battle_test_mode = BattleTestMode(device_manager, ocr_handler, log_queue)
        
        # 运行单次战斗测试
        battle_test_mode.run(script_path)
        
    except Exception as e:
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[单次战斗测试子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}")

def run_memory_test_main(script_path, battle_count, click_x, click_y, ui_wait_time, log_queue, log_level):
    """
    追忆之书测试主函数，在子进程中运行
    
    :param script_path: 战斗脚本文件路径
    :param battle_count: 战斗次数
    :param click_x: 点击阅读X坐标
    :param click_y: 点击阅读Y坐标
    :param ui_wait_time: UI等待时间
    :param log_queue: 日志队列，用于向主进程发送日志消息
    :param log_level: 日志级别
    """
    import logging
    import os
    import traceback
    from common.config import config
    from utils.logger import get_log_file_path
    from core.device_manager import DeviceManager
    from core.ocr_handler import OCRHandler
    from modes.memory import MemoryMode
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
    log_file_path = get_log_file_path(logs_dir, "memory_test")
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
        logger.info(f"[追忆之书子进程] 日志级别: {log_level}")
        logger.info("追忆之书子进程已启动，等待业务执行...")
        
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
        
        # 启动追忆之书模式
        logger.info("启动追忆之书模块 MemoryMode ...")
        memory_mode = MemoryMode(device_manager, ocr_handler, log_queue)
        
        # 运行追忆之书测试
        memory_mode.run(script_path, battle_count, click_x, click_y, ui_wait_time)
        
    except Exception as e:
        tb = traceback.format_exc()
        try:
            if log_queue:
                log_queue.put(f"[追忆之书子进程异常] {e}\n{tb}")
        except Exception as ee:
            print(f"日志队列异常: {ee}\n{traceback.format_exc()}") 