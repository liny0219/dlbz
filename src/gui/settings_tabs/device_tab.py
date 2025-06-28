import tkinter as tk
from tkinter import ttk, messagebox
import os
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type

class DeviceSettingsTab(ttk.Frame):
    def __init__(self, master, config_data, config_filename):
        super().__init__(master)
        self.config_filename = config_filename
        label_width = 14
        input_width = 20
        row = 0
        self.vars = {}
        
        # 服务器配置映射
        self.server_packages = {
            "官服": "com.netease.ma167",
            "B服": "com.netease.ma167.bilibili"
        }
        
        # 处理app_packages配置项
        app_packages_val = config_data.get("app_packages", "com.netease.ma167")
        # 根据包名找到对应的显示名称
        display_name = "官服"  # 默认值
        for name, package in self.server_packages.items():
            if package == app_packages_val:
                display_name = name
                break
        
        self.app_packages_var = tk.StringVar(value=display_name)
        ttk.Label(self, text="服务器", width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
        app_packages_combo = ttk.Combobox(self, textvariable=self.app_packages_var, 
                                         values=list(self.server_packages.keys()), 
                                         state="readonly", width=input_width)
        app_packages_combo.grid(row=row, column=1, padx=5, pady=3, sticky='w')
        row += 1
        
        # 处理其他配置项
        for k, v in config_data.items():
            if k == "app_packages":
                continue  # 跳过已处理的app_packages
            ttk.Label(self, text=k).grid(row=row, column=0, sticky='w', padx=5, pady=3)
            var = tk.StringVar(value=str(v))
            entry = ttk.Entry(self, textvariable=var, width=40)
            entry.grid(row=row, column=1, padx=5, pady=3)
            self.vars[k] = var
            row += 1
        
        save_btn = ttk.Button(self, text="保存设置", command=self.save_settings)
        save_btn.grid(row=row, column=0, columnspan=2, pady=10)

    def get_config_data(self):
        data = {}
        # 添加app_packages配置
        display_name = self.app_packages_var.get()
        data["app_packages"] = self.server_packages.get(display_name, "com.netease.ma167")
        
        # 添加其他配置项
        for k, var in self.vars.items():
            data[k] = var.get()
        return data

    def save_settings(self):
        config_dir = get_config_dir()
        fpath = os.path.join(config_dir, self.config_filename)
        raw_data = self.get_config_data()
        save_yaml_with_type(fpath, raw_data)
        messagebox.showinfo("提示", "设置已保存！") 