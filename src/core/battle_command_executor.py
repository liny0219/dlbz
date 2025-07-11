from __future__ import annotations
import logging
from typing import Callable, List, Dict, Any
from core.battle import Battle
from utils.sleep_utils import sleep_until
from typing import TYPE_CHECKING
from PIL import Image
if TYPE_CHECKING:
    from common.world import World
class BattleCommandExecutor:
    """
    战斗指令执行器
    负责加载、解析、顺序执行战斗指令配置文件，直接调用 Battle 类方法。
    支持重置、销毁、链式调用，便于在复杂流程中多次复用。
    """
    def __init__(self, battle: Battle, world: "World"):
        """
        初始化指令执行器
        :param battle: Battle 实例，负责具体战斗操作
        :param world: World 实例，负责具体世界操作
        """
        self.battle: Battle = battle
        self.commands: List[Dict[str, Any]] = []
        self._current_index: int = 0
        self.logger = logging.getLogger(__name__)
        self.world: World = world
        # 循环控制变量（不考虑嵌套）
        self._loop_start_index: int = -1  # 循环开始位置
        self._loop_count: int = 0  # 循环次数
        self._loop_max_count: int = 0  # 最大循环次数，0表示无限循环
        # 指令类型到参数名的映射
        self._param_map = {
            "BattleStart": [],
            "BattleEnd":   [],
            "Attack":      [],
            "Role":        ["index", "skill", "bp", "role_id", "x", "y"],
            "XRole":       ["index", "skill", "bp", "role_id", "x", "y"],
            "SP":          ["index", "role_id", "x", "y"],
            "XSP":         ["index", "role_id", "x", "y"],
            "EX":          ["index", "bp", "role_id", "x", "y"],
            "XEX":         ["index", "bp", "role_id", "x", "y"],
            "Pet":         ["index", "bp", "role_id", "x", "y"],
            "XPet":        ["index", "bp", "role_id", "x", "y"],
            "Wait":        ["seconds"],
            "Skip":        ["seconds"],
            "RoleEx":      ["index", "skill", "bp", "role_id", "x", "y"],
            "XRoleEx":     ["index", "skill", "bp", "role_id", "x", "y"],
            "Click":       ["x", "y"],
            "Switch":      [],
            "Boost":       [],
            "CheckDead":   [],
            "NoCheckDead": [],
            "Run":         [],
            "ExitApp":     [],
            "PressInRound":["timeout"],
            "LoopS":        [],
            "LoopE":        ["count"],
            # 其它指令可按需扩展
        }

    def load_commands_from_txt(self, path: str) -> bool:
        """
        加载纯文本格式的战斗指令配置文件（每行一个指令，逗号分隔，#注释，空行跳过）
        :param path: 配置文件路径
        :return: self（支持链式调用）
        """
        commands = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # 解析指令类型和参数
                    parts = [p.strip() for p in line.split(',')]
                    if not parts:
                        continue
                    cmd_type = parts[0]
                    param_names = self._param_map.get(cmd_type, [])
                    params = {}
                    for i, val in enumerate(parts[1:] if len(parts) > 1 else []):
                        # 尝试转为 int/float，否则保留字符串
                        try:
                            if '.' in val:
                                v = float(val)
                            else:
                                v = int(val)
                        except Exception:
                            v = val
                        if i < len(param_names):
                            params[param_names[i]] = v
                        else:
                            params[f'arg{i+1}'] = v
                    commands.append({'type': cmd_type, 'params': params})
            self._current_index = 0
            self.commands = commands
            self.logger.info(f"成功加载TXT战斗指令配置: {path}, 共 {len(self.commands)} 条指令")
            return True
        except Exception as e:
            self.logger.error(f"加载TXT战斗指令配置失败: {e}")
            return False

    def execute_all(self, callback:Callable[[Image.Image], str|None]|None = None) -> dict[str,bool|str]:
        """
        顺序执行所有指令，遇到异常自动记录并继续
        支持通过修改 _current_index 来回退到指定命令位置
        """
        check_dead_cmd = None
        # 使用 _current_index 来控制执行位置，支持回退功能
        while self._current_index < len(self.commands):
            idx = self._current_index
            cmd = self.commands[idx]
            next_cmd = self.commands[idx+1] if idx+1 < len(self.commands) else None
            try:
                self.logger.info(f"执行第{idx+1}条指令: {cmd}")
                if cmd.get('type') == 'CheckDead':
                    self.logger.info(f"开启队友阵亡检查:{cmd}")
                    check_dead_cmd = cmd
                result = self.execute_command(cmd)
                if result and cmd.get('type') == 'Auto':
                    self.logger.info(f"等待战斗回合结束")
                    sleep_until(self.battle.not_in_battle,timeout=120)
                    self.logger.info(f"战斗回合结束")
                if result and cmd.get('type') == 'Run':
                    return { 'success': False,"state":'run'}
                if result and cmd.get('type') == 'ExitApp':
                    return { 'success': False,"state":'exit_app'}
                if not result:
                    self.battle.reset_round()
                    result = self.battle.wait_in_round_or_world(callback=callback,timeout=30)
                    if result in ['in_round']:
                        self.logger.info(f"指令执行异常:{cmd}")
                        self.battle.exit_battle()
                        return { 'success': False,"state":'exception'}
                    if result in ['in_world']:
                        self.logger.info(f"指令执行异常:{cmd}{result}.但是进入世界,默认为战斗提前结束")
                        return { 'success': True,"state":'normal'}
                if cmd.get('type') == 'NoCheckDead':
                    self.logger.info(f"取消队友阵亡检查:{cmd}")
                    check_dead_cmd = None
                if cmd.get('type') == 'Attack':
                    self.logger.info(f"等待战斗回合结束")
                    result = self.battle.wait_done(callback=callback)
                    if result == 'end':
                        if next_cmd and next_cmd.get('type') == 'PressInRound':
                            self._current_index += 1
                            continue
                        return { 'success': True,"state":'end'}
                    if result in ['wait_done_timeout', 'exception']:
                        self.logger.info(f"回合异常:{cmd}{result}")
                        return { 'success': False,"state":'exception'}
                    if result == 'in_round' and check_dead_cmd and self.battle.check_dead(cmd.get('params', {}).get('role_id', 0)):
                        self.logger.info(f"检查到队友阵亡:{cmd}")
                        self.battle.reset_round()
                        self.battle.exit_battle()
                        return { 'success': False,"state":'dead'}
                    self.logger.info(f"战斗回合结束, result: {result}")
                    if result in ['in_world']:
                        self.logger.info(f"指令执行异常:{cmd}{result}.但是进入世界,默认为战斗提前结束")
                        return { 'success': True,"state":'normal'}
                # 处理循环逻辑
                if cmd.get('type') == 'LoopS':
                    self._handle_loop_start(idx)
                elif cmd.get('type') == 'LoopE':
                    loop_result = self._handle_loop_end(idx, cmd.get('params', {}))
                    if loop_result is not None:
                        # 如果需要跳转，更新索引
                        self._current_index = loop_result
                        continue
                
            except Exception as e:
                self.logger.error(f"执行指令失败: {cmd}, 错误: {e}")
                return { 'success': False,"state":'exception'}
            
            # 移动到下一条指令
            self._current_index += 1
        
        return { 'success': True,"state":'normal'}

    def execute_command(self, cmd: Dict[str, Any]):
        """
        执行单条指令，根据 type 分发到 Battle 类对应方法
        :param cmd: 指令字典，需包含 type 字段
        """
        cmd_type = cmd.get('type')
        params = cmd.get('params', {})
        if not cmd_type:
            self.logger.warning(f"指令缺少 type 字段: {cmd}")
            return False
        # 指令类型与 Battle 方法映射（全部加 cmd_ 前缀）
        if cmd_type == "Role":
            return self.battle.cmd_role(**params)
        elif cmd_type == "XRole":
            return self.battle.cmd_xrole(**params)
        elif cmd_type == "Boost":
            return self.battle.cmd_boost(**params)
        elif cmd_type == "Attack":
            return self.battle.cmd_attack(**params)
        elif cmd_type == "Switch":
            return self.battle.cmd_switch_all(**params)
        elif cmd_type == "SP":
            return self.battle.cmd_sp_skill(**params)
        elif cmd_type == "XSP":
            return self.battle.cmd_xsp_skill(**params)
        elif cmd_type == "EX":
            return self.battle.cmd_ex(**params)
        elif cmd_type == "XEX":
            return self.battle.cmd_xex(**params)
        elif cmd_type == "Pet":
            return self.battle.cmd_pet(**params)
        elif cmd_type == "XPet":
            return self.battle.cmd_xpet(**params)
        elif cmd_type == "RoleEx":
            return self.battle.cmd_role_ex(**params)
        elif cmd_type == "XRoleEx":
            return self.battle.cmd_xrole_ex(**params)
        elif cmd_type == "Wait":
            return self.battle.cmd_wait(**params)
        elif cmd_type == "Skip":
            return self.battle.cmd_skip(**params)
        elif cmd_type == "Click":
            return self.battle.cmd_click(**params)
        elif cmd_type == "BattleStart":
            return self.battle.cmd_battle_start(**params)
        elif cmd_type == "BattleEnd":
            return self.battle.cmd_battle_end(**params)
        elif cmd_type == "CheckDead":
            return not self.battle.cmd_check_dead(**params)
        elif cmd_type == "Run":
            return self.battle.cmd_run(**params)
        elif cmd_type == "ExitApp":
            return self.battle.cmd_exit_app(**params)
        elif cmd_type == "PressInRound":
            return self.battle.cmd_press_in_round(**params)
        elif cmd_type == "Auto":
            return self.battle.cmd_auto_battle(**params)
        elif cmd_type == "LoopS":
            return True
        elif cmd_type == "LoopE":
            return True
        else:
            self.logger.warning(f"未知指令类型: {cmd_type}")

    def reset_index(self):
        """
        重置当前指令索引
        """
        self._current_index = 0

    def reset(self):
        """
        重置指令队列和执行状态，便于复用
        """
        self.commands = []
        self._current_index = 0
        self._reset_loop_state()
        self.logger.info("BattleCommandExecutor 已重置")

    def set_current_index(self, index: int):
        """
        设置当前执行指令的索引位置，用于回退或跳转到指定命令
        
        :param index: 要设置的指令索引（从0开始）
        """
        if 0 <= index < len(self.commands):
            old_index = self._current_index
            self._current_index = index
            self.logger.info(f"指令执行位置已从第{old_index+1}条调整到第{index+1}条")
        else:
            self.logger.warning(f"无效的指令索引: {index}，有效范围: 0-{len(self.commands)-1}")

    def get_current_index(self) -> int:
        """
        获取当前执行指令的索引位置
        
        :return: 当前指令索引
        """
        return self._current_index

    def rollback_to_command(self, command_index: int):
        """
        回退到指定的命令位置
        
        :param command_index: 要回退到的命令索引（从0开始）
        """
        if 0 <= command_index < len(self.commands):
            self.set_current_index(command_index)
            self.logger.info(f"已回退到第{command_index+1}条指令: {self.commands[command_index]}")
        else:
            self.logger.warning(f"无法回退到索引{command_index}，有效范围: 0-{len(self.commands)-1}")

    def get_total_commands(self) -> int:
        """
        获取总指令数量
        
        :return: 指令总数
        """
        return len(self.commands)

    def _handle_loop_start(self, index: int):
        """
        处理循环开始指令(LoopS)
        
        :param index: 当前指令索引
        """
        self._loop_start_index = index
        self._loop_count = 0
        self.logger.info(f"循环开始标记，位置: 第{index+1}条指令")

    def _handle_loop_end(self, index: int, params: dict) -> int | None:
        """
        处理循环结束指令(LoopE)
        
        :param index: 当前指令索引  
        :param params: 指令参数，包含循环次数
        :return: 如果需要跳转返回新的索引，否则返回None
        """
        if self._loop_start_index == -1:
            self.logger.warning(f"找不到对应的LoopS指令，忽略LoopE")
            return None
        
        # 获取循环次数参数，默认为1
        max_count = params.get('count', 1)
        self._loop_max_count = max_count
        self._loop_count += 1
        
        self.logger.info(f"循环结束检查，当前循环次数: {self._loop_count}/{max_count if max_count > 0 else '无限'}")
        
        # 判断是否需要继续循环
        if max_count == 0 or self._loop_count < max_count:
            # 需要继续循环，跳转到LoopS的下一条指令
            next_index = self._loop_start_index + 1
            self.logger.info(f"继续循环，跳转到第{next_index+1}条指令")
            return next_index
        else:
            # 循环结束，重置循环状态
            self.logger.info(f"循环完成，共执行{self._loop_count}次")
            self._loop_start_index = -1
            self._loop_count = 0
            self._loop_max_count = 0
            return None

    def _reset_loop_state(self):
        """
        重置循环状态
        """
        self._loop_start_index = -1
        self._loop_count = 0
        self._loop_max_count = 0

    def close(self):
        """
        释放资源（如有）
        """
        self.logger.info("BattleCommandExecutor 已关闭")

    def __del__(self):
        self.close() 