from sys import maxsize
import tkinter as tk
import tkinter.messagebox as mbox
from tkinter import ttk, messagebox, filedialog
import os
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type
from gui.monster_editor import MonsterEditor
from gui.monster_pos_editor import MonsterPosEditor
from common.config import config

class FengmoSettingsTab(ttk.Frame):
    def __init__(self, master, config_data, config_filename):
        super().__init__(master)
        self.config_filename = config_filename
        label_width = 14
        input_width = 20
        row = 0

        # 常规配置区
        config_frame = ttk.Frame(self)
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # 旅馆休息
        rest_val = config_data.get("rest_in_inn", False)
        if isinstance(rest_val, str):
            rest_val = rest_val.lower() == "true"
        self.rest_var = tk.StringVar(value="是" if rest_val else "否")
        ttk.Label(config_frame, text="旅馆休息", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        rest_combo = ttk.Combobox(config_frame, textvariable=self.rest_var, values=["是", "否"], state="readonly", width=input_width)
        rest_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 月卡恢复
        vip_cure_val = config_data.get("vip_cure", False)
        if isinstance(vip_cure_val, str):
            vip_cure_val = vip_cure_val.lower() == "true"
        self.vip_cure_var = tk.StringVar(value="是" if vip_cure_val else "否")
        ttk.Label(config_frame, text="月卡恢复", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        vip_cure_combo = ttk.Combobox(config_frame, textvariable=self.vip_cure_var, values=["是", "否"], state="readonly", width=input_width)
        vip_cure_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 城市
        city_keys = list(config.fengmo_cities.keys())
        city_display = city_keys
        self.city_var = tk.StringVar(value=config_data.get("city", city_keys[0]))
        ttk.Label(config_frame, text="城市", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        city_combo = ttk.Combobox(config_frame, textvariable=self.city_var, values=city_display, state="readonly", width=input_width)
        city_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 深度
        self.depth_var = tk.StringVar(value=str(config_data.get("depth", 1)))
        ttk.Label(config_frame, text="深度", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        depth_spin = tk.Spinbox(config_frame, from_=1, to=10, textvariable=self.depth_var, width=input_width)
        depth_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 逢魔点等待时间
        self.wait_var = tk.StringVar(value=str(config_data.get("find_point_wait_time", 1.5)))
        ttk.Label(config_frame, text="逢魔点等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        wait_spin = tk.Spinbox(config_frame, from_=0.1, to=5, increment=0.1, textvariable=self.wait_var, width=input_width)
        wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 起步等待时间
        self.wait_map_time_var = tk.StringVar(value=str(config_data.get("wait_map_time", 0.5)))
        ttk.Label(config_frame, text="起步等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        start_wait_spin = tk.Spinbox(config_frame, from_=0.5, to=1.5, increment=0.1, textvariable=self.wait_map_time_var, width=input_width)
        start_wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # UI等待时间
        self.wait_ui_var = tk.StringVar(value=str(config_data.get("wait_ui_time", "0.3")))
        ttk.Label(config_frame, text="UI等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        wait_ui_spin = tk.Spinbox(config_frame, from_=0.1, to=1.0, increment=0.1, textvariable=self.wait_ui_var, width=input_width, format="%.1f")
        wait_ui_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1

        # 默认战斗配置
        self.default_battle_config_var = tk.StringVar(value=str(config_data.get("default_battle_config", "")))
        ttk.Label(config_frame, text="默认战斗配置", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        default_battle_entry = ttk.Entry(config_frame, textvariable=self.default_battle_config_var, width=input_width)
        default_battle_entry.grid(row=row, column=1, padx=5, pady=3, sticky='w')

        def select_battle_file():
            fpath = filedialog.askopenfilename(title="选择默认战斗配置文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
            if fpath:
                self.default_battle_config_var.set(fpath)
        edit_btn = ttk.Button(config_frame, text="编辑", width=6, command=self.on_edit_battle_file)
        edit_btn.grid(row=row, column=2, padx=5, pady=3, sticky='w')
        select_btn = ttk.Button(config_frame, text="浏览", command=select_battle_file)
        select_btn.grid(row=row, column=3, padx=5, pady=3, sticky='w')
        row += 1

        # 其余字段
        self.extra_vars = {}
        for k, v in config_data.items():
            if k in ("rest_in_inn", "vip_cure", "city", "depth", "find_point_wait_time", "wait_map_time", "wait_ui_time", "default_battle_config"):
                continue
            var = tk.StringVar(value=str(v))
            ttk.Label(config_frame, text=k, width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(config_frame, textvariable=var, width=input_width)
            entry.grid(row=row, column=1, padx=5, pady=3, sticky='w')
            self.extra_vars[k] = var
            row += 1

        # 保存按钮
        save_btn = ttk.Button(self, text="保存设置", command=self.save_settings)
        save_btn.pack(pady=10)

        # 怪物设置
        monster_frame = ttk.LabelFrame(self, text="怪物设置")
        monster_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        monster_frame.columnconfigure(0, weight=1, minsize=30)  # 怪物点坐标区 1/4
        monster_frame.columnconfigure(1, weight=3, minsize=120)  # 怪物配置区 3/4
        monster_frame.rowconfigure(0, weight=1)
        self.monster_pos_editor = MonsterPosEditor(monster_frame, self.city_var)
        self.monster_pos_editor.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=5)
        self.monster_editor = MonsterEditor(monster_frame, self.city_var)
        self.monster_editor.grid(row=0, column=1, sticky="nsew", padx=(2, 5), pady=5)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def get_config_data(self):
        data = {
            "rest_in_inn": self.rest_var.get(),
            "vip_cure": self.vip_cure_var.get(),
            "city": self.city_var.get(),
            "depth": self.depth_var.get(),
            "find_point_wait_time": self.wait_var.get(),
            "wait_map_time": self.wait_map_time_var.get(),
            "wait_ui_time": self.wait_ui_var.get(),
            "default_battle_config": self.default_battle_config_var.get(),
        }
        for k, var in self.extra_vars.items():
            data[k] = var.get()
        # 怪物设置可扩展
        return data

    def save_settings(self):
        config_dir = get_config_dir()
        fpath = os.path.join(config_dir, self.config_filename)
        raw_data = self.get_config_data()
        save_yaml_with_type(fpath, raw_data)
        messagebox.showinfo("提示", "设置已保存！") 

    def on_edit_battle_file(self):
        # 获取当前战斗配置文件名
        fname = self.default_battle_config_var.get().strip()
        if not fname:
            mbox.showwarning("提示", "请先填写战斗配置文件名！")
            return
        config_dir = get_config_dir()
        # 1. 先直接用填写的路径（绝对或相对）
        battle_path = fname
        if not os.path.isabs(battle_path):
            # 2. 如果不是绝对路径，尝试config_dir下
            try_path = os.path.join(config_dir, fname)
            if os.path.exists(try_path):
                battle_path = try_path
            else:
                # 3. 再尝试battle_scripts下
                try_path2 = os.path.join(config_dir, 'battle_scripts', fname)
                if os.path.exists(try_path2):
                    battle_path = try_path2
        if not os.path.exists(battle_path):
            mbox.showwarning("提示", f"未找到文件: {battle_path}")
            return
        try:
            if os.name == 'nt':
                os.startfile(battle_path)
            else:
                subprocess.Popen(['xdg-open', battle_path])
        except Exception as e:
            mbox.showerror("错误", f"无法打开文件: {battle_path}\n{e}")
            print(f"无法打开文件: {battle_path}, {e}")
