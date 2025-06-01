import tkinter as tk
from tkinter import ttk, scrolledtext

class LogPanel(ttk.Frame):
    def __init__(self, parent, log_level_var, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.log_level_var = log_level_var
        self._build_widgets()

    def _build_widgets(self):
        self.log_text = scrolledtext.ScrolledText(self, width=120, height=20, state='disabled', font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self, text="日志级别:").pack(side=tk.LEFT, padx=5)
        self.loglevel_combo = ttk.Combobox(self, textvariable=self.log_level_var, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], width=10, state="readonly")
        self.loglevel_combo.pack(side=tk.LEFT, padx=5)

    def append_log(self, msg):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled') 