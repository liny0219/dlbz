"""
文件句柄管理器
确保所有文件句柄正确关闭，防止文件句柄泄漏
"""

import logging
from typing import List, Optional
from utils import logger

class FileHandleManager:
    """
    文件句柄管理器
    确保所有文件句柄正确关闭，防止文件句柄泄漏
    """
    
    def __init__(self):
        """初始化文件句柄管理器"""
        self._file_handles: List = []
        self._log_handlers: List[logging.FileHandler] = []
        self._is_cleaned_up = False
        
    def register_file_handler(self, handler: logging.FileHandler):
        """
        注册文件处理器
        
        :param handler: 日志文件处理器
        """
        if not self._is_cleaned_up:
            self._log_handlers.append(handler)
            logger.debug(f"注册文件处理器: {handler.baseFilename}")
        
    def register_file_handle(self, file_handle):
        """
        注册文件句柄
        
        :param file_handle: 文件句柄对象
        """
        if not self._is_cleaned_up:
            self._file_handles.append(file_handle)
            logger.debug(f"注册文件句柄: {file_handle}")
        
    def cleanup_all(self):
        """清理所有文件句柄"""
        if self._is_cleaned_up:
            return
            
        logger.info("开始清理文件句柄...")
        
        # 关闭所有日志文件处理器
        closed_handlers = 0
        for handler in self._log_handlers:
            try:
                if hasattr(handler, 'close'):
                    handler.close()
                    closed_handlers += 1
                    logger.debug(f"关闭日志处理器: {handler.baseFilename}")
            except Exception as e:
                logger.warning(f"关闭日志处理器失败: {e}")
        
        # 关闭所有文件句柄
        closed_handles = 0
        for file_handle in self._file_handles:
            try:
                if hasattr(file_handle, 'close'):
                    file_handle.close()
                    closed_handles += 1
                    logger.debug(f"关闭文件句柄: {file_handle}")
            except Exception as e:
                logger.warning(f"关闭文件句柄失败: {e}")
        
        # 清理列表
        self._file_handles.clear()
        self._log_handlers.clear()
        
        self._is_cleaned_up = True
        logger.info(f"文件句柄清理完成: 关闭了 {closed_handlers} 个处理器, {closed_handles} 个文件句柄")
        
    def get_handle_count(self) -> int:
        """获取当前管理的句柄数量"""
        return len(self._file_handles) + len(self._log_handlers)
        
    def get_handler_info(self) -> List[str]:
        """获取处理器信息"""
        info = []
        for handler in self._log_handlers:
            if hasattr(handler, 'baseFilename'):
                info.append(f"FileHandler: {handler.baseFilename}")
            else:
                info.append(f"FileHandler: {type(handler).__name__}")
        return info

# 全局文件句柄管理器实例
_global_file_handle_manager: Optional[FileHandleManager] = None

def get_file_handle_manager() -> FileHandleManager:
    """获取全局文件句柄管理器实例"""
    global _global_file_handle_manager
    if _global_file_handle_manager is None:
        _global_file_handle_manager = FileHandleManager()
    return _global_file_handle_manager

def cleanup_file_handle_manager():
    """清理文件句柄管理器"""
    global _global_file_handle_manager
    if _global_file_handle_manager:
        _global_file_handle_manager.cleanup_all()
        _global_file_handle_manager = None 