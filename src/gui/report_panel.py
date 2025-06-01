import tkinter as tk
from tkinter import ttk

class ReportPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="玩法统计", padding=(5, 5), *args, **kwargs)
        self.report_text = tk.Text(self, height=7, width=120, state='disabled', font=("Consolas", 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)

    def update_report_data(self, report_str):
        self.report_text.configure(state='normal')
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report_str)
        self.report_text.configure(state='disabled') 