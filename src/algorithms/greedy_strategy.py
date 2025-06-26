#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪心算法实时资源拾取策略
在有限视野下优先选择性价比最高的资源
"""

import math
from typing import List, Tuple, Dict, Optional
from ..config import Config

class GreedyStrategy:
    """
    贪心策略资源拾取器
    """
    
    def __init__(self, maze: List[List[str]]):
        """
        初始化贪心策略
        
        Args:
            maze: 迷宫矩阵
        """
        self.maze = maze
        self.size = len(maze)
        self.vision_range = Config.PLAYER_VISION_RANGE
    
    def get_visible_area(self, player_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        获取玩家视野范围内的所有位置
        
        Args:
            player_pos: 玩家当前位置
        
        Returns:
            List[Tuple[int, int]]: 视野内的位置列表
        """
        x, y = player_pos
        visible_positions = []
        
        # 计算视野范围
        for i in range(max(0, x - self.vision_range), 
                      min(self.size, x + self.vision_range + 1)):
            for j in range(max(0, y - self.vision_range), 
                          min(self.size, y + self.vision_range + 1)):
                # 检查是否在视野范围内（使用曼哈顿距离）
                if abs(i - x) + abs(j - y) <= self.vision_range:
                    visible_positions.append((i, j))
        
        return visible_positions
    
    def get_resources_in_vision(self, player_pos: Tuple[int, int]) -> List[Dict]:
        """
        获取视野内的所有资源信息
        
        Args:
            player_pos: 玩家当前位置
        
        Returns:
            List[Dict]: 资源信息列表
        """
        visible_positions = self.get_visible_area(player_pos)
        resources = []
        
        for pos in visible_positions:
            x, y = pos
            cell = self.maze[x][y]
            
            # 只考虑有价值的资源（金币和陷阱）
            if cell in [Config.GOLD, Config.TRAP]:
                distance = self._manhattan_distance(player_pos, pos)
                value = self._get_cell_value(cell)
                
                # 计算性价比（价值/距离）
                cost_benefit = value / max(1, distance)  # 避免除零
                
                resources.append({
                    'position': pos,
                    'type': cell,
                    'value': value,
                    'distance': distance,
                    'cost_benefit': cost_benefit
                })
        
        return resources
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """
        计算曼哈顿距离
        
        Args:
            pos1, pos2: 两个位置
        
        Returns:
            int: 曼哈顿距离
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _get_cell_value(self, cell: str) -> int:
        """
        获取格子的价值
        
        Args:
            cell: 格子类型
        
        Returns:
            int: 格子价值
        """
        if cell == Config.GOLD:
            return Config.GOLD_VALUE
        elif cell == Config.TRAP:
            return -Config.TRAP_RESOURCE_COST
        else:
            return 0
    
    def find_best_resource(self, player_pos: Tuple[int, int]) -> Optional[Dict]:
        """
        找到视野内性价比最高的资源
        
        Args:
            player_pos: 玩家当前位置
        
        Returns:
            Optional[Dict]: 最佳资源信息，如果没有资源则返回None
        """
        resources = self.get_resources_in_vision(player_pos)
        
        if not resources:
            return None
        
        # 按性价比排序，选择最高的
        resources.sort(key=lambda x: x['cost_benefit'], reverse=True)
        
        # 过滤掉陷阱（除非没有其他选择）
        positive_resources = [r for r in resources if r['value'] > 0]
        
        if positive_resources:
            return positive_resources[0]
        else:
            # 如果只有陷阱，选择伤害最小的
            return min(resources, key=lambda x: abs(x['value']))
    
    def find_path_to_resource(self, start: Tuple[int, int], target: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        使用A*算法找到到达目标资源的路径
        
        Args:
            start: 起始位置
            target: 目标位置
        
        Returns:
            List[Tuple[int, int]]: 路径坐标列表
        """
        from heapq import heappush, heappop
        
        # A*算法实现
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._manhattan_distance(start, target)}
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == target:
                # 重构路径
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            # 检查四个方向
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 检查边界和墙壁
                if (0 <= neighbor[0] < self.size and 0 <= neighbor[1] < self.size and 
                    self.maze[neighbor[0]][neighbor[1]] != Config.WALL):
                    
                    tentative_g_score = g_score[current] + 1
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self._manhattan_distance(neighbor, target)
                        heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # 无法到达目标
    
    def greedy_resource_collection(self, start_pos: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], int]:
        """
        贪心策略收集资源的完整路径
        
        Args:
            start_pos: 起始位置
        
        Returns:
            Tuple[List[Tuple[int, int]], int]: (完整路径, 总价值)
        """
        current_pos = start_pos
        total_path = [current_pos]
        total_value = 0
        
        while True:
            # 在当前视野内寻找最佳资源
            best_resource = self.find_best_resource(current_pos)
            
            if not best_resource:
                break  # 没有可见资源
            
            target_pos = best_resource['position']
            
            # 找到到达资源的路径
            path_to_resource = self.find_path_to_resource(current_pos, target_pos)
            
            if not path_to_resource:
                break  # 无法到达资源
            
            # 添加路径到总路径（排除起点重复）
            total_path.extend(path_to_resource[1:])
            
            # 更新当前位置和总价值
            current_pos = target_pos
            total_value += best_resource['value']
            
            # 将收集过的金币格子设为路径（删除资源）
            if self.maze[current_pos[0]][current_pos[1]] == Config.GOLD:
                self.maze[current_pos[0]][current_pos[1]] = Config.PATH
        
        return total_path, total_value
    
    def simulate_step_by_step(self, start_pos: Tuple[int, int]) -> List[Dict]:
        """
        模拟逐步的贪心决策过程
        
        Args:
            start_pos: 起始位置
        
        Returns:
            List[Dict]: 每一步的决策信息
        """
        current_pos = start_pos
        steps = []
        total_value = 0
        
        step_count = 0
        
        while step_count < 100:  # 防止无限循环
            step_count += 1
            
            # 获取当前视野内的资源
            visible_resources = self.get_resources_in_vision(current_pos)
            
            if not visible_resources:
                steps.append({
                    'step': step_count,
                    'position': current_pos,
                    'action': 'no_resources_visible',
                    'visible_resources': [],
                    'total_value': total_value
                })
                break
            
            # 选择最佳资源
            best_resource = max(visible_resources, key=lambda x: x['cost_benefit'])
            
            # 记录这一步的信息
            steps.append({
                'step': step_count,
                'position': current_pos,
                'action': 'move_to_resource',
                'target': best_resource['position'],
                'target_type': best_resource['type'],
                'target_value': best_resource['value'],
                'visible_resources': visible_resources,
                'total_value': total_value
            })
            
            # 移动到目标资源
            path = self.find_path_to_resource(current_pos, best_resource['position'])
            
            if not path:
                steps.append({
                    'step': step_count + 1,
                    'position': current_pos,
                    'action': 'path_blocked',
                    'total_value': total_value
                })
                break
            
            # 更新位置和价值
            current_pos = best_resource['position']
            total_value += best_resource['value']
            
            # 将收集过的金币格子设为路径（删除资源）
            if self.maze[current_pos[0]][current_pos[1]] == Config.GOLD:
                self.maze[current_pos[0]][current_pos[1]] = Config.PATH
        
        return steps
    
    def analyze_strategy_efficiency(self, start_pos: Tuple[int, int]) -> Dict:
        """
        分析贪心策略的效率
        
        Args:
            start_pos: 起始位置
        
        Returns:
            Dict: 策略效率分析
        """
        # 创建迷宫副本以避免修改原始迷宫
        original_maze = [row[:] for row in self.maze]
        path, total_value = self.greedy_resource_collection(start_pos)
        steps = self.simulate_step_by_step(start_pos)
        
        # 恢复原始迷宫
        self.maze = [row[:] for row in original_maze]
        
        # 统计所有可收集的资源
        all_resources = 0
        all_value = 0
        
        for i in range(self.size):
            for j in range(self.size):
                if self.maze[i][j] == Config.GOLD:
                    all_resources += 1
                    all_value += Config.GOLD_VALUE
                elif self.maze[i][j] == Config.TRAP:
                    all_resources += 1
                    all_value -= Config.TRAP_RESOURCE_COST
        
        collected_count = len([s for s in steps if s.get('action') == 'move_to_resource'])
        
        return {
            'total_steps': len(steps),
            'path_length': len(path),
            'total_value_collected': total_value,
            'resources_collected': collected_count,
            'total_resources_available': all_resources,
            'total_value_available': all_value,
            'collection_rate': collected_count / max(1, all_resources),
            'value_efficiency': total_value / max(1, all_value),
            'path_efficiency': total_value / max(1, len(path)),
            'steps_detail': steps
        }