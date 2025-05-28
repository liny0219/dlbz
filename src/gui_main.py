import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import yaml
import os
import multiprocessing
import logging
from core.device_manager import DeviceManager
from core.ocr_handler import OCRHandler
from modes.fengmo import FengmoMode
from utils import logger
from common.config import get_config_dir
import traceback

version = "v0.9"

CONFIG_FILES = [
    ("fengmo.yaml", "逢魔玩法"),
    ("device.yaml", "设备"),
    ("settings.yaml", "全局设置"),
    ("logging.yaml", "日志"),
    ("game.yaml", "游戏"),
    ("ocr.yaml", "OCR"),
]
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class FengmoGUI(tk.Tk):
    """
    主窗口，包含主界面和设置界面，玩法主流程用子进程启动/终止，支持日志级别动态调整
    """
    def __init__(self):
        super().__init__()
        self.title(f"旅人休息站.免费脚本 {version}")
        self.geometry("800x600")
        self.minsize(700, 400)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.logger = logger
        self.fengmo_process = None
        self.log_queue = None
        self.log_level_var = tk.StringVar(value="INFO")
        self._build_menu()
        self._build_main_frame()
        self._build_settings_frame()
        self.show_main()

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
        self.start_btn = ttk.Button(self.main_frame, text="开始玩法", command=self.on_start)
        self.start_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.stop_btn = ttk.Button(self.main_frame, text="停止玩法", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.status_label = ttk.Label(self.main_frame, text="状态: 等待启动")
        self.status_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        ttk.Label(self.main_frame, text="日志级别:").grid(row=0, column=3, padx=5, sticky="e")
        self.loglevel_combo = ttk.Combobox(self.main_frame, textvariable=self.log_level_var, values=LOG_LEVELS, width=10, state="readonly")
        self.loglevel_combo.grid(row=0, column=4, padx=5, sticky="e")
        # 玩法统计区块
        self.report_frame = ttk.LabelFrame(self.main_frame, text="玩法统计", padding=(5, 5))
        self.report_frame.grid(row=1, column=0, columnspan=5, padx=10, pady=5, sticky="nsew")
        self.report_text = tk.Text(self.report_frame, height=7, width=120, state='disabled', font=("Consolas", 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        # 日志区块
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=120, height=20, state='disabled', font=("Consolas", 10))
        self.log_text.grid(row=2, column=0, columnspan=5, padx=10, pady=5, sticky="nsew")
        # 拉伸自适应
        self.main_frame.rowconfigure(1, weight=0)  # 统计区块高度固定
        self.main_frame.rowconfigure(2, weight=1)  # 日志区块随窗体拉伸
        for i in range(5):
            self.main_frame.columnconfigure(i, weight=1)

    def _build_settings_frame(self):
        self.settings_frame = ttk.Frame(self)
        self.settings_notebook = ttk.Notebook(self.settings_frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True)
        self.config_vars = {}
        config_dir = get_config_dir()
        for fname, label in CONFIG_FILES:
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
                    label_width = 10  # 标签宽度
                    input_width = 20  # 输入控件宽度
                    # rest_in_inn
                    ttk.Label(frame, text="旅馆休息", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    rest_var = tk.StringVar(value="是" if data.get("rest_in_inn", True) else "否")
                    rest_combo = ttk.Combobox(frame, textvariable=rest_var, values=["是", "否"], state="readonly", width=input_width)
                    rest_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["rest_in_inn"] = rest_var
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
                    # 其余字段
                    for k, v in data.items():
                        if k in ("rest_in_inn", "city", "depth"):
                            continue
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
        save_btn = ttk.Button(self.settings_frame, text="保存所有设置", command=self.save_settings)
        save_btn.pack(pady=10)

    def show_main(self):
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill=tk.BOTH, expand=True)

    def on_start(self):
        if self.fengmo_process and self.fengmo_process.is_alive():
            messagebox.showinfo("提示", "玩法已在运行中！")
            return
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 正在初始化...")
        self.append_log("玩法进程启动中...")
        self.update_report_data("")
        self.log_queue = multiprocessing.Queue()
        log_level = self.log_level_var.get()
        self.fengmo_process = multiprocessing.Process(target=run_fengmo_main, args=(self.log_queue, log_level))
        self.fengmo_process.start()
        self.status_label.config(text="状态: 玩法运行中... (点击停止可终止)")
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
            self.stop_btn.config(state=tk.DISABLED)
            self.logger.info("玩法进程已终止")
            self.append_log("玩法进程已终止")
        else:
            self.status_label.config(text="状态: 未运行")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.append_log("玩法进程未运行")

    def save_settings(self):
        config_dir = get_config_dir()
        for fname, vars_dict in self.config_vars.items():
            fpath = os.path.join(config_dir, fname)
            data = {}
            for k, var in vars_dict.items():
                v = var.get()
                # 针对逢魔玩法特殊处理
                if fname == "fengmo.yaml":
                    if k == "rest_in_inn":
                        v = True if v == "是" else False
                    elif k == "depth":
                        try:
                            v = int(v)
                        except Exception:
                            v = 1
                    elif k == "city":
                        v = str(v)
                else:
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
                    else:
                        try:
                            if "." in v:
                                v = float(v)
                            else:
                                v = int(v)
                        except Exception:
                            pass
                data[k] = v
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True)
                self.logger.info(f"已保存: {fname}")
            except Exception as e:
                self.logger.error(f"保存 {fname} 失败: {e}")
        messagebox.showinfo("提示", "所有设置已保存！")
        self.append_log("所有设置已保存！")

    def on_close(self):
        if self.fengmo_process and self.fengmo_process.is_alive():
            if not messagebox.askokcancel("退出", "玩法正在运行，确定要强制退出吗？"):
                return
            self.fengmo_process.terminate()
            self.fengmo_process.join()
            self.append_log("玩法进程已终止")
        self.destroy()
        os._exit(0)

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

def run_fengmo_main(log_queue, log_level):
    try:
        import logging
        logger = logging.getLogger("dldbz")  # 保证主进程和子进程logger name一致
        # 兼容字符串和数字
        if isinstance(log_level, str):
            log_level_value = getattr(logging, log_level.upper(), logging.INFO)
        else:
            log_level_value = log_level
        logger.setLevel(log_level_value)
        if logger.hasHandlers():
            logger.handlers.clear()
        handler = QueueLogHandler(log_queue)
        handler.setLevel(logging.NOTSET)  # 确保不过滤任何日志
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
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
        fengmo_mode = FengmoMode(device_manager, ocr_handler)
        # monkeypatch report_data: 发送统计到主进程
        def report_data_patch(self):
            lines = [
                f"当前轮数: {self.turn_count}",
                f"当前轮次用时: {self.turn_time}分钟",
                f"当前成功次数: {self.total_finished_count}",
                f"当前成功用时: {self.total_finished_time}分钟",
                f"当前成功平均用时: {self.avg_finished_time}分钟",
                f"当前失败平均用时: {self.avg_fail_time}分钟",
            ]
            report_str = '\n'.join(lines)
            log_queue.put("REPORT_DATA__" + report_str)
            logger.info("[report_data]" + report_str.replace("\n", " | "))
        from modes.fengmo import StateData
        StateData.report_data = report_data_patch
        fengmo_mode.run()
    except Exception as e:
        try:
            if log_queue:
                log_queue.put(f"[子进程异常] {e}")
        except Exception:
            pass

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows兼容
    app = FengmoGUI()
    app.mainloop()
