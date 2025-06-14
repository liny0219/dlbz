import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import yaml
import os
import sys
import multiprocessing
import logging
from utils import logger
from common.config import get_config_dir
import traceback
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from modes.fengmo import FengmoMode
from modes.farming import FarmingMode
from utils.mark_coord import mark_coord
from utils.logger import setup_logger
from gui.monster_editor import MonsterEditor

CONFIG_FILES = [
    ("fengmo.yaml", "逢魔玩法"),
    ("device.yaml", "设备"),
    ("battle.yaml", "战斗配置"),
    ("settings.yaml", "全局设置"),
    ("logging.yaml", "日志"),
    ("game.yaml", "游戏"),
    ("ocr.yaml", "OCR"),
]
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class MainWindow(tk.Tk):
    """
    主窗口，包含主界面和设置界面，玩法主流程用子进程启动/终止，支持日志级别动态调整
    """
    def __init__(self, title:str, config_files=CONFIG_FILES):
        super().__init__()
        self.title(title)
        self.geometry("800x600")
        self.minsize(700, 400)
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
        self.fengmo_process = None
        self.log_queue = None
        self.log_level_var = tk.StringVar(value="INFO")
        # 设备管理器只初始化一次
        self.device_manager = DeviceManager()
        self.device_manager.connect_device()
        self._build_menu()
        self._build_main_frame()
        self._build_settings_frame(config_files)
        self.show_main()
        # 绑定日志级别下拉框事件
        self.loglevel_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)
        # 启动时同步一次日志级别
        self.on_log_level_change()

    def append_log(self, msg):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def update_report_data(self, report_str):
        self.report_text.configure(state='normal')
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report_str)
        self.report_text.configure(state='disabled')

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        menubar.add_command(label="主界面", command=self.show_main)
        menubar.add_command(label="设置", command=self.show_settings)

    def _build_main_frame(self):
        self.main_frame = ttk.Frame(self)
        # 顶部按钮区
        self.start_btn = ttk.Button(self.main_frame, text="开始逢魔", command=self.on_start)
        self.start_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.farming_btn = ttk.Button(self.main_frame, text="自动刷野", command=self.on_start_farming)
        self.farming_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.stop_btn = ttk.Button(self.main_frame, text="停止玩法", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.coord_btn = ttk.Button(self.main_frame, text="标记坐标", command=self.on_mark_coord)
        self.coord_btn.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        self.status_label = ttk.Label(self.main_frame, text="状态: 等待启动")
        self.status_label.grid(row=0, column=4, padx=10, pady=10, sticky="w")
        ttk.Label(self.main_frame, text="日志级别:").grid(row=0, column=5, padx=5, sticky="e")
        self.loglevel_combo = ttk.Combobox(self.main_frame, textvariable=self.log_level_var, values=LOG_LEVELS, width=10, state="readonly")
        self.loglevel_combo.grid(row=0, column=6, padx=5, sticky="e")
        # 玩法统计区块
        self.report_frame = ttk.LabelFrame(self.main_frame, text="玩法统计", padding=(5, 5))
        self.report_frame.grid(row=1, column=0, columnspan=7, padx=10, pady=5, sticky="nsew")
        self.report_text = tk.Text(self.report_frame, height=7, width=120, state='disabled', font=("Consolas", 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        # 日志区块
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=120, height=20, state='disabled', font=("Consolas", 10))
        self.log_text.grid(row=2, column=0, columnspan=7, padx=10, pady=5, sticky="nsew")
        # 拉伸自适应
        self.main_frame.rowconfigure(1, weight=0)  # 统计区块高度固定
        self.main_frame.rowconfigure(2, weight=1)  # 日志区块随窗体拉伸
        for i in range(7):
            self.main_frame.columnconfigure(i, weight=1)

    def _build_settings_frame(self, config_files):
        self.settings_frame = ttk.Frame(self)
        self.settings_notebook = ttk.Notebook(self.settings_frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True)
        self.config_vars = {}
        config_dir = get_config_dir()
        for fname, label in config_files:
            if fname == "fengmo_cities.yaml":
                continue
            fpath = os.path.join(config_dir, fname)
            frame = ttk.Frame(self.settings_notebook)
            self.settings_notebook.add(frame, text=label)
            vars_dict = {}
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    try:
                        data = yaml.safe_load(f) or {}
                    except Exception as e:
                        data = {}
                row = 0
                # 针对逢魔玩法特殊处理
                if fname == "fengmo.yaml":
                    label_width = 14  # 增大标签宽度
                    input_width = 20  # 输入控件宽度
                    # rest_in_inn
                    rest_val = data.get("rest_in_inn", False)
                    if isinstance(rest_val, str):
                        rest_val = rest_val.lower() == "true"
                    rest_var = tk.StringVar(value="是" if rest_val else "否")
                    ttk.Label(frame, text="旅馆休息", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    rest_combo = ttk.Combobox(frame, textvariable=rest_var, values=["是", "否"], state="readonly", width=input_width)
                    rest_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["rest_in_inn"] = rest_var
                    row += 1
                    # vip_cure
                    vip_cure_val = data.get("vip_cure", False)
                    if isinstance(vip_cure_val, str):
                        vip_cure_val = vip_cure_val.lower() == "true"
                    vip_cure_var = tk.StringVar(value="是" if vip_cure_val else "否")
                    ttk.Label(frame, text="月卡恢复", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    vip_cure_combo = ttk.Combobox(frame, textvariable=vip_cure_var, values=["是", "否"], state="readonly", width=input_width)
                    vip_cure_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["vip_cure"] = vip_cure_var
                    row += 1
                    # city
                    from common.config import config
                    city_keys = list(config.fengmo_cities.keys())
                    city_display = city_keys  # 如需中英文映射可在此处理
                    ttk.Label(frame, text="城市", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    city_var = tk.StringVar(value=data.get("city", city_keys[0]))
                    city_combo = ttk.Combobox(frame, textvariable=city_var, values=city_display, state="readonly", width=input_width)
                    city_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["city"] = city_var
                    row += 1
                    # depth
                    ttk.Label(frame, text="深度", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    depth_var = tk.StringVar(value=str(data.get("depth", 1)))
                    depth_spin = tk.Spinbox(frame, from_=1, to=10, textvariable=depth_var, width=input_width)
                    depth_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["depth"] = depth_var
                    row += 1
                    # 逢魔点等待时间
                    ttk.Label(frame, text="逢魔点等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    wait_var = tk.StringVar(value=str(data.get("find_point_wait_time", 1.5)))
                    wait_spin = tk.Spinbox(frame, from_=0.5, to=5, increment=0.1, textvariable=wait_var, width=input_width)
                    wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["find_point_wait_time"] = wait_var
                    row += 1
                    # 起步等待时间
                    ttk.Label(frame, text="起步等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    wait_map_time_var = tk.StringVar(value=str(data.get("wait_map_time", 0.5)))
                    start_wait_spin = tk.Spinbox(frame, from_=0.5, to=1.5, increment=0.1, textvariable=wait_map_time_var, width=input_width)
                    start_wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["wait_map_time"] = wait_map_time_var
                    row += 1
                    # UI等待时间配置项
                    ui_wait_value = data.get("wait_ui_time", "0.3")
                    ttk.Label(frame, text="UI等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    wait_ui_var = tk.StringVar(value=str(ui_wait_value))
                    wait_ui_spin = tk.Spinbox(frame, from_=0.1, to=1.0, increment=0.1, 
                                            textvariable=wait_ui_var, width=input_width, format="%.1f")
                    wait_ui_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["wait_ui_time"] = wait_ui_var
                    row += 1
                    # 全灭是否复活
                    revive_val = data.get("revive_on_all_dead", False)
                    if isinstance(revive_val, str):
                        revive_val = revive_val.lower() == "true"
                    revive_var = tk.StringVar(value="是" if revive_val else "否")
                    ttk.Label(frame, text="全灭是否复活", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    revive_combo = ttk.Combobox(frame, textvariable=revive_var, values=["是", "否"], state="readonly", width=input_width)
                    revive_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["revive_on_all_dead"] = revive_var
                    row += 1
                    
                    # 其余字段
                    for k, v in data.items():
                        if k in ("rest_in_inn", "vip_cure", "city", "depth", "find_point_wait_time", "wait_map_time", "wait_ui_time", "revive_on_all_dead"):
                            continue
                        ttk.Label(frame, text=k, width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                        var = tk.StringVar(value=str(v))
                        entry = ttk.Entry(frame, textvariable=var, width=input_width)
                        entry.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                        vars_dict[k] = var
                        row += 1
                    # 怪物配置区块放在最底部
                    monster_editor = MonsterEditor(frame, city_var)
                    monster_editor.grid(row=row, column=0, columnspan=2, sticky='nsew', padx=5, pady=10)
                    frame.rowconfigure(row, weight=1)
                    frame.columnconfigure(0, weight=1)
                    frame.columnconfigure(1, weight=1)
                    vars_dict["monster_editor"] = monster_editor
                    row += 1
                elif fname == "battle.yaml":
                    # 战斗配置特殊处理
                    label_width = 14
                    input_width = 20
                    
                    # 配置项映射
                    CONFIG_ITEMS = {
                        # 基础配置
                        'wait_time': {'display_name': '基础等待时间', 'description': '基础等待时间(秒)', 'step': 0.1},
                        'wait_drag_time': {'display_name': '拖拽等待时间', 'description': '拖拽等待时间(秒)', 'step': 0.1},
                        'wait_ui_time': {'display_name': 'UI等待时间', 'description': 'UI等待时间(秒)', 'step': 0.1},
                        'battle_recognition_time': {'display_name': '战斗识别时间', 'description': '战斗识别时间(秒)', 'step': 0.5},
                        
                        # 战斗相关timeout配置
                        'auto_battle_timeout': {'display_name': '自动战斗超时', 'description': '自动战斗超时时间(秒)', 'step': 1.0},
                        'check_dead_timeout': {'display_name': '检查死亡超时', 'description': '检查角色死亡超时时间(秒)', 'step': 0.5},
                        'reset_round_timeout': {'display_name': '重置回合超时', 'description': '重置回合超时时间(秒)', 'step': 1.0},
                        'exit_battle_timeout': {'display_name': '退出战斗超时', 'description': '退出战斗超时时间(秒)', 'step': 1.0},
                        'transform_timeout': {'display_name': '切换形态超时', 'description': '切换形态超时时间(秒)', 'step': 1.0},
                        'cast_sp_timeout': {'display_name': 'SP技能超时', 'description': '释放SP技能超时时间(秒)', 'step': 1.0},
                        'cast_skill_timeout': {'display_name': '技能超时', 'description': '释放技能超时时间(秒)', 'step': 1.0},
                        'attack_timeout': {'display_name': '攻击超时', 'description': '攻击超时时间(秒)', 'step': 0.5},
                        'wait_in_round_timeout': {'display_name': '等待回合超时', 'description': '等待回合超时时间(秒)', 'step': 1.0},
                        'wait_done_timeout': {'display_name': '等待结束超时', 'description': '等待战斗结束超时时间(秒)', 'step': 5.0},
                        'boost_timeout': {'display_name': '全体加成超时', 'description': '全体加成超时时间(秒)', 'step': 1.0},
                        'switch_all_timeout': {'display_name': '全员交替超时', 'description': '全员交替超时时间(秒)', 'step': 0.5},
                        'find_enemy_timeout': {'display_name': '识别敌人超时', 'description': '识别敌人超时时间(秒)', 'step': 0.5},
                    }
                    
                    for k, v in data.items():
                        if k in CONFIG_ITEMS:
                            display_name, description = CONFIG_ITEMS[k]['display_name'], CONFIG_ITEMS[k]['description']
                            # 创建标签
                            label = ttk.Label(frame, text=display_name, width=label_width, anchor="w")
                            label.grid(row=row, column=0, sticky='w', padx=5, pady=3)
                            
                            # 创建输入框
                            if isinstance(v, bool):
                                # 布尔值使用Checkbutton
                                var = tk.BooleanVar(value=v)
                                check = ttk.Checkbutton(frame, variable=var)
                                check.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                            else:
                                # 数值使用Spinbox
                                var = tk.DoubleVar(value=v)
                                # 根据配置项类型设置不同的步进值
                                if k in CONFIG_ITEMS and 'step' in CONFIG_ITEMS[k]:
                                    step = CONFIG_ITEMS[k]['step']
                                    # 根据步进值设置合适的范围
                                    if step >= 1.0:
                                        from_ = 1.0
                                        to = 100.0
                                    elif step >= 0.5:
                                        from_ = 0.5
                                        to = 10.0
                                    else:
                                        from_ = 0.1
                                        to = 2.0
                                    spin = tk.Spinbox(frame, from_=from_, to=to, increment=step,
                                                    textvariable=var, width=input_width, format="%.1f")
                                else:
                                    # 默认步进值
                                    spin = tk.Spinbox(frame, from_=0.1, to=2.0, increment=0.1,
                                                    textvariable=var, width=input_width, format="%.1f")
                                spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                            
                            # 添加说明标签
                            desc_label = ttk.Label(frame, text=description, font=("TkDefaultFont", 8), 
                                                 foreground="gray")
                            desc_label.grid(row=row, column=2, padx=5, pady=3, sticky='w')
                            
                            vars_dict[k] = var
                            row += 1
                        else:
                            # 未知配置项使用默认处理
                            ttk.Label(frame, text=k, width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                            var = tk.StringVar(value=str(v))
                            entry = ttk.Entry(frame, textvariable=var, width=input_width)
                            entry.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                            vars_dict[k] = var
                            row += 1
                else:
                    for k, v in data.items():
                        ttk.Label(frame, text=k).grid(row=row, column=0, sticky='w', padx=5, pady=3)
                        var = tk.StringVar(value=str(v))
                        entry = ttk.Entry(frame, textvariable=var, width=40)
                        entry.grid(row=row, column=1, padx=5, pady=3)
                        vars_dict[k] = var
                        row += 1
            self.config_vars[fname] = vars_dict
        save_btn = ttk.Button(self.settings_frame, text="保存设置", command=self.save_settings)
        save_btn.pack(pady=10)
        self.settings_notebook.select(0)
        # 调试：打印控件对象和id
        if "fengmo.yaml" in self.config_vars:
            print("rest_in_inn控件对象：", self.config_vars["fengmo.yaml"].get("rest_in_inn"), id(self.config_vars["fengmo.yaml"].get("rest_in_inn")))
            print("vip_cure控件对象：", self.config_vars["fengmo.yaml"].get("vip_cure"), id(self.config_vars["fengmo.yaml"].get("vip_cure")))

    def show_main(self):
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill=tk.BOTH, expand=True)

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

    def on_start(self):
        if self.fengmo_process and self.fengmo_process.is_alive():
            messagebox.showinfo("提示", "玩法已在运行中！")
            return
        
        # 在启动玩法前检查并清理日志目录
        from utils.logger import cleanup_logs_dir
        cleanup_logs_dir()
        
        self.start_btn.config(state=tk.DISABLED)
        self.farming_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 正在初始化...")
        self.append_log("逢魔玩法进程启动中...")
        self.update_report_data("")
        self.log_queue = multiprocessing.Queue()
        log_level = self.log_level_var.get()  # 获取最新日志级别
        self.fengmo_process = multiprocessing.Process(target=run_fengmo_main, args=(self.log_queue, log_level))
        self.fengmo_process.start()
        self.status_label.config(text="状态: 逢魔玩法运行中... (点击停止可终止)")
        self.after(100, self.poll_log_queue)

    def on_start_farming(self):
        """
        启动刷野玩法
        """
        if self.fengmo_process and self.fengmo_process.is_alive():
            messagebox.showinfo("提示", "玩法已在运行中！")
            return
        
        # 在启动玩法前检查并清理日志目录
        from utils.logger import cleanup_logs_dir
        cleanup_logs_dir()
        
        self.start_btn.config(state=tk.DISABLED)
        self.farming_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 正在初始化...")
        self.append_log("刷野玩法进程启动中...")
        self.update_report_data("")
        self.log_queue = multiprocessing.Queue()
        log_level = self.log_level_var.get()  # 获取最新日志级别
        self.fengmo_process = multiprocessing.Process(target=run_farming_main, args=(self.log_queue, log_level))
        self.fengmo_process.start()
        self.status_label.config(text="状态: 刷野玩法运行中... (点击停止可终止)")
        self.after(100, self.poll_log_queue)

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
        if self.fengmo_process and self.fengmo_process.is_alive():
            self.fengmo_process.terminate()
            self.fengmo_process.join()
            self.status_label.config(text="状态: 已停止")
            self.start_btn.config(state=tk.NORMAL)
            self.farming_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.logger.info("玩法进程已终止")
            self.append_log("玩法进程已终止")
        else:
            self.status_label.config(text="状态: 未运行")
            self.start_btn.config(state=tk.NORMAL)
            self.farming_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.append_log("玩法进程未运行")

    def save_settings(self):
        """保存所有配置到文件"""
        config_dir = get_config_dir()
        for fname, _ in CONFIG_FILES:
            if fname == "fengmo_cities.yaml":
                continue
            fpath = os.path.join(config_dir, fname)
            if fname in self.config_vars:
                vars_dict = self.config_vars[fname]
                data = {}
                # 读取原始配置（用于类型还原）
                orig_data = {}
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        try:
                            orig_data = yaml.safe_load(f) or {}
                        except Exception:
                            orig_data = {}
                for key, var in vars_dict.items():
                    if not hasattr(var, "get"):
                        continue
                    value = var.get()
                    if fname == "fengmo.yaml":
                        if key in ["rest_in_inn", "vip_cure", "revive_on_all_dead"]:
                            data[key] = value == "是"
                        elif key in ["depth"]:
                            data[key] = int(value)
                        elif key in ["find_point_wait_time", "wait_map_time", "wait_ui_time"]:
                            data[key] = float(value)
                        else:
                            data[key] = value
                    else:
                        orig_val = orig_data.get(key, None)
                        if isinstance(orig_val, bool):
                            data[key] = value == "True" or value == "是"
                        elif isinstance(orig_val, int):
                            try:
                                data[key] = int(value)
                            except Exception:
                                data[key] = value
                        elif isinstance(orig_val, float):
                            try:
                                data[key] = float(value)
                            except Exception:
                                data[key] = value
                        else:
                            data[key] = value
                with open(fpath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                logger.info(f"已保存配置: {fname}")
        messagebox.showinfo("提示", "所有设置已保存！")
        self.append_log("所有设置已保存！")

    def on_close(self):
        # 移除GUI Handler，防止内存泄漏
        self.logger.handlers = [h for h in self.logger.handlers if h.__class__.__name__ != 'GuiLogHandler']
        if self.fengmo_process and self.fengmo_process.is_alive():
            if not messagebox.askokcancel("退出", "玩法正在运行，确定要强制退出吗？"):
                return
            self.fengmo_process.terminate()
            self.fengmo_process.join()
            self.append_log("玩法进程已终止")
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
    fix_stdio_if_none()
    
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
        ocr_handler = OCRHandler(device_manager,show_logger=True)
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
        ocr_handler = OCRHandler(device_manager,show_logger=True)
        
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