import tkinter as tk
from tkinter import ttk, messagebox
import os
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type

class DeviceSettingsTab(ttk.Frame):
    def __init__(self, master, config_data, config_filename):
        super().__init__(master)
        self.config_filename = config_filename
        row = 0
        self.vars = {}
        for k, v in config_data.items():
            ttk.Label(self, text=k).grid(row=row, column=0, sticky='w', padx=5, pady=3)
            var = tk.StringVar(value=str(v))
            entry = ttk.Entry(self, textvariable=var, width=40)
            entry.grid(row=row, column=1, padx=5, pady=3)
            self.vars[k] = var
            row += 1
        save_btn = ttk.Button(self, text="保存设置", command=self.save_settings)
        save_btn.grid(row=row, column=0, columnspan=2, pady=10)

    def get_config_data(self):
        return {k: var.get() for k, var in self.vars.items()}

    def save_settings(self):
        config_dir = get_config_dir()
        fpath = os.path.join(config_dir, self.config_filename)
        raw_data = self.get_config_data()
        save_yaml_with_type(fpath, raw_data)
        messagebox.showinfo("提示", "设置已保存！") 