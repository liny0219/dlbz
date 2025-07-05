import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.config import get_config_dir
from utils.yaml_helper import save_yaml_with_type

class RecognitionConfigTab(ttk.Frame):
    def __init__(self, master, config_data, config_filename):
        super().__init__(master)
        self.config_filename = config_filename
        self.config_data = config_data
        self.vars = {}
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="识别设置", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 基础设置区域
        basic_frame = ttk.LabelFrame(main_frame, text="基础设置", padding=(10, 10))
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 语言设置
        lang_frame = ttk.Frame(basic_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lang_frame, text="识别语言:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=config_data.get("lang", "ch"))
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                 values=["ch", "en"], state="readonly", width=10)
        lang_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 角度分类设置
        angle_frame = ttk.Frame(basic_frame)
        angle_frame.pack(fill=tk.X, pady=5)
        self.use_angle_cls_var = tk.BooleanVar(value=config_data.get("use_angle_cls", True))
        angle_check = ttk.Checkbutton(angle_frame, text="使用角度分类", variable=self.use_angle_cls_var)
        angle_check.pack(side=tk.LEFT)
        
        # 调试模式设置
        debug_frame = ttk.Frame(basic_frame)
        debug_frame.pack(fill=tk.X, pady=5)
        self.debug_mode_var = tk.BooleanVar(value=config_data.get("debug_mode", False))
        debug_check = ttk.Checkbutton(debug_frame, text="开启调试模式（输出详细识别与匹配信息）", variable=self.debug_mode_var)
        debug_check.pack(side=tk.LEFT)
        
        # 阈值设置区域
        threshold_frame = ttk.LabelFrame(main_frame, text="阈值设置", padding=(10, 10))
        threshold_frame.pack(fill=tk.X, pady=(0, 15))
        
        # OCR识别置信度阈值
        confidence_frame = ttk.Frame(threshold_frame)
        confidence_frame.pack(fill=tk.X, pady=5)
        ttk.Label(confidence_frame, text="OCR识别置信度阈值:").pack(side=tk.LEFT)
        
        def round_1_decimal(val):
            try:
                return round(float(val), 1)
            except Exception:
                return 0.0
        def on_conf_scale(val):
            v = round_1_decimal(val)
            self.ocr_confidence_var.set(v)
        def on_conf_spin(*args):
            v = round_1_decimal(self.ocr_confidence_var.get())
            self.ocr_confidence_var.set(v)
        self.ocr_confidence_var = tk.DoubleVar(value=round_1_decimal(config_data.get("ocr_confidence_threshold", 0.8)))
        confidence_scale = ttk.Scale(confidence_frame, from_=0.0, to=1.0, 
                                    variable=self.ocr_confidence_var, orient=tk.HORIZONTAL, length=200,
                                    command=on_conf_scale)
        confidence_scale.pack(side=tk.LEFT, padx=(10, 5))
        vcmd = (self.register(lambda P: P=='' or (P.replace('.','',1).isdigit() and 0.0<=float(P)<=1.0 and len(P.split('.')[-1])<=1)), '%P')
        confidence_spin = ttk.Spinbox(confidence_frame, from_=0.0, to=1.0, increment=0.1,
                                     textvariable=self.ocr_confidence_var, width=8, validate='key', validatecommand=vcmd, format='%.1f')
        confidence_spin.pack(side=tk.LEFT)
        self.ocr_confidence_var.trace_add('write', lambda *a: on_conf_spin())
        ttk.Label(confidence_frame, text="(0.0-1.0)").pack(side=tk.LEFT, padx=(5, 0))
        
        # 图像模板匹配阈值
        image_match_frame = ttk.Frame(threshold_frame)
        image_match_frame.pack(fill=tk.X, pady=5)
        ttk.Label(image_match_frame, text="图像模板匹配阈值:").pack(side=tk.LEFT)
        
        def on_img_scale(val):
            v = round_1_decimal(val)
            self.image_template_match_var.set(v)
        def on_img_spin(*args):
            v = round_1_decimal(self.image_template_match_var.get())
            self.image_template_match_var.set(v)
        self.image_template_match_var = tk.DoubleVar(value=round_1_decimal(config_data.get("image_template_match_threshold", 0.95)))
        image_match_scale = ttk.Scale(image_match_frame, from_=0.0, to=1.0, 
                                     variable=self.image_template_match_var, orient=tk.HORIZONTAL, length=200,
                                     command=on_img_scale)
        image_match_scale.pack(side=tk.LEFT, padx=(10, 5))
        vcmd2 = (self.register(lambda P: P=='' or (P.replace('.','',1).isdigit() and 0.0<=float(P)<=1.0 and len(P.split('.')[-1])<=1)), '%P')
        image_match_spin = ttk.Spinbox(image_match_frame, from_=0.0, to=1.0, increment=0.1,
                                      textvariable=self.image_template_match_var, width=8, validate='key', validatecommand=vcmd2, format='%.1f')
        image_match_spin.pack(side=tk.LEFT)
        self.image_template_match_var.trace_add('write', lambda *a: on_img_spin())
        ttk.Label(image_match_frame, text="(0.0-1.0)").pack(side=tk.LEFT, padx=(5, 0))
        
        # 说明文字
        help_frame = ttk.Frame(main_frame)
        help_frame.pack(fill=tk.X, pady=(0, 15))
        help_text = """
说明：
• ocr_confidence_threshold：OCR文本识别的置信度阈值，值越高识别越严格
• image_template_match_threshold：图像模板匹配的相关系数阈值，值越高匹配越严格
• 建议根据实际使用情况调整这些阈值
        """
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, foreground="gray")
        help_label.pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = ttk.Button(button_frame, text="保存设置", command=self.save_settings)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        reset_btn = ttk.Button(button_frame, text="重置默认", command=self.reset_defaults)
        reset_btn.pack(side=tk.RIGHT)

    def get_config_data(self):
        """获取配置数据"""
        return {
            "lang": self.lang_var.get(),
            "use_angle_cls": self.use_angle_cls_var.get(),
            "ocr_confidence_threshold": round(self.ocr_confidence_var.get(), 1),
            "image_template_match_threshold": round(self.image_template_match_var.get(), 1),
            "debug_mode": self.debug_mode_var.get()
        }

    def save_settings(self):
        """保存设置"""
        try:
            config_dir = get_config_dir()
            fpath = os.path.join(config_dir, self.config_filename)
            raw_data = self.get_config_data()
            save_yaml_with_type(fpath, raw_data)
            messagebox.showinfo("提示", "设置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")

    def reset_defaults(self):
        """重置为默认值"""
        if messagebox.askyesno("确认", "确定要重置为默认设置吗？"):
            self.lang_var.set("ch")
            self.use_angle_cls_var.set(True)
            self.ocr_confidence_var.set(0.8)
            self.image_template_match_var.set(0.95)
            self.ocr_confidence_var.set(round(self.ocr_confidence_var.get(), 1))
            self.image_template_match_var.set(round(self.image_template_match_var.get(), 1))
            self.debug_mode_var.set(False)
            messagebox.showinfo("提示", "已重置为默认设置！") 