"""
进程管理器
用于管理多进程应用中的进程生命周期，防止僵尸进程
"""

import multiprocessing
import time
import psutil
from typing import Optional, List, Tuple, Any, Callable
from utils import logger

class ProcessManager:
    """进程管理器，防止僵尸进程"""
    
    def __init__(self):
        """
        初始化进程管理器
        """
        self.processes: List[multiprocessing.Process] = []
        self.queues: List[multiprocessing.Queue] = []
        self.process_info: List[dict] = []  # 存储进程信息
        
    def start_process(self, target: Callable, args: tuple = (), kwargs: dict = {}, name: Optional[str] = None) -> Tuple[multiprocessing.Process, multiprocessing.Queue]:
        """
        启动进程并管理其生命周期
        
        :param target: 目标函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :param name: 进程名称
        :return: (进程对象, 队列对象)
        """
        # 创建队列
        queue = multiprocessing.Queue()
        
        # 创建进程
        process = multiprocessing.Process(
            target=target,
            args=args,
            kwargs=kwargs,
            name=name,
            daemon=False  # 不使用daemon，手动管理
        )
        
        # 启动进程
        process.start()
        
        # 记录进程信息
        process_info = {
            'process': process,
            'queue': queue,
            'name': name or f"process_{process.pid}",
            'start_time': time.time(),
            'target': target.__name__
        }
        
        self.processes.append(process)
        self.queues.append(queue)
        self.process_info.append(process_info)
        
        logger.info(f"启动进程: {process_info['name']} (PID: {process.pid})")
        return process, queue
    
    def stop_process(self, process: multiprocessing.Process, timeout: int = 10) -> bool:
        """
        安全停止进程
        
        :param process: 要停止的进程
        :param timeout: 超时时间（秒）
        :return: 是否成功停止
        """
        if not process or not process.is_alive():
            return True
            
        process_name = getattr(process, 'name', f"process_{process.pid}")
        logger.info(f"正在停止进程: {process_name}")
        
        try:
            # 1. 发送SIGTERM信号
            process.terminate()
            
            # 2. 等待进程结束
            process.join(timeout=timeout)
            
            # 3. 如果进程仍然存活，发送SIGKILL
            if process.is_alive():
                logger.warning(f"进程 {process_name} 未能在 {timeout} 秒内退出，强制终止")
                process.kill()
                process.join(timeout=5)
            
            # 4. 检查进程是否真的结束了
            if process.is_alive():
                logger.error(f"进程 {process_name} 无法终止")
                return False
            else:
                logger.info(f"进程 {process_name} 已成功终止")
                return True
                
        except Exception as e:
            logger.error(f"停止进程 {process_name} 时发生异常: {e}")
            return False
    
    def stop_all_processes(self) -> int:
        """
        停止所有进程
        
        :return: 成功停止的进程数量
        """
        logger.info(f"正在停止所有进程，共 {len(self.processes)} 个")
        stopped_count = 0
        
        # 停止所有进程
        for process_info in self.process_info[:]:  # 使用副本避免修改时出错
            process = process_info['process']
            if self.stop_process(process):
                stopped_count += 1
            self.processes.remove(process)
            self.process_info.remove(process_info)
        
        # 关闭所有队列
        for queue in self.queues:
            try:
                queue.close()
                queue.join_thread()
            except Exception as e:
                logger.error(f"关闭队列时发生异常: {e}")
        self.queues.clear()
        
        logger.info(f"成功停止 {stopped_count} 个进程")
        return stopped_count
    
    def cleanup_zombie_processes(self) -> int:
        """
        清理僵尸进程
        
        :return: 清理的僵尸进程数量
        """
        try:
            # 获取当前进程的所有子进程
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            
            zombie_count = 0
            for child in children:
                if child.status() == psutil.STATUS_ZOMBIE:
                    zombie_count += 1
                    logger.warning(f"发现僵尸进程: {child.pid}")
                    try:
                        # 尝试终止僵尸进程
                        child.terminate()
                        child.wait(timeout=5)
                        logger.info(f"成功清理僵尸进程: {child.pid}")
                    except psutil.NoSuchProcess:
                        pass  # 进程已经不存在
                    except Exception as e:
                        logger.error(f"清理僵尸进程 {child.pid} 时发生异常: {e}")
            
            if zombie_count > 0:
                logger.info(f"清理了 {zombie_count} 个僵尸进程")
            
            return zombie_count
                        
        except Exception as e:
            logger.error(f"清理僵尸进程时发生异常: {e}")
            return 0
    
    def get_process_status(self) -> List[dict]:
        """
        获取所有进程状态
        
        :return: 进程状态列表
        """
        status_list = []
        for process_info in self.process_info:
            process = process_info['process']
            status = {
                'name': process_info['name'],
                'pid': process.pid,
                'alive': process.is_alive(),
                'start_time': process_info['start_time'],
                'target': process_info['target'],
                'runtime': time.time() - process_info['start_time'] if process.is_alive() else 0
            }
            status_list.append(status)
        return status_list
    
    def is_any_process_running(self) -> bool:
        """
        检查是否有进程在运行
        
        :return: 是否有进程运行
        """
        return any(process.is_alive() for process in self.processes)
    
    def get_running_processes(self) -> List[str]:
        """
        获取正在运行的进程名称列表
        
        :return: 运行中的进程名称列表
        """
        running_processes = []
        for process_info in self.process_info:
            if process_info['process'].is_alive():
                running_processes.append(process_info['name'])
        return running_processes
    
    def __del__(self):
        """析构函数，确保所有进程都被清理"""
        try:
            self.stop_all_processes()
            self.cleanup_zombie_processes()
        except:
            pass

# 全局进程管理器实例
_global_process_manager: Optional[ProcessManager] = None

def get_process_manager() -> ProcessManager:
    """
    获取全局进程管理器实例
    
    :return: 进程管理器实例
    """
    global _global_process_manager
    if _global_process_manager is None:
        _global_process_manager = ProcessManager()
    return _global_process_manager

def cleanup_all_processes():
    """
    清理所有进程（全局函数）
    """
    global _global_process_manager
    if _global_process_manager:
        _global_process_manager.stop_all_processes()
        _global_process_manager.cleanup_zombie_processes()

def check_and_cleanup_zombies() -> int:
    """
    检查并清理僵尸进程（全局函数）
    
    :return: 清理的僵尸进程数量
    """
    manager = get_process_manager()
    return manager.cleanup_zombie_processes() 