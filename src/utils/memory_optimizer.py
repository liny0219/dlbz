"""
内存优化工具
提供统一的内存管理和优化功能，包括定期清理、监控和优化建议
"""

import gc
import time
import threading
from typing import Dict, List, Optional, Callable
from utils import logger
from utils.memory_monitor import get_memory_monitor

class MemoryOptimizer:
    """
    内存优化器
    提供自动内存优化、定期清理和性能监控功能
    """
    
    def __init__(self, auto_optimize_interval: int = 300, gc_threshold: int = 1000):
        """
        初始化内存优化器
        
        :param auto_optimize_interval: 自动优化间隔（秒），默认5分钟
        :param gc_threshold: GC阈值，当对象数量超过此值时触发GC
        """
        self.auto_optimize_interval = auto_optimize_interval
        self.gc_threshold = gc_threshold
        self.optimizing = False
        self.optimize_thread = None
        self.memory_monitor = get_memory_monitor()
        self.optimization_callbacks: List[Callable] = []
        
    def start_auto_optimization(self):
        """启动自动内存优化"""
        if self.optimizing:
            logger.warning("内存优化已在运行")
            return
            
        self.optimizing = True
        self.optimize_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimize_thread.start()
        logger.info(f"自动内存优化已启动，间隔: {self.auto_optimize_interval}秒")
    
    def stop_auto_optimization(self):
        """停止自动内存优化"""
        if not self.optimizing:
            return
            
        self.optimizing = False
        if self.optimize_thread and self.optimize_thread.is_alive():
            self.optimize_thread.join(timeout=5)
            if self.optimize_thread.is_alive():
                logger.warning("内存优化线程未能在5秒内退出")
            else:
                logger.info("内存优化线程已正常退出")
        
        # 清理资源
        self.optimization_callbacks.clear()
        logger.info("自动内存优化已停止")
    
    def add_optimization_callback(self, callback: Callable[[Dict], None]):
        """添加优化回调函数"""
        self.optimization_callbacks.append(callback)
    
    def _optimization_loop(self):
        """优化循环"""
        while self.optimizing:
            try:
                time.sleep(self.auto_optimize_interval)
                
                if not self.optimizing:
                    break
                    
                # 执行内存优化
                optimization_result = self.optimize_memory()
                
                # 触发回调
                for callback in self.optimization_callbacks:
                    try:
                        callback(optimization_result)
                    except Exception as e:
                        logger.error(f"内存优化回调执行失败: {e}")
                        
            except Exception as e:
                logger.error(f"内存优化循环异常: {e}")
    
    def optimize_memory(self) -> Dict:
        """
        执行内存优化
        
        :return: 优化结果统计
        """
        start_time = time.time()
        
        # 获取优化前的内存状态
        before_stats = self.memory_monitor.get_memory_stats()
        
        # 执行垃圾回收
        collected_objects = gc.collect()
        
        # 获取优化后的内存状态
        after_stats = self.memory_monitor.get_memory_stats()
        
        # 计算优化效果
        memory_freed = before_stats.get('current_rss_mb', 0) - after_stats.get('current_rss_mb', 0)
        
        optimization_result = {
            'timestamp': time.time(),
            'duration': time.time() - start_time,
            'collected_objects': collected_objects,
            'memory_freed_mb': memory_freed,
            'before_stats': before_stats,
            'after_stats': after_stats
        }
        
        logger.info(f"内存优化完成: 回收{collected_objects}个对象，释放{memory_freed:.1f}MB内存")
        
        return optimization_result
    
    def force_optimization(self) -> Dict:
        """
        强制执行内存优化
        
        :return: 优化结果
        """
        logger.info("执行强制内存优化...")
        return self.optimize_memory()
    
    def get_optimization_status(self) -> Dict:
        """获取优化状态"""
        return {
            'optimizing': self.optimizing,
            'auto_optimize_interval': self.auto_optimize_interval,
            'gc_threshold': self.gc_threshold,
            'memory_stats': self.memory_monitor.get_memory_stats(),
            'callback_count': len(self.optimization_callbacks)
        }
    
    def cleanup(self):
        """清理优化器资源"""
        self.stop_auto_optimization()
        self.optimization_callbacks.clear()

# 全局内存优化器实例
_global_memory_optimizer: Optional[MemoryOptimizer] = None

def get_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器实例"""
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer()
    return _global_memory_optimizer

def start_auto_memory_optimization(interval: int = 300):
    """启动自动内存优化"""
    optimizer = get_memory_optimizer()
    optimizer.auto_optimize_interval = interval
    optimizer.start_auto_optimization()

def stop_auto_memory_optimization():
    """停止自动内存优化"""
    global _global_memory_optimizer
    if _global_memory_optimizer:
        _global_memory_optimizer.stop_auto_optimization()

def force_memory_optimization() -> Dict:
    """强制执行内存优化"""
    optimizer = get_memory_optimizer()
    return optimizer.force_optimization()

def cleanup_memory_optimizer():
    """清理内存优化器"""
    global _global_memory_optimizer
    if _global_memory_optimizer:
        _global_memory_optimizer.cleanup()
        _global_memory_optimizer = None 