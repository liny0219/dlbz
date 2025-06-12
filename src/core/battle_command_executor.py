from __future__ import annotations
import logging
from typing import List, Dict, Any
from core.battle import Battle
from typing import TYPE_CHECKING
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
            "Click":       ["x", "y"],
            "Switch":      [],
            "Boost":       [],
            "CheckDead":   [],
            "NoCheckDead": [],
            "Run":         [],
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

    def execute_all(self):
        """
        顺序执行所有指令，遇到异常自动记录并继续
        """
        check_dead_cmd = None
        for idx, cmd in enumerate(self.commands):
            try:
                self.logger.info(f"执行第{idx+1}条指令: {cmd}")
                if cmd.get('type') == 'CheckDead':
                    self.logger.info(f"开启队友阵亡检查:{cmd}")
                    check_dead_cmd = cmd
                result = self.execute_command(cmd)
                if result and cmd.get('type') == 'Run':
                    return False
                if not result:
                    self.battle.reset_round()
                    result = self.battle.wait_in_round_or_world(lambda screenshot:
                                                    "in_world" if self.world.in_world(screenshot) else None, timeout=30)
                    if result in ['in_round']:
                        self.logger.info(f"指令执行异常:{cmd}")
                        self.battle.exit_battle()
                        return False
                    if result in ['in_world']:
                        self.logger.info(f"指令执行异常:{cmd}{result}.但是进入世界,默认为战斗提前结束")
                        return True
                if cmd.get('type') == 'NoCheckDead':
                    self.logger.info(f"取消队友阵亡检查:{cmd}")
                    check_dead_cmd = None
                if cmd.get('type') == 'Attack':
                    result = self.battle.wait_done(lambda screenshot: "in_world" if self.world.in_world(screenshot) else None)
                    if result in ['wait_done_timeout', 'exception']:
                        self.logger.info(f"回合异常:{cmd}{result}")
                        return False
                    if result == 'in_round' and check_dead_cmd and self.battle.check_dead(cmd.get('params', {}).get('role_id', 0)):
                        self.logger.info(f"检查到队友阵亡:{cmd}")
                        self.battle.reset_round()
                        self.battle.exit_battle()
                        return True
            except Exception as e:
                self.logger.error(f"执行指令失败: {cmd}, 错误: {e}")
        return True

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
        else:
            self.logger.warning(f"未知指令类型: {cmd_type}")

    def reset(self):
        """
        重置指令队列和执行状态，便于复用
        """
        self.commands = []
        self._current_index = 0
        self.logger.info("BattleCommandExecutor 已重置")

    def close(self):
        """
        释放资源（如有）
        """
        self.logger.info("BattleCommandExecutor 已关闭")

    def __del__(self):
        self.close() 