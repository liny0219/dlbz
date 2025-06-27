"""
内存监控工具
用于检测和报告Python进程的内存使用情况，帮助识别内存泄漏
"""

import psutil
import gc
import time
import threading
from typing import Dict, List, Optional, Callable
import logging
from utils import logger

class MemoryMonitor:
    """
    内存监控器
    定期检查内存使用情况，检测内存泄漏
    """
    
    def __init__(self, check_interval: int = 30, threshold_mb: float = 100.0):
        """
        初始化内存监控器
        
        :param check_interval: 检查间隔（秒）
        :param threshold_mb: 内存增长阈值（MB），超过此值会发出警告
        """
        self.check_interval = check_interval
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
        self.memory_history: List[Dict] = []
        self.max_history_size = 100
        self.callbacks: List[Callable] = []
        
        # 获取当前进程
        self.process = psutil.Process()
        
    def start_monitoring(self):
        """开始内存监控"""
        if self.monitoring:
            logger.warning("内存监控已在运行")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"内存监控已启动，检查间隔: {self.check_interval}秒")
    
    def stop_monitoring(self):
        """停止内存监控"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            if self.monitor_thread.is_alive():
                logger.warning("内存监控线程未能在5秒内退出")
            else:
                logger.info("内存监控线程已正常退出")
        
        # 清理资源
        self.memory_history.clear()
        self.callbacks.clear()
        logger.info("内存监控已停止")
    
    def add_callback(self, callback: Callable[[Dict], None]):
        """添加内存变化回调函数"""
        self.callbacks.append(callback)
    
    def _monitor_loop(self):
        """监控循环"""
        last_memory = self._get_memory_info()
        self.memory_history.append(last_memory)
        
        while self.monitoring:
            try:
                time.sleep(self.check_interval)
                
                if not self.monitoring:
                    break
                    
                current_memory = self._get_memory_info()
                self.memory_history.append(current_memory)
                
                # 限制历史记录大小
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)
                
                # 检查内存增长
                memory_growth = current_memory['rss_mb'] - last_memory['rss_mb']
                if memory_growth > self.threshold_mb:
                    warning_msg = f"内存使用增长 {memory_growth:.1f}MB，当前使用: {current_memory['rss_mb']:.1f}MB"
                    logger.warning(warning_msg)
                    
                    # 触发回调
                    for callback in self.callbacks:
                        try:
                            callback(current_memory)
                        except Exception as e:
                            logger.error(f"内存监控回调执行失败: {e}")
                
                last_memory = current_memory
                
            except Exception as e:
                logger.error(f"内存监控循环异常: {e}")
    
    def _get_memory_info(self) -> Dict:
        """获取当前内存信息"""
        memory_info = self.process.memory_info()
        
        return {
            'timestamp': time.time(),
            'rss_mb': memory_info.rss / 1024 / 1024,  # 物理内存使用量（MB）
            'vms_mb': memory_info.vms / 1024 / 1024,  # 虚拟内存使用量（MB）
            'percent': self.process.memory_percent(),  # 内存使用百分比
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,  # 系统可用内存（MB）
            'gc_objects': len(gc.get_objects()),  # 垃圾回收器跟踪的对象数量
        }
    
    def get_current_memory(self) -> Dict:
        """获取当前内存使用情况"""
        return self._get_memory_info()
    
    def get_memory_history(self) -> List[Dict]:
        """获取内存使用历史"""
        return self.memory_history.copy()
    
    def get_memory_stats(self) -> Dict:
        """获取内存统计信息"""
        if not self.memory_history:
            return {}
        
        rss_values = [entry['rss_mb'] for entry in self.memory_history]
        vms_values = [entry['vms_mb'] for entry in self.memory_history]
        
        return {
            'current_rss_mb': rss_values[-1],
            'current_vms_mb': vms_values[-1],
            'min_rss_mb': min(rss_values),
            'max_rss_mb': max(rss_values),
            'avg_rss_mb': sum(rss_values) / len(rss_values),
            'memory_growth_mb': rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            'history_count': len(self.memory_history),
            'gc_objects': self.memory_history[-1]['gc_objects'] if self.memory_history else 0,
        }
    
    def force_gc(self):
        """强制垃圾回收"""
        collected = gc.collect()
        logger.info(f"强制垃圾回收完成，回收对象数: {collected}")
        return collected
    
    def get_detailed_memory_info(self) -> Dict:
        """获取详细的内存信息"""
        memory_info = self._get_memory_info()
        
        # 获取系统内存信息
        system_memory = psutil.virtual_memory()
        
        # 获取垃圾回收器信息
        gc_stats = gc.get_stats()
        
        return {
            'process_memory': memory_info,
            'system_memory': {
                'total_mb': system_memory.total / 1024 / 1024,
                'available_mb': system_memory.available / 1024 / 1024,
                'used_mb': system_memory.used / 1024 / 1024,
                'percent': system_memory.percent,
            },
            'gc_stats': gc_stats,
            'gc_counts': gc.get_count(),
        }
    
    def detect_memory_leak(self) -> Dict:
        """
        检测内存泄漏
        
        :return: 内存泄漏检测结果
        """
        if len(self.memory_history) < 10:  # 需要足够的历史数据
            return {'leak_detected': False, 'reason': '历史数据不足'}
        
        # 计算最近10次检查的内存增长趋势
        recent_history = self.memory_history[-10:]
        rss_values = [entry['rss_mb'] for entry in recent_history]
        
        # 计算线性回归斜率
        x = list(range(len(rss_values)))
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(rss_values)
        sum_xy = sum(x[i] * rss_values[i] for i in range(n))
        sum_x2 = sum(x[i] * x[i] for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # 计算内存增长总量
        total_growth = rss_values[-1] - rss_values[0]
        
        # 判断是否存在内存泄漏
        leak_detected = False
        leak_reason = ""
        
        if slope > 5.0:  # 每次检查增长超过5MB
            leak_detected = True
            leak_reason = f"内存持续增长，斜率: {slope:.2f}MB/次"
        elif total_growth > 50.0:  # 总增长超过50MB
            leak_detected = True
            leak_reason = f"内存总增长过大: {total_growth:.1f}MB"
        elif rss_values[-1] > 500.0:  # 内存使用超过500MB
            leak_detected = True
            leak_reason = f"内存使用过高: {rss_values[-1]:.1f}MB"
        
        return {
            'leak_detected': leak_detected,
            'reason': leak_reason,
            'slope': slope,
            'total_growth': total_growth,
            'current_memory': rss_values[-1],
            'growth_rate_mb_per_check': slope,
            'history_count': len(self.memory_history)
        }

# 全局内存监控实例
_memory_monitor: Optional[MemoryMonitor] = None

def get_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控实例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor

def start_memory_monitoring(check_interval: int = 30, threshold_mb: float = 100.0):
    """启动内存监控"""
    monitor = get_memory_monitor()
    monitor.check_interval = check_interval
    monitor.threshold_mb = threshold_mb
    monitor.start_monitoring()

def stop_memory_monitoring():
    """停止内存监控"""
    global _memory_monitor
    if _memory_monitor:
        _memory_monitor.stop_monitoring()

def get_memory_stats() -> Dict:
    """获取内存统计信息"""
    monitor = get_memory_monitor()
    return monitor.get_memory_stats()

def force_garbage_collection():
    """强制垃圾回收"""
    monitor = get_memory_monitor()
    return monitor.force_gc()

def log_memory_usage():
    """记录当前内存使用情况"""
    monitor = get_memory_monitor()
    stats = monitor.get_memory_stats()
    
    if stats:
        logger.info(f"内存使用情况 - RSS: {stats['current_rss_mb']:.1f}MB, "
                   f"VMS: {stats['current_vms_mb']:.1f}MB, "
                   f"增长: {stats['memory_growth_mb']:.1f}MB, "
                   f"GC对象: {stats['gc_objects']}")
    else:
        logger.info("无法获取内存统计信息") 