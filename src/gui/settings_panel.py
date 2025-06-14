import tkinter as tk
from tkinter import ttk
import os
import yaml
from common.config import get_config_dir
from gui.settings_tabs.fengmo_tab import FengmoSettingsTab
from gui.settings_tabs.device_tab import DeviceSettingsTab
from gui.settings_tabs.battle_tab import BattleSettingsTab
from gui.settings_tabs.settings_tab import SettingsSettingsTab
from gui.settings_tabs.logging_tab import LoggingSettingsTab
from gui.settings_tabs.game_tab import GameSettingsTab
from gui.settings_tabs.ocr_tab import OCRSettingsTab

class SettingsPanel(ttk.Frame):
    def __init__(self, master, config_files, save_callback):
        super().__init__(master)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs = {}
        config_dir = get_config_dir()
        for fname, label in config_files:
            if fname == "fengmo_cities.yaml":
                continue
            fpath = os.path.join(config_dir, fname)
            config_data = {}
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    try:
                        config_data = yaml.safe_load(f) or {}
                    except Exception:
                        config_data = {}
            if fname == "fengmo.yaml":
                tab = FengmoSettingsTab(self.notebook, config_data, fname)
            elif fname == "device.yaml":
                tab = DeviceSettingsTab(self.notebook, config_data, fname)
            elif fname == "battle.yaml":
                tab = BattleSettingsTab(self.notebook, config_data, fname)
            elif fname == "settings.yaml":
                tab = SettingsSettingsTab(self.notebook, config_data, fname)
            elif fname == "logging.yaml":
                tab = LoggingSettingsTab(self.notebook, config_data, fname)
            elif fname == "game.yaml":
                tab = GameSettingsTab(self.notebook, config_data, fname)
            elif fname == "ocr.yaml":
                tab = OCRSettingsTab(self.notebook, config_data, fname)
            else:
                tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=label)
            self.tabs[fname] = tab 