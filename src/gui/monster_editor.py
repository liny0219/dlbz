import tkinter as tk
from tkinter import ttk
import yaml
import os
import subprocess
from common.config import get_config_dir
import logging
import tkinter.messagebox as mbox
import tkinter.filedialog as filedialog

class MonsterEditor(ttk.LabelFrame):
    def __init__(self, parent, city_var, *args, **kwargs):
        super().__init__(parent, text="怪物配置", padding=(5, 5), *args, **kwargs)
        self.city_var = city_var
        self.monsters = []
        self.selecting_monster = False
        self._build_widgets()
        self.load_monsters(self.city_var.get())
        self.refresh_monster_list()
        self.city_var.trace_add('write', self.on_city_change)

    def _build_widgets(self):
        # 先全部weight=0
        for i in range(5):
            self.rowconfigure(i, weight=0)
        self.rowconfigure(1, weight=1)  # 识别特征点（Text）填充剩余高度
        self.columnconfigure(0, weight=0)  # Listbox
        self.columnconfigure(1, weight=0)  # 标签
        self.columnconfigure(2, weight=1)  # 编辑区
        # Listbox
        self.monster_list = tk.Listbox(self, height=5, width=30, exportselection=0)
        self.monster_list.grid(row=0, column=0, rowspan=5, padx=5, pady=3, sticky='nsew')
        label_width = 20
        # 名称
        ttk.Label(self, text="名称", width=label_width, anchor='w').grid(row=0, column=1, sticky='w')
        self.monster_name_var = tk.StringVar()
        self.monster_name_entry = ttk.Entry(self, textvariable=self.monster_name_var, width=20)
        self.monster_name_entry.grid(row=0, column=2, padx=5, pady=3, sticky='ew')
        # 识别特征点
        ttk.Label(self, text="识别特征点(points)", width=label_width, anchor='w').grid(row=1, column=1, sticky='nw')
        points_tip = "一行一个点: x,y,color,range  例: 100,200,#FF0000,3"
        points_tip_label = tk.Label(self, text=points_tip, fg='gray', anchor='w', wraplength=400, justify='left')
        points_tip_label.grid(row=2, column=1, columnspan=2, sticky='ew', padx=5)
        self.monster_points_text = tk.Text(self, width=30, height=4)
        self.monster_points_text.grid(row=1, column=2, padx=5, pady=3, sticky='nsew')  # 只占row=1
        # 战斗配置
        ttk.Label(self, text="战斗配置", width=20, anchor='w').grid(row=3, column=1, sticky='w')
        self.monster_battle_var = tk.StringVar()
        self.monster_battle_entry = ttk.Entry(self, textvariable=self.monster_battle_var, width=20)
        self.monster_battle_entry.grid(row=3, column=2, padx=5, pady=3, sticky='ew')
        # 新增按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=3, padx=2, pady=3, sticky='w')
        edit_btn = ttk.Button(btn_frame, text="编辑", width=6, command=self.on_edit_battle_file)
        edit_btn.pack(side=tk.LEFT, padx=(0, 2))
        help_btn = ttk.Button(btn_frame, text="说明", width=6, command=self.on_battle_help)
        help_btn.pack(side=tk.LEFT, padx=(0, 2))
        set_btn = ttk.Button(btn_frame, text="设置", width=6, command=self.on_set_battle_file)
        set_btn.pack(side=tk.LEFT)
        # 按钮区优化
        btn_frame2 = ttk.Frame(self)
        btn_frame2.grid(row=4, column=1, columnspan=3, padx=5, pady=3, sticky='w')
        self.add_btn = ttk.Button(btn_frame2, text="添加", width=8, command=self.on_add)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.del_btn = ttk.Button(btn_frame2, text="删除", width=8, command=self.on_del)
        self.del_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.modify_btn = ttk.Button(btn_frame2, text="修改", width=8, command=self.on_modify)
        self.modify_btn.pack(side=tk.LEFT)
        # 在修改按钮后添加tip文案
        self.modify_tip_label = tk.Label(btn_frame2, text="保存路径先点击修改生效", fg="gray", anchor="w")
        self.modify_tip_label.pack(side=tk.LEFT, padx=(8, 0))
        # 事件绑定
        self.monster_list.bind('<<ListboxSelect>>', self.on_select)
        self.monster_name_var.trace_add('write', self.on_edit)
        self.monster_battle_var.trace_add('write', self.on_edit)
        self.monster_points_text.bind('<KeyRelease>', lambda e: self.on_edit())
        # 新增：编辑区获得焦点时自动恢复Listbox选中态
        self.monster_points_text.bind('<FocusIn>', self.restore_listbox_selection)
        self.monster_name_entry.bind('<FocusIn>', self.restore_listbox_selection)
        self.monster_battle_entry.bind('<FocusIn>', self.restore_listbox_selection)

    def get_monsters_for_city(self, city_name):
        cities_path = os.path.join(get_config_dir(), "fengmo_cities.yaml")
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities_data = yaml.safe_load(f) or {}
        return cities_data.get("cities", {}).get(city_name, {}).get("monsters", [])

    def load_monsters(self, city_name):
        self.monsters = self.get_monsters_for_city(city_name)

    def refresh_monster_list(self, keep_selection=True):
        cur_idx = self.monster_list.curselection()
        self.monster_list.delete(0, tk.END)
        for m in self.monsters:
            self.monster_list.insert(tk.END, m.get("name", "未命名"))
        if keep_selection and cur_idx:
            self.monster_list.selection_set(cur_idx[0])

    def on_select(self, evt):
        self.selecting_monster = True
        idx = self.monster_list.curselection()
        if not idx:
            self.selecting_monster = False
            return
        self._last_selected_idx = idx[0]  # 记录上一次选中项
        m = self.monsters[idx[0]]
        self.monster_name_var.set(m.get("name", ""))
        pts = m.get("points", [])
        if not isinstance(pts, list):
            pts = []
        pts_strs = []
        for pt in pts:
            if isinstance(pt, (list, tuple)) and len(pt) == 4:
                pts_strs.append(f"{pt[0]},{pt[1]},{pt[2]},{pt[3]}")
        self.monster_points_text.delete(1.0, tk.END)
        self.monster_points_text.insert(tk.END, "\n".join(pts_strs))
        battle_val = m.get("battle_config", "")
        if battle_val is None:
            battle_val = ""
        self.monster_battle_var.set(str(battle_val))
        self.selecting_monster = False

    def on_add(self):
        logging.info(f"[MonsterEditor] on_add: name={self.monster_name_var.get()}, points={self.monster_points_text.get(1.0, tk.END).strip()}, battle_config={self.monster_battle_var.get()}")
        # 读取当前编辑区内容
        name = self.monster_name_var.get()
        pts_lines = self.monster_points_text.get(1.0, tk.END).strip().splitlines()
        pts = []
        for line in pts_lines:
            try:
                x, y, color, r = line.split(",")
                pts.append([int(x), int(y), color.strip(), int(r)])
            except Exception as e:
                logging.warning(f"[MonsterEditor] on_add: 解析点失败: {line}, err={e}")
                continue
        battle_config = self.monster_battle_var.get()
        # 构造新怪物
        new_monster = {"name": name or "新怪物", "points": pts, "battle_config": battle_config}
        self.monsters.append(new_monster)
        logging.info(f"[MonsterEditor] on_add: 新怪物已添加: {new_monster}")
        self.save_to_yaml()
        self.refresh_monster_list()
        self.monster_list.selection_clear(0, tk.END)
        self.monster_list.selection_set(tk.END)
        self.on_select(None)

    def on_del(self):
        idx = self.monster_list.curselection()
        if not idx:
            return
        i = idx[0]
        self.monster_list.delete(i)
        self.monsters.pop(i)
        self.monster_name_var.set("")
        self.monster_points_text.delete(1.0, tk.END)
        self.monster_battle_var.set("")
        self.save_to_yaml()
        self.refresh_monster_list()
        # 删除后自动选中下一个或上一个
        count = len(self.monsters)
        if count > 0:
            next_idx = min(i, count - 1)
            self.monster_list.selection_set(next_idx)
            self.on_select(None)

    def on_edit(self, *args):
        # 不再自动同步到self.monsters，避免和on_modify冲突
        pass

    def on_modify(self):
        idx = self.monster_list.curselection()
        if not idx:
            mbox.showwarning("提示", "请先在左侧列表中选中要修改的怪物！")
            logging.warning("[MonsterEditor] on_modify: 未选中怪物")
            return
        i = idx[0]
        # 读取当前编辑区内容并同步到self.monsters[i]
        name = self.monster_name_var.get()
        pts_lines = self.monster_points_text.get(1.0, tk.END).strip().splitlines()
        pts = []
        for line in pts_lines:
            try:
                x, y, color, r = line.split(",")
                pts.append([int(x), int(y), color.strip(), int(r)])
            except Exception as e:
                logging.warning(f"[MonsterEditor] on_modify: 解析点失败: {line}, err={e}")
                continue
        battle_config = self.monster_battle_var.get()
        before = self.monsters[i].copy()
        self.monsters[i] = {"name": name, "points": pts, "battle_config": battle_config}
        logging.info(f"[MonsterEditor] on_modify: 修改前: {before}, 修改后: {self.monsters[i]}")
        self.save_to_yaml()
        self.refresh_monster_list()
        self.monster_list.selection_clear(0, tk.END)
        self.monster_list.selection_set(i)
        # 不自动调用on_select，防止内容被旧值覆盖

    def on_city_change(self, *args):
        city = self.city_var.get()
        self.load_monsters(city)
        self.refresh_monster_list()
        self.monster_name_var.set("")
        self.monster_points_text.delete(1.0, tk.END)
        self.monster_battle_var.set("")

    def on_edit_battle_file(self):
        # 获取当前战斗配置文件名
        fname = self.monster_battle_var.get().strip()
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

    def on_battle_help(self):
        # 打开config/readme.txt
        config_dir = get_config_dir()
        help_path = os.path.join(config_dir, 'readme.txt')
        if not os.path.exists(help_path):
            mbox.showwarning("提示", f"未找到文件: {help_path}")
            return
        try:
            if os.name == 'nt':
                os.startfile(help_path)
            else:
                subprocess.Popen(['xdg-open', help_path])
        except Exception as e:
            mbox.showerror("错误", f"无法打开说明文件: {help_path}\n{e}")
            print(f"无法打开说明文件: {help_path}, {e}")

    def on_set_battle_file(self):
        config_dir = get_config_dir()
        # 默认打开battle_scripts目录，但可选任意文件
        default_dir = os.path.join(config_dir, 'battle_scripts')
        filetypes = [("文本文件", "*.txt"), ("所有文件", "*.*")]
        filepath = filedialog.askopenfilename(title="选择战斗配置文件", initialdir=default_dir, filetypes=filetypes)
        if filepath:
            self.monster_battle_var.set(filepath)

    def save_to_yaml(self):
        cities_path = os.path.join(get_config_dir(), "fengmo_cities.yaml")
        try:
            with open(cities_path, 'r', encoding='utf-8') as f:
                all_data = yaml.safe_load(f) or {}
            city = self.city_var.get()
            if "cities" not in all_data:
                all_data["cities"] = {}
            if city not in all_data["cities"]:
                all_data["cities"][city] = {}
            all_data["cities"][city]["monsters"] = self.monsters
            with open(cities_path, 'w', encoding='utf-8') as f:
                yaml.dump(all_data, f, allow_unicode=True)
            logging.info(f"[MonsterEditor] save_to_yaml: 已保存到{cities_path}, city={city}, monsters={self.monsters}")
        except Exception as e:
            logging.error(f"[MonsterEditor] save_to_yaml: 保存失败: {e}")

    def restore_listbox_selection(self, event=None):
        # 如果当前没有选中项，自动选中上一次的项
        if not self.monster_list.curselection() and hasattr(self, '_last_selected_idx'):
            idx = self._last_selected_idx
            if idx is not None and 0 <= idx < len(self.monsters):
                self.monster_list.selection_set(idx) 