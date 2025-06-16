import tkinter as tk
from tkinter import ttk, messagebox
import os
from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type

class BattleSettingsTab(ttk.Frame):
    def __init__(self, master, config_data, config_filename):
        super().__init__(master)
        self.config_filename = config_filename
        label_width = 14
        input_width = 20
        row = 0
        self.vars = {}
        CONFIG_ITEMS = {
            'wait_time': {'display_name': '基础等待时间', 'description': '基础等待时间(秒)', 'step': 0.1},
            'drag_press_time': {'display_name': '拖拽按下时间', 'description': '拖拽按下等待时间(秒)', 'step': 0.1},
            'drag_wait_time': {'display_name': '拖拽等待时间', 'description': '拖拽等待时间(秒)', 'step': 0.1},
            'drag_release_time': {'display_name': '拖拽松开时间', 'description': '拖拽松开等待时间(秒)', 'step': 0.1},
            'wait_ui_time': {'display_name': 'UI等待时间', 'description': 'UI等待时间(秒)', 'step': 0.1},
            'recognition_time': {'display_name': '识别时间', 'description': '战斗识别时间(秒)', 'step': 0.1, 'min_value': 0.1},
            'auto_battle_timeout': {'display_name': '自动战斗超时', 'description': '自动战斗超时时间(秒)', 'step': 1.0},
            'check_dead_timeout': {'display_name': '检查死亡超时', 'description': '检查角色死亡超时时间(秒)', 'step': 0.5},
            'reset_round_timeout': {'display_name': '重置回合超时', 'description': '重置回合超时时间(秒)', 'step': 1.0},
            'exit_battle_timeout': {'display_name': '退出战斗超时', 'description': '退出战斗超时时间(秒)', 'step': 1.0},
            'transform_timeout': {'display_name': '切换形态超时', 'description': '切换形态超时时间(秒)', 'step': 1.0},
            'cast_sp_timeout': {'display_name': 'SP技能超时', 'description': '释放SP技能超时时间(秒)', 'step': 1.0},
            'cast_skill_timeout': {'display_name': '技能超时', 'description': '释放技能超时时间(秒)', 'step': 1.0},
            'attack_timeout': {'display_name': '攻击超时', 'description': '攻击超时时间(秒)', 'step': 0.5},
            'wait_in_round_timeout': {'display_name': '等待回合超时', 'description': '等待回合超时时间(秒)', 'step': 1.0},
            'wait_done_timeout': {'display_name': '等待结束超时', 'description': '等待战斗结束超时时间(秒)', 'step': 5.0},
            'boost_timeout': {'display_name': '全体加成超时', 'description': '全体加成超时时间(秒)', 'step': 1.0},
            'switch_all_timeout': {'display_name': '全员交替超时', 'description': '全员交替超时时间(秒)', 'step': 0.5},
        }
        # 首先处理CONFIG_ITEMS中定义的配置项
        from common.config import BattleConfig
        default_config = BattleConfig()
        
        for k, config_item in CONFIG_ITEMS.items():
            # 获取配置值，如果config_data中没有，则使用默认值
            v = config_data.get(k, getattr(default_config, k))
            display_name = config_item['display_name']
            description = config_item['description']
            step = config_item['step']
            min_value = config_item.get('min_value', None)  # 获取自定义最小值
            ttk.Label(self, text=display_name, width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
            if isinstance(v, bool):
                var = tk.BooleanVar(value=v)
                check = ttk.Checkbutton(self, variable=var)
                check.grid(row=row, column=1, padx=5, pady=3, sticky='w')
            else:
                # 判断是否为整数类型的配置项
                if isinstance(v, int) or (step >= 1.0 and step == int(step)):
                    var = tk.IntVar(value=int(v))
                    if step >= 1.0:
                        from_ = 1
                        to = 100
                    else:
                        from_ = 1
                        to = 10
                    spin = tk.Spinbox(self, from_=from_, to=to, increment=int(step), textvariable=var, width=input_width)
                    spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                else:
                    var = tk.DoubleVar(value=v)
                    # 如果有自定义最小值，使用自定义值；否则使用默认逻辑
                    if min_value is not None:
                        from_ = min_value
                        to = 100.0 if step >= 1.0 else 10.0
                    elif step >= 1.0:
                        from_ = 1.0
                        to = 100.0
                    elif step >= 0.5:
                        from_ = 0.5
                        to = 10.0
                    else:
                        from_ = 0.1
                        to = 2.0
                    spin = tk.Spinbox(self, from_=from_, to=to, increment=step, textvariable=var, width=input_width, format="%.1f")
                    spin.grid(row=row, column=1, padx=5, pady=3, sticky='w')
            desc_label = ttk.Label(self, text=description, font=("TkDefaultFont", 8), foreground="gray")
            desc_label.grid(row=row, column=2, padx=5, pady=3, sticky='w')
            self.vars[k] = var
            row += 1
        
        # 然后处理CONFIG_ITEMS中没有定义但config_data中存在的配置项
        for k, v in config_data.items():
            if k not in CONFIG_ITEMS:
                ttk.Label(self, text=k, width=label_width, anchor="w").grid(row=row, column=0, sticky='w', padx=5, pady=3)
                var = tk.StringVar(value=str(v))
                entry = ttk.Entry(self, textvariable=var, width=input_width)
                entry.grid(row=row, column=1, padx=5, pady=3, sticky='w')
                self.vars[k] = var
                row += 1
        save_btn = ttk.Button(self, text="保存设置", command=self.save_settings)
        save_btn.grid(row=row, column=0, columnspan=3, pady=10)

    def get_config_data(self):
        return {k: var.get() for k, var in self.vars.items()}

    def save_settings(self):
        config_dir = get_config_dir()
        fpath = os.path.join(config_dir, self.config_filename)
        raw_data = self.get_config_data()
        save_yaml_with_type(fpath, raw_data)
        messagebox.showinfo("提示", "设置已保存！") 