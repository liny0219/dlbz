import tkinter as tk
from tkinter import ttk, messagebox
import os
import yaml
from common.config import get_config_dir

class MonsterPosEditor(ttk.LabelFrame):
    def __init__(self, parent, city_var, *args, **kwargs):
        super().__init__(parent, text="怪物点坐标(monster_pos)", padding=(5, 5), *args, **kwargs)
        self.city_var = city_var
        self.city_var.trace_add('write', self.on_city_change)
        self.monster_pos = []
        self._build_widgets()
        self.load_monster_pos(self.city_var.get())
        self.refresh_editor()

    def _build_widgets(self):
        self.editor = tk.Text(self)
        self.editor.grid(row=0, column=0, padx=5, pady=3, sticky='nsew')
        self.editor.insert(tk.END, "请输入坐标，格式为：x,y\n每行一个坐标")
        self.editor.bind('<FocusIn>', self.on_focus_in)
        self.editor.bind('<FocusOut>', self.on_focus_out)
        save_btn = ttk.Button(self, text="保存", command=self.save_to_yaml)
        save_btn.grid(row=1, column=0, pady=5, sticky='ew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

    def on_focus_in(self, event):
        if self.editor.get(1.0, tk.END).strip() == "请输入坐标，格式为：x,y\n每行一个坐标":
            self.editor.delete(1.0, tk.END)

    def on_focus_out(self, event):
        if not self.editor.get(1.0, tk.END).strip():
            self.editor.insert(tk.END, "请输入坐标，格式为：x,y\n每行一个坐标")

    def load_monster_pos(self, city_name):
        cities_path = os.path.join(get_config_dir(), "fengmo_cities.yaml")
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities_data = yaml.safe_load(f) or {}
        self.monster_pos = cities_data.get("cities", {}).get(city_name, {}).get("monster_pos", [])

    def refresh_editor(self):
        self.editor.delete(1.0, tk.END)
        for pos in self.monster_pos:
            self.editor.insert(tk.END, f"{pos[0]},{pos[1]}\n")

    def save_to_yaml(self):
        content = self.editor.get(1.0, tk.END).strip()
        lines = content.split('\n')
        new_monster_pos = []
        for line in lines:
            if line.strip():
                try:
                    x, y = map(int, line.split(','))
                    new_monster_pos.append([x, y])
                except Exception:
                    messagebox.showwarning("提示", f"无效的坐标格式: {line}")
                    return
        self.monster_pos = new_monster_pos
        city_name = self.city_var.get()
        cities_path = os.path.join(get_config_dir(), "fengmo_cities.yaml")
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities_data = yaml.safe_load(f) or {}
        if "cities" not in cities_data:
            cities_data["cities"] = {}
        if city_name not in cities_data["cities"]:
            cities_data["cities"][city_name] = {}
        cities_data["cities"][city_name]["monster_pos"] = self.monster_pos
        with open(cities_path, 'w', encoding='utf-8') as f:
            yaml.dump(cities_data, f, allow_unicode=True, sort_keys=False)
        messagebox.showinfo("提示", "怪物点坐标已保存！")

    def on_city_change(self, *args):
        self.load_monster_pos(self.city_var.get())
        self.refresh_editor() 