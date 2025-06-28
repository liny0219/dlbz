"""
打包环境修复工具
用于解决在PyInstaller等打包工具打包后的环境中出现的常见问题
"""

import sys
import os
import logging

def fix_frozen_environment():
    """
    修复打包环境中的常见问题
    包括：
    1. 标准输出流为None的问题
    2. tqdm进度条问题
    3. 日志系统问题
    """
    if not getattr(sys, 'frozen', False):
        return  # 非打包环境，不需要修复
    
    # 修复标准输出流
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    
    # 修复tqdm问题
    try:
        import tqdm
        # 禁用tqdm的监控以避免输出问题
        tqdm.tqdm.monitor_interval = 0
    except ImportError:
        pass
    
    # 修复日志系统
    try:
        # 确保根logger有有效的handler
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            # 添加一个安全的handler
            handler = logging.StreamHandler(sys.stdout if sys.stdout else open(os.devnull, 'w'))
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            root_logger.addHandler(handler)
            root_logger.setLevel(logging.WARNING)
    except Exception:
        pass

def safe_import_paddleocr():
    """
    安全导入PaddleOCR，处理打包环境中的问题
    """
    try:
        # 先修复环境
        fix_frozen_environment()
        
        # 然后导入PaddleOCR
        from paddleocr import PaddleOCR
        return PaddleOCR
    except Exception as e:
        logging.error(f"导入PaddleOCR失败: {e}")
        raise

def get_model_path(base_path, model_type, language, model_name):
    """
    获取模型路径，处理打包环境中的路径问题
    """
    if getattr(sys, 'frozen', False):
        # 打包环境，使用相对路径
        return os.path.join(base_path, model_type, language, model_name)
    else:
        # 开发环境，使用绝对路径
        return os.path.join(os.path.dirname(__file__), "..", "..", "ocr", "model", "whl", model_type, language, model_name) 