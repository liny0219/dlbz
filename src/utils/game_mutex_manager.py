"""
游戏互斥管理器
确保每个玩法同时只能单独启动，开启新玩法时自动终止已在运行的玩法
"""

from tkinter import messagebox
from typing import Dict, List, Optional
from utils.process_manager import get_process_manager
from utils import logger

class GameMutexManager:
    """游戏互斥管理器"""
    
    def __init__(self):
        """
        初始化游戏互斥管理器
        """
        self.process_manager = get_process_manager()
        self.game_processes: Dict[str, dict] = {}  # 存储各玩法的进程信息
        self.game_names = {
            "fengmo_process": "逢魔玩法",
            "farming_process": "自动刷野", 
            "memory_test_process": "追忆之书测试",
            "battle_test_process": "单次战斗测试",
            "daily_process": "日常玩法"
        }
    
    def register_game_process(self, game_key: str, process, queue=None, parent_widget=None):
        """
        注册游戏进程
        
        :param game_key: 游戏进程键名
        :param process: 进程对象
        :param queue: 日志队列
        :param parent_widget: 父窗口组件
        """
        self.game_processes[game_key] = {
            'process': process,
            'queue': queue,
            'parent_widget': parent_widget,
            'name': self.game_names.get(game_key, game_key)
        }
        logger.info(f"注册游戏进程: {self.game_names.get(game_key, game_key)}")
    
    def unregister_game_process(self, game_key: str):
        """
        注销游戏进程
        
        :param game_key: 游戏进程键名
        """
        if game_key in self.game_processes:
            del self.game_processes[game_key]
            logger.info(f"注销游戏进程: {game_key}")
    
    def is_game_running(self, game_key: str) -> bool:
        """
        检查指定游戏是否在运行
        
        :param game_key: 游戏进程键名
        :return: 是否在运行
        """
        if game_key not in self.game_processes:
            return False
        process_info = self.game_processes[game_key]
        return process_info['process'] and process_info['process'].is_alive()
    
    def get_running_games(self) -> List[str]:
        """
        获取正在运行的游戏列表
        
        :return: 正在运行的游戏名称列表
        """
        running_games = []
        for game_key, process_info in self.game_processes.items():
            if process_info['process'] and process_info['process'].is_alive():
                running_games.append(process_info['name'])
        return running_games
    
    def is_any_game_running(self) -> bool:
        """
        检查是否有任何游戏在运行
        
        :return: 是否有游戏在运行
        """
        return len(self.get_running_games()) > 0
    
    def stop_game(self, game_key: str) -> bool:
        """
        停止指定游戏
        
        :param game_key: 游戏进程键名
        :return: 是否成功停止
        """
        if not self.is_game_running(game_key):
            return True
        
        process_info = self.game_processes[game_key]
        game_name = process_info['name']
        logger.info(f"正在停止游戏: {game_name}")
        
        # 使用进程管理器停止进程
        if self.process_manager.stop_process(process_info['process']):
            logger.info(f"成功停止游戏: {game_name}")
            # 清理引用
            process_info['process'] = None
            process_info['queue'] = None
            return True
        else:
            logger.error(f"停止游戏失败: {game_name}")
            return False
    
    def stop_all_games(self) -> int:
        """
        停止所有游戏
        
        :return: 成功停止的游戏数量
        """
        stopped_count = 0
        running_games = self.get_running_games()
        
        if not running_games:
            return 0
        
        logger.info(f"正在停止所有游戏: {', '.join(running_games)}")
        
        # 停止所有游戏进程
        for game_key in list(self.game_processes.keys()):
            if self.stop_game(game_key):
                stopped_count += 1
        
        logger.info(f"成功停止 {stopped_count} 个游戏")
        return stopped_count
    
    def check_and_stop_other_games(self, new_game_key: str, parent_widget=None) -> bool:
        """
        检查并停止其他游戏，为新游戏让路
        
        :param new_game_key: 新游戏的键名
        :param parent_widget: 父窗口组件，用于显示确认对话框
        :return: 是否应该继续启动新游戏
        """
        running_games = self.get_running_games()
        
        if not running_games:
            return True
        
        # 如果新游戏已经在运行，直接返回
        if self.is_game_running(new_game_key):
            if parent_widget:
                messagebox.showwarning("提示", f"{self.game_names.get(new_game_key, new_game_key)}已在运行中！")
            return False
        
        # 显示确认对话框
        if parent_widget:
            running_list = '\n'.join([f"• {game}" for game in running_games])
            new_game_name = self.game_names.get(new_game_key, new_game_key)
            result = messagebox.askyesno(
                "其他玩法正在运行", 
                f"检测到以下玩法正在运行:\n\n{running_list}\n\n是否停止所有正在运行的玩法并启动{new_game_name}？",
                icon="warning"
            )
            if not result:
                return False
        
        # 停止所有其他游戏
        stopped_count = self.stop_all_games()
        
        if stopped_count > 0:
            logger.info(f"已停止 {stopped_count} 个游戏，准备启动新游戏")
            # 等待一小段时间确保进程完全停止
            import time
            time.sleep(1)
        
        return True
    
    def start_game_safely(self, game_key: str, target_func, args=(), kwargs={}, 
                         parent_widget=None, log_callback=None) -> tuple:
        """
        安全启动游戏，自动处理互斥
        
        :param game_key: 游戏进程键名
        :param target_func: 目标函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :param parent_widget: 父窗口组件
        :param log_callback: 日志回调函数
        :return: (是否成功, 进程对象, 队列对象)
        """
        # 检查并停止其他游戏
        if not self.check_and_stop_other_games(game_key, parent_widget):
            return False, None, None
        
        try:
            # 创建日志队列
            import multiprocessing
            log_queue = multiprocessing.Queue()
            
            # 修改args，将队列参数正确传递
            # 查找args中None的位置，替换为实际的队列
            new_args = list(args)
            for i, arg in enumerate(new_args):
                if arg is None and i < len(new_args) - 1:  # 假设None是队列参数
                    new_args[i] = log_queue
                    break
            
            # 使用进程管理器启动进程
            process, queue = self.process_manager.start_process(
                target=target_func,
                args=tuple(new_args),
                kwargs=kwargs,
                name=game_key
            )
            
            # 注册游戏进程
            self.register_game_process(game_key, process, log_queue, parent_widget)
            
            game_name = self.game_names.get(game_key, game_key)
            logger.info(f"成功启动游戏: {game_name}")
            
            if log_callback:
                log_callback(f"{game_name}进程启动成功")
            
            return True, process, log_queue
            
        except Exception as e:
            logger.error(f"启动游戏失败: {game_key}, 错误: {e}")
            if log_callback:
                log_callback(f"启动游戏失败: {e}")
            return False, None, None
    
    def stop_game_safely(self, game_key: str, log_callback=None) -> bool:
        """
        安全停止游戏
        
        :param game_key: 游戏进程键名
        :param log_callback: 日志回调函数
        :return: 是否成功停止
        """
        if not self.is_game_running(game_key):
            if log_callback:
                log_callback(f"{self.game_names.get(game_key, game_key)}未在运行")
            return True
        
        game_name = self.game_names.get(game_key, game_key)
        if log_callback:
            log_callback(f"正在停止{game_name}...")
        
        success = self.stop_game(game_key)
        
        if success:
            if log_callback:
                log_callback(f"{game_name}已成功停止")
        else:
            if log_callback:
                log_callback(f"{game_name}停止失败")
        
        return success
    
    def cleanup(self):
        """清理所有游戏进程"""
        logger.info("清理所有游戏进程...")
        self.stop_all_games()
        self.game_processes.clear()

# 全局游戏互斥管理器实例
_global_game_mutex_manager: Optional[GameMutexManager] = None

def get_game_mutex_manager() -> GameMutexManager:
    """
    获取全局游戏互斥管理器实例
    
    :return: 游戏互斥管理器实例
    """
    global _global_game_mutex_manager
    if _global_game_mutex_manager is None:
        _global_game_mutex_manager = GameMutexManager()
    return _global_game_mutex_manager

def cleanup_all_games():
    """
    清理所有游戏进程（全局函数）
    """
    global _global_game_mutex_manager
    if _global_game_mutex_manager:
        _global_game_mutex_manager.cleanup() 