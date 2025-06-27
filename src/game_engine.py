#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏引擎核心模块
整合所有算法组件，管理游戏状态和逻辑
"""

import json
import random
from typing import List, Tuple, Dict, Optional
from .config import Config
from .algorithms.maze_generator import MazeGenerator
from .algorithms.path_planning import PathPlanner
from .algorithms.greedy_strategy import GreedyStrategy
from .algorithms.puzzle_solver import PuzzleSolver
from .algorithms.boss_strategy import BossStrategy
from .algorithms.resource_path_planner import ResourcePathPlanner
from .battle.multi_monster_battle import MultiMonsterBattle

class GameEngine:
    """
    游戏引擎类
    """
    
    def __init__(self, maze_size: int = None):
        """
        初始化游戏引擎
        
        Args:
            maze_size: 迷宫大小，如果为None则使用默认值
        """
        self.maze_size = maze_size if maze_size is not None else Config.DEFAULT_MAZE_SIZE
        self.maze = None
        self.player_pos = None
        self.start_pos = None
        self.exit_pos = None
        
        # 算法组件
        self.maze_generator = None
        self.path_planner = None
        self.greedy_strategy = None
        self.puzzle_solver = PuzzleSolver()
        self.boss_strategy = None
        self.resource_path_planner = None
        
        # 游戏状态（移除玩家血量）
        self.player_resources = 0
        self.collected_items = set()
        self.solved_puzzles = set()
        self.defeated_bosses = set()
        
        # 游戏统计
        self.moves_count = 0
        self.puzzles_attempted = 0
        self.battles_fought = 0
        
        # 当前活跃的谜题和战斗
        self.active_puzzle = None
        self.active_battle = None
        self.active_multi_battle = None  # 多怪物战斗
        
        # 待交互状态
        self.pending_interaction = None  # 存储待交互的特殊方格信息
        
        # Boss战斗配置 - 在迷宫生成时固定每个boss位置的难度
        self.boss_configurations = {}  # {(x, y): scenario_name}
        
        # 游戏模式
        self.ai_mode = True  # AI自动游戏模式
        self.visualization_enabled = True
        
        # 自动拾取功能
        self.auto_pickup_enabled = False  # 自动拾取开关
        self.auto_pickup_path = []  # 自动拾取路径
        self.auto_pickup_target = None  # 当前自动拾取目标
    
    def initialize_game(self, maze_size: int = None) -> Dict:
        """
        初始化游戏
        
        Args:
            maze_size: 迷宫大小，如果提供则更新当前迷宫大小
        
        Returns:
            Dict: 初始化结果
        """
        # 如果提供了新的迷宫大小，则更新
        if maze_size is not None:
            self.maze_size = maze_size
            
        # 生成迷宫
        self.maze_generator = MazeGenerator(self.maze_size)
        self.maze = self.maze_generator.generate_maze()
        
        # 找到起点和终点
        self._find_start_and_exit()
        
        # 初始化玩家位置
        self.player_pos = self.start_pos
        
        # 初始化算法组件
        self.path_planner = PathPlanner(self.maze)
        self.greedy_strategy = GreedyStrategy(self.maze)
        self.boss_strategy = BossStrategy()
        self.resource_path_planner = ResourcePathPlanner(self.maze)
        
        # 重置游戏状态
        self._reset_game_state()
        
        # 为每个boss位置分配固定的战斗场景
        self._initialize_boss_configurations()
        
        return {
            'success': True,
            'maze_size': self.maze_size,
            'maze_info': self.maze_generator.get_maze_info(),
            'start_pos': self.start_pos,
            'exit_pos': self.exit_pos
        }
    
    def _find_start_and_exit(self):
        """
        找到迷宫中的起点和终点
        """
        for i in range(self.maze_size):
            for j in range(self.maze_size):
                if self.maze[i][j] == Config.START:
                    self.start_pos = (i, j)
                elif self.maze[i][j] == Config.EXIT:
                    self.exit_pos = (i, j)
    
    def _reset_game_state(self):
        """
        重置游戏状态
        """
        self.player_resources = 100
        self.collected_items = set()
        self.solved_puzzles = set()
        self.defeated_bosses = set()
        self.moves_count = 0

        self.puzzles_attempted = 0
        self.battles_fought = 0
        self.active_puzzle = None
        self.active_battle = None
        self.boss_configurations = {}  # 重置boss配置
        
        # 重置自动拾取状态
        self.auto_pickup_path = []
        self.auto_pickup_target = None
    
    def _initialize_boss_configurations(self):
        """
        为每个boss位置分配固定的战斗场景，确保重复进入时难度不变
        """
        self.boss_configurations = {}
        scenarios = list(Config.MULTI_BATTLE_SCENARIOS.keys())
        
        # 找到所有boss位置
        for i in range(self.maze_size):
            for j in range(self.maze_size):
                if self.maze[i][j] == Config.BOSS:
                    # 为每个boss位置随机分配一个战斗场景（但在游戏过程中保持不变）
                    selected_scenario = random.choice(scenarios)
                    self.boss_configurations[(i, j)] = selected_scenario
    
    def get_game_state(self) -> Dict:
        """
        获取当前游戏状态
        
        Returns:
            Dict: 游戏状态信息
        """
        return {
            'player_pos': self.player_pos,
            'player_resources': self.player_resources,
            'moves_count': self.moves_count,

            'collected_items': len(self.collected_items),
            'solved_puzzles': len(self.solved_puzzles),
            'defeated_bosses': len(self.defeated_bosses),
            'puzzles_attempted': self.puzzles_attempted,
            'battles_fought': self.battles_fought,
            'active_puzzle': self.active_puzzle,
            'active_battle': self.active_battle,
            'game_completed': self.is_game_completed()
        }
    
    def move_player(self, direction: str) -> Dict:
        """
        移动玩家
        
        Args:
            direction: 移动方向 ('up', 'down', 'left', 'right')
        
        Returns:
            Dict: 移动结果
        """
        if not self.player_pos:
            return {'success': False, 'message': '游戏未初始化'}
        
        # 方向映射
        direction_map = {
            'up': (-1, 0),
            'down': (1, 0),
            'left': (0, -1),
            'right': (0, 1)
        }
        
        if direction not in direction_map:
            return {'success': False, 'message': '无效的移动方向'}
        
        dx, dy = direction_map[direction]
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # 检查边界和墙壁
        if (0 <= new_x < self.maze_size and 0 <= new_y < self.maze_size and 
            self.maze[new_x][new_y] != Config.WALL):
            
            # 清除之前位置的待交互状态
            self.pending_interaction = None
            
            self.player_pos = (new_x, new_y)
            self.moves_count += 1
            
            # 处理当前位置的元素
            interaction_result = self._handle_cell_interaction(new_x, new_y)
            
            return {
                'success': True,
                'new_position': self.player_pos,
                'moves_count': self.moves_count,
                'interaction': interaction_result
            }
        else:
            return {'success': False, 'message': '无法移动到该位置'}
    
    def _handle_cell_interaction(self, x: int, y: int) -> Dict:
        """
        处理玩家与格子的交互
        
        Args:
            x, y: 格子坐标
        
        Returns:
            Dict: 交互结果
        """
        cell = self.maze[x][y]
        result = {'type': 'none', 'message': '', 'value_change': 0}
        
        if (x, y) in self.collected_items:
            return result  # 已经收集过的物品
        
        if cell == Config.GOLD:
            self.player_resources += Config.RESOURCE_VALUE
            self.collected_items.add((x, y))
            result = {
                'type': 'resource',
                'message': f'收集到资源！获得{Config.RESOURCE_VALUE}资源'
            }
        
        elif cell == Config.TRAP:
            # 陷阱只消耗资源，不影响血量
            resource_cost = Config.TRAP_RESOURCE_COST
            self.player_resources -= resource_cost
            self.collected_items.add((x, y))
            result = {
                'type': 'trap',
                'message': f'触发陷阱！消耗{resource_cost}资源'
            }
        
        elif cell == Config.LOCKER:
            if (x, y) not in self.solved_puzzles:
                puzzle = self.puzzle_solver.generate_password_puzzle()
                self.pending_interaction = {
                    'position': (x, y),
                    'puzzle': puzzle,
                    'type': 'puzzle'
                }
                result = {
                    'type': 'pending_puzzle',
                    'message': '发现密码锁！按Enter键进行交互',
                    'puzzle': puzzle
                }
        
        elif cell == Config.BOSS:
            if (x, y) not in self.defeated_bosses:
                # 使用预设的战斗场景配置，确保重复进入时难度不变
                selected_scenario = self.boss_configurations.get((x, y), 'medium')  # 默认中等难度
                
                self.pending_interaction = {
                    'position': (x, y),
                    'type': 'multi_monster_battle',
                    'scenario': selected_scenario
                }
                
                result = {
                    'type': 'pending_multi_monster_battle',
                    'message': f'遭遇怪物群！{Config.MULTI_BATTLE_SCENARIOS[selected_scenario]["name"]} 按Enter键开始战斗',
                    'scenario': selected_scenario
                }
        
        elif cell == Config.EXIT:
            result = {
                'type': 'exit',
                'message': '到达终点！',
                'game_completed': self.is_game_completed()
            }
        
        return result
    
    def interact_with_special_cell(self) -> Dict:
        """
        与当前位置的特殊方格进行交互（按Enter键触发）
        
        Returns:
            Dict: 交互结果
        """
        if not self.pending_interaction:
            return {'success': False, 'message': '当前位置没有可交互的内容'}
        
        interaction = self.pending_interaction
        self.pending_interaction = None  # 清除待交互状态
        
        if interaction['type'] == 'puzzle':
            self.active_puzzle = {
                'position': interaction['position'],
                'puzzle': interaction['puzzle'],
                'type': 'password'
            }
            return {
                'success': True,
                'type': 'puzzle',
                'message': '进入解谜界面...',
                'puzzle': interaction['puzzle']
            }
        
        elif interaction['type'] == 'multi_monster_battle':
            # 开始多怪物战斗
            self.start_multi_monster_battle(interaction['scenario'])
            return {
                'success': True,
                'type': 'multi_monster_battle',
                'message': f'开始战斗！{Config.MULTI_BATTLE_SCENARIOS[interaction["scenario"]]["name"]}',
                'scenario': interaction['scenario']
            }
        
        return {'success': False, 'message': '未知的交互类型'}
    
    # 旧的Boss战斗系统方法 - 已被多怪物战斗系统替代
    # def get_battle_state(self) -> Optional[Dict]:
    #     """
    #     获取当前战斗状态
    #     """
    #     if not self.active_battle:
    #         return None
    #     
    #     return {
    #         'boss_hp': self.active_battle.get('boss_hp'),
    #         'player_hp': self.player_hp,
    #         'player_resources': self.player_resources,
    #         'skill_cooldowns': self.active_battle.get('skill_cooldowns', {}),
    #         'available_skills': self.get_available_skills()
    #     }

    # 旧的Boss战斗系统方法 - 已被多怪物战斗系统替代
    # def get_available_skills(self) -> Dict[str, bool]:
    #     """
    #     获取当前可用的战斗技能
    #     """
    #     if not self.active_battle:
    #         return {}
    #     
    #     available = {}
    #     for skill_name, properties in Config.SKILLS.items():
    #         can_use = True
    #         if self.player_resources < properties['cost']:
    #             can_use = False
    #         if self.active_battle.get('skill_cooldowns', {}).get(skill_name, 0) > 0:
    #             can_use = False
    #         available[skill_name] = can_use
    #     return available

    # 旧的Boss战斗系统方法 - 已被多怪物战斗系统替代
    # def execute_battle_turn(self, player_action: str) -> Dict:
    #     """
    #     执行一个完整的战斗回合：玩家行动，然后Boss行动
    #     """
    #     if not self.active_battle or player_action not in Config.SKILLS:
    #         return {'success': False, 'message': '无效的操作'}
    #         
    #     turn_result = {
    #         'player_action': {'skill': player_action, 'damage': 0, 'heal': 0},
    #         'boss_action': {'damage': 0},
    #         'status': 'ongoing',
    #         'success': True
    #     }
    # 
    #     # 更新冷却时间
    #     for skill in self.active_battle['skill_cooldowns']:
    #         if self.active_battle['skill_cooldowns'][skill] > 0:
    #             self.active_battle['skill_cooldowns'][skill] -= 1
    # 
    #     # 1. 玩家行动
    #     skill = Config.SKILLS[player_action]
    #     if not self.get_available_skills().get(player_action):
    #         return {'success': False, 'message': f"无法使用 '{skill['name']}'"}
    # 
    #     self.player_resources -= skill['cost']
    #     self.active_battle['skill_cooldowns'][player_action] = skill['cooldown']
    #     
    #     if 'damage' in skill:
    #         damage = skill['damage']
    #         self.active_battle['boss_hp'] -= damage
    #         turn_result['player_action']['damage'] = damage
    #     
    #     if 'heal_amount' in skill:
    #         heal = skill['heal_amount']
    #         self.player_hp = min(self.active_battle['initial_player_hp'], self.player_hp + heal)
    #         turn_result['player_action']['heal'] = heal
    # 
    #     # 检查Boss是否被击败
    #     if self.active_battle['boss_hp'] <= 0:
    #         self.active_battle['boss_hp'] = 0
    #         turn_result['status'] = 'victory'
    #         self.defeated_bosses.add(self.active_battle['position'])
    #         reward = 50
    #         self.player_resources += reward
    #         self.total_value_collected += reward
    #         turn_result['reward'] = reward
    #         turn_result['message'] = f"你赢了！获得 {reward} 资源奖励。"
    #         self.active_battle = None
    #         return turn_result
    # 
    #     # 2. Boss行动 (简单AI：直接攻击)
    #     boss_damage = Config.BOSS_ATTACK_DAMAGE
    #     self.player_hp -= boss_damage
    #     turn_result['boss_action']['damage'] = boss_damage
    # 
    #     # 检查玩家是否被击败
    #     if self.player_hp <= 0:
    #         self.player_hp = 0
    #         turn_result['status'] = 'defeat'
    #         turn_result['message'] = "你被击败了！"
    #         self.player_hp = self.active_battle['initial_player_hp'] // 2 # 惩罚：半血复活
    #         self.active_battle = None
    #         return turn_result
    #         
    #     return turn_result
    
    def solve_puzzle(self, puzzle_type: str = 'auto') -> Dict:
        """
        解决当前谜题
        
        Args:
            puzzle_type: 解谜方式 ('auto' 为AI自动解谜)
        
        Returns:
            Dict: 解谜结果
        """
        if not self.active_puzzle:
            return {'success': False, 'message': '没有活跃的谜题'}
        
        self.puzzles_attempted += 1
        puzzle_data = self.active_puzzle['puzzle']
        
        if puzzle_type == 'auto':
            if self.active_puzzle['type'] == 'password':
                solution, attempts = self.puzzle_solver.solve_password_puzzle(puzzle_data['clues'])
                
                if solution:
                    self.solved_puzzles.add(self.active_puzzle['position'])
                    reward = 20  # 解谜奖励
                    self.player_resources += reward

                    
                    result = {
                        'success': True,
                        'solution': solution,
                        'attempts': attempts,
                        'reward': reward,
                        'message': f'谜题解决！密码是{"".join(map(str, solution))}，获得{reward}资源奖励'
                    }
                    
                    self.active_puzzle = None
                    return result
                else:
                    return {
                        'success': False,
                        'attempts': attempts,
                        'message': '谜题解决失败，请重试'
                    }
        
        return {'success': False, 'message': '不支持的解谜方式'}
    
    # 旧的Boss战斗系统方法 - 已被多怪物战斗系统替代
    # def fight_boss(self, strategy_type: str = 'optimal') -> Dict:
    #     """
    #     与BOSS战斗
    #     
    #     Args:
    #         strategy_type: 战斗策略类型 ('optimal', 'random')
    #     
    #     Returns:
    #         Dict: 战斗结果
    #     """
    #     if not self.active_battle:
    #         return {'success': False, 'message': '没有活跃的战斗'}
    #     
    #     self.battles_fought += 1
    #     
    #     if strategy_type == 'optimal':
    #         # 使用分支限界算法找最优策略
    #         boss_strategy = BossStrategy(
    #             boss_hp=self.active_battle['boss_hp'],
    #             player_resources=self.player_resources
    #         )
    #         
    #         optimal_sequence, rounds_needed, stats = boss_strategy.find_optimal_strategy()
    #         
    #         if optimal_sequence:
    #             # 模拟战斗
    #             battle_result = boss_strategy.simulate_battle(optimal_sequence)
    #             
    #             if battle_result['success']:
    #                 self.defeated_bosses.add(self.active_battle['position'])
    #                 self.player_resources = battle_result['final_resources']
    #                 
    #                 reward = 50  # 击败BOSS奖励
    #                 self.player_resources += reward
    # 
    #                 
    #                 result = {
    #                     'success': True,
    #                     'strategy': optimal_sequence,
    #                     'rounds_used': battle_result['rounds_used'],
    #                     'reward': reward,
    #                     'stats': stats,
    #                     'battle_log': battle_result['battle_log'],
    #                     'message': f'击败BOSS！用时{battle_result["rounds_used"]}回合，获得{reward}资源奖励'
    #                 }
    #                 
    #                 self.active_battle = None
    #                 return result
    #             else:
    #                 return {
    #                     'success': False,
    #                     'reason': battle_result['reason'],
    #                     'message': '战斗失败，请重试'
    #                 }
    #         else:
    #             return {
    #                 'success': False,
    #                 'message': '无法找到获胜策略，资源不足或BOSS太强'
    #             }
    #     
    #     elif strategy_type == 'random':
    #         # 使用随机策略
    #         boss_strategy = BossStrategy(
    #             boss_hp=self.active_battle['boss_hp'],
    #             player_resources=self.player_resources
    #         )
    #         
    #         random_strategies = boss_strategy.generate_random_strategies(count=10)
    #         comparison = boss_strategy.compare_strategies(random_strategies)
    #         
    #         if comparison['best_strategy']:
    #             best_strategy = comparison['best_strategy']['strategy']
    #             battle_result = boss_strategy.simulate_battle(best_strategy)
    #             
    #             if battle_result['success']:
    #                 self.defeated_bosses.add(self.active_battle['position'])
    #                 self.player_resources = battle_result['final_resources']
    #                 
    #                 reward = 30  # 随机策略奖励较少
    #                 self.player_resources += reward
    #                 self.total_value_collected += reward
    #                 
    #                 result = {
    #                     'success': True,
    #                     'strategy': best_strategy,
    #                     'rounds_used': battle_result['rounds_used'],
    #                     'reward': reward,
    #                     'comparison': comparison,
    #                     'battle_log': battle_result['battle_log'],
    #                     'message': f'击败BOSS！用时{battle_result["rounds_used"]}回合，获得{reward}资源奖励'
    #                 }
    #                 
    #                 self.active_battle = None
    #                 return result
    #     
    #     return {'success': False, 'message': '战斗策略执行失败'}
    
    def start_multi_monster_battle(self, scenario_name: str = 'medium') -> Dict:
        """
        开始多怪物战斗
        
        Args:
            scenario_name: 战斗场景名称
        
        Returns:
            Dict: 战斗开始结果
        """
        if scenario_name not in Config.MULTI_BATTLE_SCENARIOS:
            return {'success': False, 'message': f'未知的战斗场景: {scenario_name}'}
        
        scenario = Config.MULTI_BATTLE_SCENARIOS[scenario_name]
        
        # 创建怪物配置
        monster_configs = []
        for monster_type in scenario['monsters']:
            if monster_type not in Config.MONSTER_TYPES:
                return {'success': False, 'message': f'未知的怪物类型: {monster_type}'}
            monster_config = Config.MONSTER_TYPES[monster_type].copy()
            monster_configs.append(monster_config)
        
        # 创建多怪物战斗实例
        self.active_multi_battle = MultiMonsterBattle(monster_configs)
        self.battles_fought += 1
        
        return {
            'success': True,
            'scenario_name': scenario_name,
            'scenario_display_name': scenario['name'],
            'monster_count': len(monster_configs),
            'monsters': [config['name'] for config in monster_configs],
            'message': f'开始{scenario["name"]}！面对{len(monster_configs)}个怪物！'
        }
    
    def get_multi_battle_state(self) -> Optional[Dict]:
        """
        获取多怪物战斗状态
        
        Returns:
            Optional[Dict]: 战斗状态，如果没有活跃战斗则返回None
        """
        if not self.active_multi_battle:
            return None
        
        return self.active_multi_battle.get_battle_state()
    
    def execute_multi_battle_turn(self, skill_name: str, target_monster_id: Optional[int] = None) -> Dict:
        """
        执行多怪物战斗回合
        
        Args:
            skill_name: 使用的技能名称
            target_monster_id: 目标怪物ID（攻击技能需要）
        
        Returns:
            Dict: 回合执行结果
        """
        if not self.active_multi_battle:
            return {'success': False, 'message': '没有活跃的多怪物战斗'}
        
        # 执行玩家回合
        result = self.active_multi_battle.execute_player_turn(skill_name, target_monster_id)
        
        if result['success']:
            # 检查战斗是否结束
            battle_result = self.active_multi_battle.get_battle_result()
            
            if battle_result['status'] == 'victory':
                # 胜利
                reward = battle_result['reward']
                self.player_resources += reward
                self.total_value_collected += reward
                
                result['battle_result'] = battle_result
                result['reward'] = reward
                result['message'] = battle_result['message']
                
                # 清除活跃战斗
                self.active_multi_battle = None
                
            elif battle_result['status'] == 'defeat':
                # 失败
                self.player_hp = max(1, self.player_hp // 2)  # 惩罚：减半生命值，但至少保留1点
                
                result['battle_result'] = battle_result
                result['message'] = battle_result['message']
                
                # 清除活跃战斗
                self.active_multi_battle = None
        
        return result
    
    def get_multi_battle_target_suggestion(self) -> Optional[int]:
        """
        获取多怪物战斗的最优目标建议
        
        Returns:
            Optional[int]: 建议的目标怪物ID
        """
        if not self.active_multi_battle:
            return None
        
        return self.active_multi_battle.get_optimal_target_suggestion()
    
    def get_optimal_path(self) -> Dict:
        """
        获取动态规划最优路径
        
        Returns:
            Dict: 最优路径信息
        """
        if not self.path_planner:
            return {'success': False, 'message': '路径规划器未初始化'}
        
        max_value, optimal_path = self.path_planner.find_optimal_path()
        path_details = self.path_planner.get_path_details(optimal_path)
        
        return {
            'success': True,
            'max_value': max_value,
            'optimal_path': optimal_path,
            'path_details': path_details
        }
    
    def get_greedy_path(self) -> Dict:
        """
        获取贪心策略路径
        
        Returns:
            Dict: 贪心路径信息
        """
        if not self.greedy_strategy or not self.start_pos:
            return {'success': False, 'message': '贪心策略未初始化'}
        
        greedy_path, total_value = self.greedy_strategy.greedy_resource_collection(self.start_pos)
        efficiency_analysis = self.greedy_strategy.analyze_strategy_efficiency(self.start_pos)
        
        return {
            'success': True,
            'greedy_path': greedy_path,
            'total_value': total_value,
            'efficiency_analysis': efficiency_analysis
        }
    
    def compare_path_strategies(self) -> Dict:
        """
        比较动态规划和贪心策略的路径
        
        Returns:
            Dict: 路径策略比较结果
        """
        dp_result = self.get_optimal_path()
        greedy_result = self.get_greedy_path()
        
        if not dp_result['success'] or not greedy_result['success']:
            return {'success': False, 'message': '路径计算失败'}
        
        # 使用路径规划器的比较功能
        comparison = self.path_planner.compare_with_greedy(greedy_result['greedy_path'])
        
        return {
            'success': True,
            'dp_result': dp_result,
            'greedy_result': greedy_result,
            'comparison': comparison
        }
    
    def toggle_auto_pickup(self) -> Dict:
        """
        切换自动拾取功能开关
        
        Returns:
            Dict: 切换结果
        """
        self.auto_pickup_enabled = not self.auto_pickup_enabled
        
        if not self.auto_pickup_enabled:
            # 关闭自动拾取时清除路径
            self.auto_pickup_path = []
            self.auto_pickup_target = None
        
        return {
            'success': True,
            'auto_pickup_enabled': self.auto_pickup_enabled,
            'message': f'自动拾取功能已{"开启" if self.auto_pickup_enabled else "关闭"}'
        }
    
    def get_auto_pickup_status(self) -> Dict:
        """
        获取自动拾取状态信息
        
        Returns:
            Dict: 自动拾取状态
        """
        return {
            'enabled': self.auto_pickup_enabled,
            'has_target': self.auto_pickup_target is not None,
            'target_position': self.auto_pickup_target['position'] if self.auto_pickup_target else None,
            'target_type': self.auto_pickup_target['type'] if self.auto_pickup_target else None,
            'target_value': self.auto_pickup_target['value'] if self.auto_pickup_target else None,
            'path_length': len(self.auto_pickup_path),
            'remaining_steps': len(self.auto_pickup_path)
        }
    
    def find_best_resource_in_vision(self) -> Optional[Dict]:
        """
        在玩家周围3x3区域内找到性价比最高的资源
        
        Returns:
            Optional[Dict]: 最佳资源信息，如果没有资源则返回None
        """
        if not self.maze:
            return None
        
        # 获取玩家周围3x3区域的所有资源
        resources = self._get_resources_in_3x3_area()
        available_resources = [r for r in resources if r['position'] not in self.collected_items]
        
        if not available_resources:
            return None
        
        # 优先选择正价值资源，按性价比排序
        positive_resources = [r for r in available_resources if r['value'] > 0]
        
        if positive_resources:
            return max(positive_resources, key=lambda x: x['cost_benefit'])
        else:
            # 如果只有陷阱，选择伤害最小的
            return min(available_resources, key=lambda x: abs(x['value']))
    
    def _get_resources_in_3x3_area(self) -> List[Dict]:
        """
        获取玩家周围3x3区域内的所有资源
        
        Returns:
            List[Dict]: 资源信息列表
        """
        if not self.player_pos:
            return []
        
        x, y = self.player_pos
        resources = []
        
        # 遍历玩家周围3x3区域（包括玩家当前位置）
        for i in range(max(0, x - 1), min(self.maze_size, x + 2)):
            for j in range(max(0, y - 1), min(self.maze_size, y + 2)):
                cell = self.maze[i][j]
                
                # 只考虑有价值的资源（资源和陷阱）
                if cell in [Config.GOLD, Config.TRAP]:
                    distance = abs(i - x) + abs(j - y)  # 曼哈顿距离
                    value = self._get_cell_value(cell)
                    
                    # 计算性价比（价值/距离），距离为0时设为最高优先级
                    cost_benefit = value / max(1, distance) if distance > 0 else value * 10
                    
                    resources.append({
                        'position': (i, j),
                        'type': cell,
                        'value': value,
                        'distance': distance,
                        'cost_benefit': cost_benefit
                    })
        
        return resources
    
    def _get_cell_value(self, cell: str) -> int:
        """
        获取格子的价值
        
        Args:
            cell: 格子类型
        
        Returns:
            int: 格子价值
        """
        if cell == Config.GOLD:
            return Config.RESOURCE_VALUE
        elif cell == Config.TRAP:
            return -Config.TRAP_RESOURCE_COST
        else:
            return 0
    
    def calculate_path_to_resource(self, target_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        计算到达目标资源的路径（3x3区域内的简单路径）
        
        Args:
            target_pos: 目标位置
        
        Returns:
            List[Tuple[int, int]]: 路径坐标列表
        """
        if not self.player_pos:
            return []
        
        # 对于3x3区域内的移动，使用简单的直线路径
        current_x, current_y = self.player_pos
        target_x, target_y = target_pos
        
        path = [self.player_pos]
        
        # 先水平移动，再垂直移动
        while current_x != target_x or current_y != target_y:
            if current_x < target_x:
                current_x += 1
            elif current_x > target_x:
                current_x -= 1
            elif current_y < target_y:
                current_y += 1
            elif current_y > target_y:
                current_y -= 1
            
            # 检查是否可以移动到该位置
            if (0 <= current_x < self.maze_size and 0 <= current_y < self.maze_size and 
                self.maze[current_x][current_y] != Config.WALL):
                path.append((current_x, current_y))
            else:
                # 如果遇到墙壁，返回空路径
                return []
        
        return path
    
    def execute_auto_pickup_step(self) -> Dict:
        """
        执行一步自动拾取操作
        
        Returns:
            Dict: 执行结果
        """
        if not self.auto_pickup_enabled:
            return {'success': False, 'message': '自动拾取功能未开启'}
        
        # 如果没有当前目标或路径，寻找新目标
        if not self.auto_pickup_target or not self.auto_pickup_path:
            best_resource = self.find_best_resource_in_vision()
            
            if not best_resource:
                return {
                    'success': True,
                    'action': 'no_resources',
                    'message': '视野内没有可拾取的资源'
                }
            
            # 计算到达目标的路径
            path = self.calculate_path_to_resource(best_resource['position'])
            
            if not path:
                return {
                    'success': False,
                    'action': 'path_blocked',
                    'message': '无法到达目标资源'
                }
            
            # 设置新目标和路径
            self.auto_pickup_target = best_resource
            self.auto_pickup_path = path[1:]  # 排除当前位置
        
        # 如果已到达目标位置，清除目标并寻找下一个
        if self.player_pos == self.auto_pickup_target['position']:
            self.auto_pickup_target = None
            self.auto_pickup_path = []
            return {
                'success': True,
                'action': 'target_reached',
                'message': '已到达目标资源位置'
            }
        
        # 执行下一步移动
        if self.auto_pickup_path:
            next_pos = self.auto_pickup_path[0]
            self.auto_pickup_path = self.auto_pickup_path[1:]
            
            # 计算移动方向
            direction = self._get_direction(self.player_pos, next_pos)
            
            # 执行移动
            move_result = self.move_player(direction)
            
            if move_result['success']:
                return {
                    'success': True,
                    'action': 'moved',
                    'direction': direction,
                    'new_position': move_result['new_position'],
                    'interaction': move_result.get('interaction', {}),
                    'target_info': {
                        'position': self.auto_pickup_target['position'],
                        'type': self.auto_pickup_target['type'],
                        'value': self.auto_pickup_target['value'],
                        'remaining_steps': len(self.auto_pickup_path)
                    }
                }
            else:
                # 移动失败，清除当前路径重新规划
                self.auto_pickup_path = []
                self.auto_pickup_target = None
                return {
                    'success': False,
                    'action': 'move_failed',
                    'message': '移动失败，重新规划路径'
                }
        
        return {
            'success': False,
            'action': 'no_path',
            'message': '没有可执行的路径'
        }
    
    def auto_pickup_until_complete(self, max_steps: int = 1000) -> Dict:
        """
        持续执行自动拾取直到视野内没有资源或达到最大步数
        
        Args:
            max_steps: 最大执行步数，防止无限循环
        
        Returns:
            Dict: 执行结果统计
        """
        if not self.auto_pickup_enabled:
            return {'success': False, 'message': '自动拾取功能未开启'}
        
        steps_taken = 0
        resources_collected = 0

        execution_log = []
        
        while steps_taken < max_steps:
            step_result = self.execute_auto_pickup_step()
            steps_taken += 1
            
            execution_log.append({
                'step': steps_taken,
                'result': step_result
            })
            
            if not step_result['success']:
                if step_result.get('action') == 'no_resources':
                    break  # 正常结束：没有更多资源
                else:
                    continue  # 继续尝试
            
            # 检查是否收集到资源
            if step_result.get('interaction', {}).get('type') in ['gold', 'trap']:
                resources_collected += 1
            
            # 如果没有更多资源可拾取，结束
            if step_result.get('action') == 'no_resources':
                break
        
        return {
            'success': True,
            'steps_taken': steps_taken,
            'resources_collected': resources_collected,
            'final_position': self.player_pos,
            'execution_log': execution_log[-10:] if len(execution_log) > 10 else execution_log,  # 只保留最后10步
            'message': f'自动拾取完成：执行{steps_taken}步，收集{resources_collected}个资源'
        }
    

    

    

    
    def _get_direction(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """
        获取从一个位置到另一个位置的方向
        
        Args:
            from_pos: 起始位置
            to_pos: 目标位置
        
        Returns:
            str: 移动方向
        """
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        if dx > 0:
            return 'down'
        elif dx < 0:
            return 'up'
        elif dy > 0:
            return 'right'
        elif dy < 0:
            return 'left'
        else:
            return 'up'  # 默认方向
    
    def is_game_completed(self) -> bool:
        """
        检查游戏是否完成
        
        Returns:
            bool: 游戏是否完成
        """
        return self.player_pos == self.exit_pos
    
    def get_game_statistics(self) -> Dict:
        """
        获取游戏统计信息
        
        Returns:
            Dict: 游戏统计
        """
        maze_info = self.maze_generator.get_maze_info() if self.maze_generator else {}
        
        return {
            'maze_info': maze_info,
            'player_stats': {
                'final_position': self.player_pos,
                'moves_count': self.moves_count,
                'final_resources': self.player_resources,

            },
            'collection_stats': {
                'items_collected': len(self.collected_items),
                'puzzles_solved': len(self.solved_puzzles),
                'bosses_defeated': len(self.defeated_bosses),
                'puzzles_attempted': self.puzzles_attempted,
                'battles_fought': self.battles_fought
            },
            'efficiency_metrics': {
                'completion_rate': 1.0 if self.is_game_completed() else 0.0
            }
        }
    

    
    def save_game_state(self, filename: str) -> Dict:
        """
        保存游戏状态
        
        Args:
            filename: 保存文件名
        
        Returns:
            Dict: 保存结果
        """
        try:
            game_data = {
                'maze': self.maze,
                'maze_size': self.maze_size,
                'player_pos': self.player_pos,
                'start_pos': self.start_pos,
                'exit_pos': self.exit_pos,
                'game_state': self.get_game_state(),
                'statistics': self.get_game_statistics()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            
            return {'success': True, 'message': f'游戏状态已保存到 {filename}'}
        
        except Exception as e:
            return {'success': False, 'message': f'保存失败: {str(e)}'}
    
    def export_maze_data(self, filename: str) -> Dict:
        """
        导出迷宫数据
        
        Args:
            filename: 导出文件名
        
        Returns:
            Dict: 导出结果
        """
        if self.maze_generator:
            try:
                self.maze_generator.save_maze_to_json(filename)
                return {'success': True, 'message': f'迷宫数据已导出到 {filename}'}
            except Exception as e:
                return {'success': False, 'message': f'导出失败: {str(e)}'}
        else:
            return {'success': False, 'message': '迷宫未生成'}
    
    # ==================== 资源路径规划功能 ====================
    
    def find_optimal_resource_path(self, max_resources: int = None) -> Dict:
        """
        找到从当前位置到终点的最优资源收集路径
        
        Args:
            max_resources: 最大收集资源数量限制
        
        Returns:
            Dict: 最优路径结果
        """
        if not self.resource_path_planner:
            return {
                'success': False,
                'message': '资源路径规划器未初始化',
                'path': [],
                'total_value': 0
            }
        
        # 临时更新起点为当前玩家位置
        original_start = self.resource_path_planner.start_pos
        self.resource_path_planner.start_pos = self.player_pos
        
        try:
            result = self.resource_path_planner.find_optimal_resource_path(max_resources)
            return result
        finally:
            # 恢复原始起点
            self.resource_path_planner.start_pos = original_start
    
    def get_auto_navigation_to_exit(self) -> Dict:
        """
        获取从当前位置到出口的自动导航路径
        
        Returns:
            Dict: 导航结果
        """
        if not self.resource_path_planner:
            return {
                'success': False,
                'message': '资源路径规划器未初始化',
                'steps': []
            }
        
        # 使用A*算法找到最短路径
        path = self.resource_path_planner._a_star_path(self.player_pos, self.exit_pos)
        
        if not path:
            return {
                'success': False,
                'message': '无法找到到达出口的路径',
                'steps': []
            }
        
        # 获取导航步骤
        steps = self.resource_path_planner.get_auto_navigation_steps(path, self.player_pos)
        
        return {
            'success': True,
            'path': path,
            'steps': steps,
            'total_steps': len(steps),
            'message': f'找到到达出口的路径，共需{len(steps)}步'
        }
    
    def get_auto_navigation_to_nearest_resource(self) -> Dict:
        """
        获取到最近资源的自动导航路径
        
        Returns:
            Dict: 导航结果
        """
        if not self.resource_path_planner:
            return {
                'success': False,
                'message': '资源路径规划器未初始化',
                'steps': []
            }
        
        # 找到所有未收集的资源
        available_resources = []
        for resource in self.resource_path_planner.resources:
            pos = resource['position']
            if pos not in self.collected_items and resource['value'] > 0:  # 只考虑正价值资源
                available_resources.append(resource)
        
        if not available_resources:
            return {
                'success': False,
                'message': '没有可收集的资源',
                'steps': []
            }
        
        # 找到最近的资源
        nearest_resource = min(available_resources, 
                             key=lambda r: self.resource_path_planner._manhattan_distance(
                                 self.player_pos, r['position']))
        
        target_pos = nearest_resource['position']
        path = self.resource_path_planner._a_star_path(self.player_pos, target_pos)
        
        if not path:
            return {
                'success': False,
                'message': f'无法到达资源位置 {target_pos}',
                'steps': []
            }
        
        steps = self.resource_path_planner.get_auto_navigation_steps(path, self.player_pos)
        
        return {
            'success': True,
            'path': path,
            'steps': steps,
            'target_resource': nearest_resource,
            'total_steps': len(steps),
            'message': f'找到最近资源路径，共需{len(steps)}步'
        }
    
    def get_resource_path_alternatives(self, num_alternatives: int = 3) -> List[Dict]:
        """
        获取多个资源收集路径方案
        
        Args:
            num_alternatives: 备选方案数量
        
        Returns:
            List[Dict]: 备选路径列表
        """
        if not self.resource_path_planner:
            return []
        
        # 临时更新起点为当前玩家位置
        original_start = self.resource_path_planner.start_pos
        self.resource_path_planner.start_pos = self.player_pos
        
        try:
            alternatives = self.resource_path_planner.get_alternative_paths(num_alternatives)
            
            # 为每个方案添加导航步骤
            for alt in alternatives:
                if alt.get('success') and alt.get('path'):
                    steps = self.resource_path_planner.get_auto_navigation_steps(
                        alt['path'], self.player_pos)
                    alt['navigation_steps'] = steps
                    alt['total_steps'] = len(steps)
            
            return alternatives
        finally:
            # 恢复原始起点
            self.resource_path_planner.start_pos = original_start
    
    def analyze_current_path_efficiency(self) -> Dict:
        """
        分析当前玩家路径的效率
        
        Returns:
            Dict: 路径效率分析
        """
        if not self.resource_path_planner:
            return {
                'success': False,
                'message': '资源路径规划器未初始化'
            }
        
        # 构建玩家已走过的路径（简化版本）
        player_path = [self.start_pos, self.player_pos] if self.start_pos and self.player_pos else []
        
        if len(player_path) < 2:
            return {
                'success': False,
                'message': '路径数据不足'
            }
        
        analysis = self.resource_path_planner.analyze_path_efficiency(player_path)
        
        # 添加游戏状态信息
        analysis.update({
            'success': True,
            'current_resources': self.player_resources,
            'items_collected': len(self.collected_items),
            'moves_made': self.moves_count,

        })
        
        return analysis
    
    def execute_auto_navigation(self, steps: List[str]) -> Dict:
        """
        执行自动导航步骤
        
        Args:
            steps: 移动步骤列表
        
        Returns:
            Dict: 执行结果
        """
        if not steps:
            return {
                'success': False,
                'message': '没有导航步骤',
                'executed_steps': 0
            }
        
        executed_steps = 0
        results = []
        
        for step in steps:
            result = self.move_player(step)
            results.append(result)
            
            if result['success']:
                executed_steps += 1
            else:
                # 遇到障碍或错误，停止执行
                break
        
        return {
            'success': executed_steps > 0,
            'executed_steps': executed_steps,
            'total_steps': len(steps),
            'final_position': self.player_pos,
            'step_results': results,
            'message': f'成功执行{executed_steps}/{len(steps)}步导航'
        }