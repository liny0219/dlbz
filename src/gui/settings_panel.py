import tkinter as tk
from tkinter import ttk
import yaml
import os
from common.config import get_config_dir
from gui.monster_editor import MonsterEditor
from tkinter import messagebox

class SettingsPanel(ttk.Frame):
    def __init__(self, parent, config_files, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.config_vars = {}
        config_dir = get_config_dir()
        for fname, label in config_files:
            if fname == "fengmo_cities.yaml":
                continue
            fpath = os.path.join(config_dir, fname)
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=label)
            vars_dict = {}
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    try:
                        data = yaml.safe_load(f) or {}
                    except Exception as e:
                        data = {}
                row = 0
                if fname == "fengmo.yaml":
                    label_width = 10
                    input_width = 20
                    ttk.Label(frame, text="旅馆休息", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    rest_var = tk.StringVar(value="是" if data.get("rest_in_inn", True) else "否")
                    rest_combo = ttk.Combobox(frame, textvariable=rest_var, values=["是", "否"], state="readonly", width=input_width)
                    rest_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["rest_in_inn"] = rest_var
                    row += 1
                    from common.config import config
                    city_keys = list(config.fengmo_cities.keys())
                    city_display = city_keys
                    ttk.Label(frame, text="城市", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    city_var = tk.StringVar(value=data.get("city", city_keys[0]))
                    city_combo = ttk.Combobox(frame, textvariable=city_var, values=city_display, state="readonly", width=input_width)
                    city_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["city"] = city_var
                    row += 1
                    ttk.Label(frame, text="深度", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    depth_var = tk.StringVar(value=str(data.get("depth", 1)))
                    depth_spin = tk.Spinbox(frame, from_=1, to=10, textvariable=depth_var, width=input_width)
                    depth_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["depth"] = depth_var
                    row += 1
                    ttk.Label(frame, text="逢魔点等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    wait_var = tk.StringVar(value=str(data.get("find_point_wait_time", 3)))
                    wait_spin = tk.Spinbox(frame, from_=2, to=5, textvariable=wait_var, width=input_width)
                    wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["find_point_wait_time"] = wait_var
                    row += 1
                    ttk.Label(frame, text="起步等待时间", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                    wait_map_time_var = tk.StringVar(value=str(data.get("wait_map_time", 0.5)))
                    start_wait_spin = tk.Spinbox(frame, from_=0.5, to=1.5, increment=0.1, textvariable=wait_map_time_var, width=input_width)
                    start_wait_spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                    vars_dict["wait_map_time"] = wait_map_time_var
                    row += 1
                    # 怪物配置区块
                    monster_editor = MonsterEditor(frame, city_var)
                    monster_editor.grid(row=row, column=0, columnspan=2, sticky='nsew', padx=5, pady=10)
                    # 关键：让怪物配置区块自适应剩余高度和宽度
                    frame.rowconfigure(row, weight=1)
                    frame.columnconfigure(0, weight=1)
                    frame.columnconfigure(1, weight=1)
                    vars_dict["monster_editor"] = monster_editor
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
        save_btn = ttk.Button(self, text="保存所有设置", command=self.save_settings)
        save_btn.pack(pady=10)

    def save_settings(self):
        config_dir = get_config_dir()
        for fname, vars_dict in self.config_vars.items():
            fpath = os.path.join(config_dir, fname)
            data = {}
            for k, var in vars_dict.items():
                if k == "monster_editor":
                    continue
                v = var.get()
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
            except Exception as e:
                print(f"保存 {fname} 失败: {e}")
            # 保存怪物配置
            if "monster_editor" in vars_dict:
                vars_dict["monster_editor"].save_to_yaml()
        messagebox.showinfo("提示", "所有设置已保存！") 