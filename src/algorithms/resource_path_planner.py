#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源路径规划算法
计算从起点到终点的最优资源收集路径，支持自动寻路
"""

import heapq
from typing import List, Tuple, Dict, Optional, Set
from ..config import Config

class ResourcePathPlanner:
    """
    资源路径规划器
    结合A*算法和动态规划，实现最优资源收集路径规划
    """
    
    def __init__(self, maze: List[List[str]]):
        """
        初始化资源路径规划器
        
        Args:
            maze: 迷宫矩阵
        """
        self.maze = maze
        self.size = len(maze)
        self.start_pos = None
        self.exit_pos = None
        self.resources = []  # 所有资源位置
        
        # 找到起点、终点和所有资源
        self._find_key_positions()
    
    def _find_key_positions(self):
        """
        找到迷宫中的关键位置：起点、终点和所有资源
        """
        self.resources = []
        
        for i in range(self.size):
            for j in range(self.size):
                cell = self.maze[i][j]
                if cell == Config.START:
                    self.start_pos = (i, j)
                elif cell == Config.EXIT:
                    self.exit_pos = (i, j)
                elif cell in [Config.GOLD, Config.TRAP]:
                    value = self._get_cell_value(i, j)
                    self.resources.append({
                        'position': (i, j),
                        'type': cell,
                        'value': value
                    })
    
    def _get_cell_value(self, x: int, y: int) -> int:
        """
        获取格子的价值
        
        Args:
            x, y: 格子坐标
        
        Returns:
            int: 格子价值
        """
        cell = self.maze[x][y]
        
        if cell == Config.GOLD:
            return Config.RESOURCE_VALUE
        elif cell == Config.TRAP:
            return -Config.TRAP_RESOURCE_COST
        elif cell in [Config.PATH, Config.START, Config.EXIT, Config.LOCKER, Config.BOSS]:
            return 0
        else:  # 墙壁
            return -float('inf')
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """
        计算曼哈顿距离
        
        Args:
            pos1, pos2: 两个位置
        
        Returns:
            int: 曼哈顿距离
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _a_star_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        使用A*算法找到两点间的最短路径
        
        Args:
            start: 起始位置
            goal: 目标位置
        
        Returns:
            List[Tuple[int, int]]: 路径坐标列表
        """
        if start == goal:
            return [start]
        
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._manhattan_distance(start, goal)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
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
                        f_score[neighbor] = tentative_g_score + self._manhattan_distance(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # 无法到达目标
    
    def _calculate_path_value(self, path: List[Tuple[int, int]]) -> int:
        """
        计算路径的总价值（只计算资源格子的价值）
        
        Args:
            path: 路径坐标列表
        
        Returns:
            int: 路径总价值
        """
        total_value = 0
        for x, y in path:
            cell = self.maze[x][y]
            if cell == Config.GOLD:
                total_value += Config.RESOURCE_VALUE
            elif cell == Config.TRAP:
                total_value += -Config.TRAP_RESOURCE_COST
            # 普通路径格子不计算价值
        return total_value
    
    def find_optimal_resource_path(self, max_resources: int = None) -> Dict:
        """
        找到从起点到终点的最优资源收集路径
        使用动态规划 + TSP思想
        
        Args:
            max_resources: 最大收集资源数量限制
        
        Returns:
            Dict: 包含最优路径和相关信息的字典
        """
        if not self.start_pos or not self.exit_pos:
            return {
                'success': False,
                'message': '未找到起点或终点',
                'path': [],
                'total_value': 0
            }
        
        # 如果没有资源，直接返回最短路径
        if not self.resources:
            direct_path = self._a_star_path(self.start_pos, self.exit_pos)
            return {
                'success': True,
                'path': direct_path,
                'total_value': self._calculate_path_value(direct_path),
                'resources_collected': [],
                'strategy': 'direct_path'
            }
        
        # 限制资源数量
        if max_resources is None:
            max_resources = len(self.resources)
        else:
            max_resources = min(max_resources, len(self.resources))
        
        # 使用动态规划求解TSP变种问题
        best_result = self._solve_resource_collection_tsp(max_resources)
        
        return best_result
    
    def _solve_resource_collection_tsp(self, max_resources: int) -> Dict:
        """
        使用动态规划解决资源收集的TSP变种问题
        不考虑最小步数，专注于最大化资源收集价值
        
        Args:
            max_resources: 最大资源收集数量
        
        Returns:
            Dict: 最优解结果
        """
        # 按资源价值排序，不考虑距离因素
        sorted_resources = sorted(self.resources, 
                                key=lambda r: r['value'], 
                                reverse=True)
        
        best_path = []
        best_value = -float('inf')
        best_resources = []
        
        # 尝试不同的资源组合
        for num_resources in range(min(max_resources + 1, len(sorted_resources) + 1)):
            if num_resources == 0:
                # 不收集任何资源，直接到终点
                path = self._a_star_path(self.start_pos, self.exit_pos)
                value = self._calculate_path_value(path)
                
                if value > best_value:
                    best_value = value
                    best_path = path
                    best_resources = []
            else:
                # 尝试收集前num_resources个高价值资源
                selected_resources = sorted_resources[:num_resources]
                result = self._find_path_through_resources(selected_resources)
                
                if result['success'] and result['total_value'] > best_value:
                    best_value = result['total_value']
                    best_path = result['path']
                    best_resources = result['resources_collected']
        
        return {
            'success': len(best_path) > 0,
            'path': best_path,
            'total_value': best_value,
            'resources_collected': best_resources,
            'strategy': 'optimal_resource_collection'
        }
    
    def _find_path_through_resources(self, resources: List[Dict]) -> Dict:
        """
        找到经过指定资源的最优路径
        
        Args:
            resources: 要收集的资源列表
        
        Returns:
            Dict: 路径结果
        """
        if not resources:
            path = self._a_star_path(self.start_pos, self.exit_pos)
            return {
                'success': True,
                'path': path,
                'total_value': self._calculate_path_value(path),
                'resources_collected': []
            }
        
        # 使用最近邻算法确定资源访问顺序
        resource_order = self._nearest_neighbor_order(resources)
        
        # 构建完整路径
        full_path = []
        current_pos = self.start_pos
        total_value = 0
        collected_resources = []
        
        # 依次访问每个资源
        for resource in resource_order:
            target_pos = resource['position']
            segment_path = self._a_star_path(current_pos, target_pos)
            
            if not segment_path:
                return {
                    'success': False,
                    'message': f'无法到达资源位置 {target_pos}',
                    'path': [],
                    'total_value': 0
                }
            
            # 添加路径段（避免重复起点）
            if full_path:
                full_path.extend(segment_path[1:])
            else:
                full_path.extend(segment_path)
            
            current_pos = target_pos
            collected_resources.append(resource)
        
        # 从最后一个资源到终点
        final_segment = self._a_star_path(current_pos, self.exit_pos)
        if not final_segment:
            return {
                'success': False,
                'message': '无法从最后资源到达终点',
                'path': [],
                'total_value': 0
            }
        
        full_path.extend(final_segment[1:])
        total_value = self._calculate_path_value(full_path)
        
        return {
            'success': True,
            'path': full_path,
            'total_value': total_value,
            'resources_collected': collected_resources
        }
    
    def _nearest_neighbor_order(self, resources: List[Dict]) -> List[Dict]:
        """
        按资源价值确定访问顺序，不考虑距离因素
        
        Args:
            resources: 资源列表
        
        Returns:
            List[Dict]: 按价值排序的资源列表
        """
        if not resources:
            return []
        
        # 直接按价值从高到低排序，不考虑距离
        ordered = sorted(resources, key=lambda r: r['value'], reverse=True)
        
        return ordered
    
    def get_auto_navigation_steps(self, target_path: List[Tuple[int, int]], 
                                 current_pos: Tuple[int, int]) -> List[str]:
        """
        获取自动导航的步骤指令
        
        Args:
            target_path: 目标路径
            current_pos: 当前位置
        
        Returns:
            List[str]: 移动指令列表 ('up', 'down', 'left', 'right')
        """
        if not target_path or current_pos not in target_path:
            return []
        
        current_index = target_path.index(current_pos)
        steps = []
        
        for i in range(current_index + 1, len(target_path)):
            current = target_path[i - 1]
            next_pos = target_path[i]
            
            dx = next_pos[0] - current[0]
            dy = next_pos[1] - current[1]
            
            if dx == 1:
                steps.append('down')
            elif dx == -1:
                steps.append('up')
            elif dy == 1:
                steps.append('right')
            elif dy == -1:
                steps.append('left')
        
        return steps
    
    def analyze_path_efficiency(self, path: List[Tuple[int, int]]) -> Dict:
        """
        分析路径效率
        
        Args:
            path: 路径坐标列表
        
        Returns:
            Dict: 路径效率分析结果
        """
        if not path:
            return {
                'path_length': 0,
                'total_value': 0,
                'efficiency': 0,
                'resources_collected': 0,
                'direct_path_length': 0,
                'detour_ratio': 0
            }
        
        # 计算路径信息
        path_length = len(path)
        total_value = self._calculate_path_value(path)
        
        # 计算收集的资源数量
        resources_collected = 0
        for x, y in path:
            if self.maze[x][y] in [Config.GOLD, Config.TRAP]:
                resources_collected += 1
        
        # 计算直接路径长度
        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        direct_path_length = len(direct_path) if direct_path else 0
        
        # 计算绕路比例
        detour_ratio = (path_length / max(1, direct_path_length)) - 1
        
        # 计算效率（主要关注总价值，步数为次要因素）
        efficiency = total_value  # 不再除以路径长度，专注于总价值
        
        return {
            'path_length': path_length,
            'total_value': total_value,
            'efficiency': efficiency,
            'resources_collected': resources_collected,
            'direct_path_length': direct_path_length,
            'detour_ratio': detour_ratio,
            'resource_value_priority': total_value  # 新增：资源价值优先指标
        }
    
    def get_alternative_paths(self, num_alternatives: int = 3) -> List[Dict]:
        """
        获取多个备选路径方案
        
        Args:
            num_alternatives: 备选方案数量
        
        Returns:
            List[Dict]: 备选路径列表
        """
        alternatives = []
        
        # 方案1：最优资源收集路径
        optimal_result = self.find_optimal_resource_path()
        if optimal_result['success']:
            alternatives.append({
                'name': '最优资源收集路径',
                'description': '收集价值最高的资源组合',
                **optimal_result
            })
        
        # 方案2：直接路径（不收集资源）
        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        if direct_path:
            alternatives.append({
                'name': '直接路径',
                'description': '最短路径，不收集任何资源',
                'success': True,
                'path': direct_path,
                'total_value': self._calculate_path_value(direct_path),
                'resources_collected': [],
                'strategy': 'direct_path'
            })
        
        # 方案3：全资源收集路径（收集所有正价值资源）
        positive_resources = [r for r in self.resources if r['value'] > 0]
        if positive_resources:
            greedy_result = self._find_path_through_resources(positive_resources)  # 收集所有正价值资源
            if greedy_result['success']:
                alternatives.append({
                    'name': '全资源收集路径',
                    'description': '收集所有正价值资源，不考虑路径长度',
                    **greedy_result
                })
        
        # 按总价值排序
        alternatives.sort(key=lambda x: x.get('total_value', 0), reverse=True)
        
        return alternatives[:num_alternatives]
    
    def find_maximum_value_path(self) -> Dict:
        """
        找到最大价值路径，完全不考虑步数限制
        优先收集所有正价值资源，避免负价值资源
        
        Returns:
            Dict: 最大价值路径结果
        """
        if not self.start_pos or not self.exit_pos:
            return {
                'success': False,
                'message': '未找到起点或终点',
                'path': [],
                'total_value': 0
            }
        
        # 分离正价值和负价值资源
        positive_resources = [r for r in self.resources if r['value'] > 0]
        negative_resources = [r for r in self.resources if r['value'] < 0]
        
        # 按价值排序正价值资源（从高到低）
        positive_resources.sort(key=lambda r: r['value'], reverse=True)
        
        # 尝试收集所有正价值资源
        if positive_resources:
            result = self._find_path_through_resources(positive_resources)
            if result['success']:
                return {
                    'success': True,
                    'path': result['path'],
                    'total_value': result['total_value'],
                    'resources_collected': result['resources_collected'],
                    'strategy': 'maximum_value_collection',
                    'positive_resources': len(positive_resources),
                    'negative_resources_avoided': len(negative_resources)
                }
        
        # 如果无法收集资源，返回直接路径
        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        return {
            'success': True,
            'path': direct_path,
            'total_value': self._calculate_path_value(direct_path),
            'resources_collected': [],
            'strategy': 'direct_path_fallback'
        }