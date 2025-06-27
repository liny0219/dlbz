"""
刷野玩法界面
提供刷野功能的独立界面，包含配置选项、启动/停止控制、日志显示和统计信息
"""

import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import os
import datetime
from common.config import get_config_dir
from utils.process_manager import get_process_manager
from utils.game_mutex_manager import get_game_mutex_manager


class FarmingPanel(ttk.Frame):
    """
    刷野玩法界面
    """
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        
        # 初始化进程管理器和游戏互斥管理器
        self.process_manager = get_process_manager()
        self.game_mutex_manager = get_game_mutex_manager()
        
        # 进程相关
        self.farming_process = None
        self.log_queue = None
        
        # 统计信息
        self.reset_farming_stats()
        
        # 构建界面
        self._build_widgets()
        
        # 加载配置
        self.load_config()

    def reset_farming_stats(self):
        """重置刷野统计数据"""
        self.farming_stats = {
            "total_battles": 0,
            "successful_battles": 0,
            "failed_battles": 0,
            "total_time": 0.0,
            "avg_battle_time": 0.0,
            "current_session_time": 0.0
        }

    def load_config(self):
        """加载刷野配置"""
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, "farming.yaml")
        
        # 不需要配置文件了，刷野将持续运行
        pass

    def save_config(self):
        """保存刷野配置"""
        # 不需要保存配置了
        config = {}
        
        config_dir = get_config_dir()
        config_path = os.path.join(config_dir, "farming.yaml")
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            self.log_status("刷野配置已保存")
        except Exception as e:
            self.log_status(f"保存刷野配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _build_widgets(self):
        """构建界面组件"""
        # 刷野配置区域
        farming_frame = ttk.LabelFrame(self, text="自动刷野配置", padding=(10, 10))
        farming_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        # 刷野说明
        info_frame = ttk.Frame(farming_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="自动刷野模式将持续运行直到手动停止", 
                 wraplength=400, font=("TkDefaultFont", 9)).pack(pady=5)

        # 按钮区域
        button_frame = ttk.Frame(farming_frame)
        button_frame.pack(fill=tk.X, pady=(10, 5))

        # 开始刷野按钮
        self.start_farming_btn = ttk.Button(button_frame, text="开始刷野", 
                                           command=self.start_farming, style="Accent.TButton")
        self.start_farming_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止刷野按钮
        self.stop_farming_btn = ttk.Button(button_frame, text="停止刷野", 
                                          command=self.stop_farming, state=tk.DISABLED)
        self.stop_farming_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存配置按钮
        save_config_btn = ttk.Button(button_frame, text="保存配置", 
                                    command=self.save_config)
        save_config_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 重置统计按钮
        reset_stats_btn = ttk.Button(button_frame, text="重置统计", 
                                    command=self.reset_stats)
        reset_stats_btn.pack(side=tk.LEFT)

        # 统计信息展示区域
        stats_frame = ttk.LabelFrame(self, text="刷野统计", padding=(10, 10))
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
        self.log_status("自动刷野面板已初始化")
        self.log_status("点击开始刷野即可启动持续刷野模式")

    def start_farming(self):
        """开始刷野"""
        # 在启动玩法前检查并清理日志目录
        try:
            from utils.logger import cleanup_logs_dir
            cleanup_logs_dir()
        except Exception as e:
            self.log_status(f"清理日志目录失败: {e}")
        
        # 自动保存配置
        self.save_config()
        
        self.log_status("=" * 50)
        self.log_status("刷野进程启动中...")
        self.log_status("持续运行模式: 将一直刷野直到手动停止")
        
        # 重置统计数据
        self.reset_farming_stats()
        self.update_stats()
        
        # 获取日志级别
        log_level = "INFO"
        if hasattr(self.parent, 'log_level_var'):
            log_level = self.parent.log_level_var.get()
        
        # 使用游戏互斥管理器启动
        from gui.main_window import run_farming_main
        success, process, queue = self.game_mutex_manager.start_game_safely(
            game_key="farming_process",
            target_func=run_farming_main,
            args=(None, log_level),  # 先传None，启动后会设置正确的队列
            parent_widget=self.parent,
            log_callback=self.log_status
        )
        
        if success:
            self.farming_process = process
            self.log_queue = queue
            # 更新按钮状态
            self._set_farming_running_state()
            self.log_status("刷野进程已启动，正在连接设备...")
            # 开始轮询日志队列
            self.after(100, self.poll_log_queue)
        else:
            self.log_status("刷野进程启动失败")

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
            if self.farming_process and self.farming_process.is_alive():
                self.after(100, self.poll_log_queue)
            else:
                # 进程已结束
                if self.farming_process:
                    self.log_status("刷野进程已结束")
                    self._cleanup_farming()
        except Exception as e:
            self.log_status(f"日志队列处理异常: {e}")
            self._cleanup_farming()

    def update_report_data(self, report_str):
        """
        更新统计数据显示
        处理来自刷野模式的统计信息
        """
        try:
            lines = report_str.strip().split('\n')
            for line in lines:
                if line.startswith("当前战斗次数:"):
                    battle_count = int(line.split(':')[1].strip().replace('次', ''))
                    self.farming_stats["total_battles"] = battle_count
                    self.farming_stats["successful_battles"] = battle_count  # 假设所有战斗都成功
                elif line.startswith("当前挂机时间:"):
                    time_str = line.split(':')[1].strip().replace('分钟', '')
                    try:
                        time_minutes = float(time_str)
                        self.farming_stats["total_time"] = time_minutes * 60  # 转换为秒
                        if self.farming_stats["total_battles"] > 0:
                            self.farming_stats["avg_battle_time"] = self.farming_stats["total_time"] / self.farming_stats["total_battles"]
                    except ValueError:
                        pass
            
            # 更新统计显示
            self.update_stats()
            
        except Exception as e:
            self.log_status(f"更新统计数据失败: {e}")

    def stop_farming(self):
        """停止刷野"""
        success = self.game_mutex_manager.stop_game_safely(
            game_key="farming_process",
            log_callback=self.log_status
        )
        
        if success:
            self._cleanup_farming()

    def _set_farming_running_state(self):
        """设置刷野运行状态"""
        self.start_farming_btn.config(state=tk.DISABLED)
        self.stop_farming_btn.config(state=tk.NORMAL)

    def _set_idle_state(self):
        """设置空闲状态"""
        self.start_farming_btn.config(state=tk.NORMAL)
        self.stop_farming_btn.config(state=tk.DISABLED)

    def _cleanup_farming(self):
        """清理刷野状态"""
        self.farming_process = None
        self.log_queue = None
        self._set_idle_state()

    def update_stats(self):
        """更新统计信息显示"""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        # 计算成功率
        success_rate = 0
        if self.farming_stats["total_battles"] > 0:
            success_rate = (self.farming_stats["successful_battles"] / self.farming_stats["total_battles"]) * 100
        
        stats_content = f"""总战斗次数: {self.farming_stats["total_battles"]} 次
成功战斗: {self.farming_stats["successful_battles"]} 次
失败战斗: {self.farming_stats["failed_battles"]} 次
成功率: {success_rate:.1f}%
总用时: {self.format_time(self.farming_stats["total_time"])}
平均每战斗用时: {self.format_time(self.farming_stats["avg_battle_time"])}"""
        
        self.stats_text.insert(tk.END, stats_content)
        self.stats_text.config(state='disabled')

    def reset_stats(self):
        """重置统计数据"""
        if messagebox.askyesno("确认", "确定要重置所有统计数据吗？"):
            self.reset_farming_stats()
            self.update_stats()
            self.log_status("刷野统计数据已重置")

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