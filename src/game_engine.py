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

class GameEngine:
    """
    游戏引擎类
    """
    
    def __init__(self, maze_size: int = Config.DEFAULT_MAZE_SIZE):
        """
        初始化游戏引擎
        
        Args:
            maze_size: 迷宫大小
        """
        self.maze_size = maze_size
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
        
        # 游戏状态
        self.player_resources = 100
        self.player_hp = 100
        self.collected_items = set()
        self.solved_puzzles = set()
        self.defeated_bosses = set()
        
        # 游戏统计
        self.moves_count = 0
        self.total_value_collected = 0
        self.puzzles_attempted = 0
        self.battles_fought = 0
        
        # 当前活跃的谜题和战斗
        self.active_puzzle = None
        self.active_battle = None
        
        # 游戏模式
        self.ai_mode = True  # AI自动游戏模式
        self.visualization_enabled = True
    
    def initialize_game(self) -> Dict:
        """
        初始化游戏
        
        Returns:
            Dict: 初始化结果
        """
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
        
        # 重置游戏状态
        self._reset_game_state()
        
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
        self.player_hp = 100
        self.collected_items = set()
        self.solved_puzzles = set()
        self.defeated_bosses = set()
        self.moves_count = 0
        self.total_value_collected = 0
        self.puzzles_attempted = 0
        self.battles_fought = 0
        self.active_puzzle = None
        self.active_battle = None
    
    def get_game_state(self) -> Dict:
        """
        获取当前游戏状态
        
        Returns:
            Dict: 游戏状态信息
        """
        return {
            'player_pos': self.player_pos,
            'player_resources': self.player_resources,
            'player_hp': self.player_hp,
            'moves_count': self.moves_count,
            'total_value_collected': self.total_value_collected,
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
            self.total_value_collected += Config.GOLD_VALUE
            self.player_resources += Config.GOLD_VALUE
            self.collected_items.add((x, y))
            result = {
                'type': 'gold',
                'message': f'收集到金币！获得{Config.GOLD_VALUE}资源',
                'value_change': Config.GOLD_VALUE
            }
        
        elif cell == Config.TRAP:
            self.player_hp += Config.TRAP_DAMAGE  # 陷阱造成伤害
            self.total_value_collected += Config.TRAP_DAMAGE
            self.collected_items.add((x, y))
            result = {
                'type': 'trap',
                'message': f'触发陷阱！损失{-Config.TRAP_DAMAGE}生命值',
                'value_change': Config.TRAP_DAMAGE
            }
        
        elif cell == Config.LOCKER:
            if (x, y) not in self.solved_puzzles:
                puzzle = self.puzzle_solver.generate_password_puzzle()
                self.active_puzzle = {
                    'position': (x, y),
                    'puzzle': puzzle,
                    'type': 'password'
                }
                result = {
                    'type': 'puzzle',
                    'message': '发现密码锁！需要解谜',
                    'puzzle': puzzle
                }
        
        elif cell == Config.BOSS:
            if (x, y) not in self.defeated_bosses:
                self.active_battle = {
                    'position': (x, y),
                    'boss_hp': Config.BOSS_HP,
                    'type': 'boss'
                }
                result = {
                    'type': 'boss',
                    'message': '遭遇BOSS！准备战斗',
                    'boss_hp': Config.BOSS_HP
                }
        
        elif cell == Config.EXIT:
            result = {
                'type': 'exit',
                'message': '到达终点！',
                'game_completed': self.is_game_completed()
            }
        
        return result
    
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
                    self.total_value_collected += reward
                    
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
    
    def fight_boss(self, strategy_type: str = 'optimal') -> Dict:
        """
        与BOSS战斗
        
        Args:
            strategy_type: 战斗策略类型 ('optimal', 'random')
        
        Returns:
            Dict: 战斗结果
        """
        if not self.active_battle:
            return {'success': False, 'message': '没有活跃的战斗'}
        
        self.battles_fought += 1
        
        if strategy_type == 'optimal':
            # 使用分支限界算法找最优策略
            boss_strategy = BossStrategy(
                boss_hp=self.active_battle['boss_hp'],
                player_resources=self.player_resources
            )
            
            optimal_sequence, rounds_needed, stats = boss_strategy.find_optimal_strategy()
            
            if optimal_sequence:
                # 模拟战斗
                battle_result = boss_strategy.simulate_battle(optimal_sequence)
                
                if battle_result['success']:
                    self.defeated_bosses.add(self.active_battle['position'])
                    self.player_resources = battle_result['final_resources']
                    
                    reward = 50  # 击败BOSS奖励
                    self.player_resources += reward
                    self.total_value_collected += reward
                    
                    result = {
                        'success': True,
                        'strategy': optimal_sequence,
                        'rounds_used': battle_result['rounds_used'],
                        'reward': reward,
                        'stats': stats,
                        'battle_log': battle_result['battle_log'],
                        'message': f'击败BOSS！用时{battle_result["rounds_used"]}回合，获得{reward}资源奖励'
                    }
                    
                    self.active_battle = None
                    return result
                else:
                    return {
                        'success': False,
                        'reason': battle_result['reason'],
                        'message': '战斗失败，请重试'
                    }
            else:
                return {
                    'success': False,
                    'message': '无法找到获胜策略，资源不足或BOSS太强'
                }
        
        elif strategy_type == 'random':
            # 使用随机策略
            boss_strategy = BossStrategy(
                boss_hp=self.active_battle['boss_hp'],
                player_resources=self.player_resources
            )
            
            random_strategies = boss_strategy.generate_random_strategies(count=10)
            comparison = boss_strategy.compare_strategies(random_strategies)
            
            if comparison['best_strategy']:
                best_strategy = comparison['best_strategy']['strategy']
                battle_result = boss_strategy.simulate_battle(best_strategy)
                
                if battle_result['success']:
                    self.defeated_bosses.add(self.active_battle['position'])
                    self.player_resources = battle_result['final_resources']
                    
                    reward = 30  # 随机策略奖励较少
                    self.player_resources += reward
                    self.total_value_collected += reward
                    
                    result = {
                        'success': True,
                        'strategy': best_strategy,
                        'rounds_used': battle_result['rounds_used'],
                        'reward': reward,
                        'comparison': comparison,
                        'battle_log': battle_result['battle_log'],
                        'message': f'击败BOSS！用时{battle_result["rounds_used"]}回合，获得{reward}资源奖励'
                    }
                    
                    self.active_battle = None
                    return result
        
        return {'success': False, 'message': '战斗策略执行失败'}
    
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
    
    def auto_play_step(self) -> Dict:
        """
        AI自动游戏一步
        
        Returns:
            Dict: 自动游戏步骤结果
        """
        if not self.ai_mode:
            return {'success': False, 'message': 'AI模式未启用'}
        
        # 处理活跃的谜题或战斗
        if self.active_puzzle:
            return self.solve_puzzle('auto')
        
        if self.active_battle:
            return self.fight_boss('optimal')
        
        # 如果到达终点，游戏结束
        if self.player_pos == self.exit_pos:
            return {
                'success': True,
                'message': '游戏完成！',
                'game_completed': True,
                'final_stats': self.get_game_statistics()
            }
        
        # 使用贪心策略选择下一步移动
        visible_resources = self.greedy_strategy.get_resources_in_vision(self.player_pos)
        
        if visible_resources:
            # 有可见资源，移动到最佳资源
            best_resource = self.greedy_strategy.find_best_resource(self.player_pos)
            if best_resource:
                target_pos = best_resource['position']
                path = self.greedy_strategy.find_path_to_resource(self.player_pos, target_pos)
                
                if len(path) > 1:
                    next_pos = path[1]  # 下一步位置
                    direction = self._get_direction(self.player_pos, next_pos)
                    return self.move_player(direction)
        
        # 没有可见资源，朝终点移动
        if self.exit_pos:
            path = self.greedy_strategy.find_path_to_resource(self.player_pos, self.exit_pos)
            if len(path) > 1:
                next_pos = path[1]
                direction = self._get_direction(self.player_pos, next_pos)
                return self.move_player(direction)
        
        # 随机移动
        directions = ['up', 'down', 'left', 'right']
        random.shuffle(directions)
        
        for direction in directions:
            result = self.move_player(direction)
            if result['success']:
                return result
        
        return {'success': False, 'message': '无法移动'}
    
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
                'final_hp': self.player_hp,
                'total_value_collected': self.total_value_collected
            },
            'collection_stats': {
                'items_collected': len(self.collected_items),
                'puzzles_solved': len(self.solved_puzzles),
                'bosses_defeated': len(self.defeated_bosses),
                'puzzles_attempted': self.puzzles_attempted,
                'battles_fought': self.battles_fought
            },
            'efficiency_metrics': {
                'value_per_move': self.total_value_collected / max(1, self.moves_count),
                'completion_rate': 1.0 if self.is_game_completed() else 0.0,
                'resource_efficiency': self.total_value_collected / 100.0  # 相对于初始资源
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