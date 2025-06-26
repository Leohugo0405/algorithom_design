#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态规划路径规划算法
计算从起点到终点的最优资源收集路径
"""

from typing import List, Tuple, Dict, Optional
from ..config import Config

class PathPlanner:
    """
    动态规划路径规划器
    """
    
    def __init__(self, maze: List[List[str]]):
        """
        初始化路径规划器
        
        Args:
            maze: 迷宫矩阵
        """
        self.maze = maze
        self.size = len(maze)
        self.start_pos = None
        self.exit_pos = None
        
        # 找到起点和终点
        self._find_start_and_exit()
        
        # 初始化DP表
        self.dp = [[-float('inf') for _ in range(self.size)] for _ in range(self.size)]
        self.parent = [[None for _ in range(self.size)] for _ in range(self.size)]
    
    def _find_start_and_exit(self):
        """
        找到迷宫中的起点和终点
        """
        for i in range(self.size):
            for j in range(self.size):
                if self.maze[i][j] == Config.START:
                    self.start_pos = (i, j)
                elif self.maze[i][j] == Config.EXIT:
                    self.exit_pos = (i, j)
    
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
            return Config.GOLD_VALUE
        elif cell == Config.TRAP:
            return -Config.TRAP_RESOURCE_COST
        elif cell in [Config.PATH, Config.START, Config.EXIT, Config.LOCKER, Config.BOSS]:
            return 0
        else:  # 墙壁
            return -float('inf')
    
    def find_optimal_path(self, custom_start: Optional[Tuple[int, int]] = None) -> Tuple[int, List[Tuple[int, int]]]:
        """
        使用动态规划找到最优路径
        
        Args:
            custom_start: 自定义起点位置，如果为None则使用默认起点
        
        Returns:
            Tuple[int, List[Tuple[int, int]]]: (最大资源值, 最优路径)
        """
        # 使用自定义起点或默认起点
        start_pos = custom_start if custom_start else self.start_pos
        
        if not start_pos or not self.exit_pos:
            return 0, []
        
        # 重新初始化DP表
        self.dp = [[-float('inf') for _ in range(self.size)] for _ in range(self.size)]
        self.parent = [[None for _ in range(self.size)] for _ in range(self.size)]
        
        # 初始化起点
        start_x, start_y = start_pos
        self.dp[start_x][start_y] = self._get_cell_value(start_x, start_y)
        
        # 动态规划填表
        self._fill_dp_table_from_start(start_pos)
        
        # 回溯构建最优路径
        max_value = self.dp[self.exit_pos[0]][self.exit_pos[1]]
        optimal_path = self._reconstruct_path_to_exit()
        
        return max_value, optimal_path
    
    def _fill_dp_table(self):
        """
        使用动态规划填充DP表（使用默认起点）
        采用拓扑排序的思想，按照从起点到终点的顺序更新
        """
        self._fill_dp_table_from_start(self.start_pos)
    
    def _fill_dp_table_from_start(self, start_pos: Tuple[int, int]):
        """
        从指定起点使用动态规划填充DP表
        按照用户提供的DP模式：三层嵌套循环结构
        
        Args:
            start_pos: 起点位置
        """
        # 构建图结构：graph[period][current_pos][prev_pos] = transition_cost
        graph = self._build_graph_structure()
        
        # 初始化costs字典：costs[pos] = 到达该位置的最大价值
        costs = {}
        parents = {}
        
        # 初始化所有可达位置的costs为负无穷
        for i in range(self.size):
            for j in range(self.size):
                if self.maze[i][j] != Config.WALL:
                    costs[(i, j)] = -float('inf')
                    parents[(i, j)] = None
        
        # 设置起点的初始值
        costs[start_pos] = self._get_cell_value(start_pos[0], start_pos[1])
        
        # 按照用户提供的DP模式进行三层嵌套循环
        for period_key in graph.keys():
            for key_i in graph[period_key].keys():
                for key_i_cost in graph[period_key][key_i].keys():
                    # 如果通过key_i_cost到达key_i的路径更优，则更新
                    transition_value = graph[period_key][key_i][key_i_cost]
                    new_cost = costs[key_i_cost] + transition_value
                    
                    if new_cost > costs[key_i]:
                        costs[key_i] = new_cost
                        parents[key_i] = key_i_cost
        
        # 将结果更新到DP表中
        for pos, cost in costs.items():
            self.dp[pos[0]][pos[1]] = cost
            self.parent[pos[0]][pos[1]] = parents[pos]
    
    def _build_graph_structure(self):
        """
        构建图结构用于DP算法
        返回格式：graph[period][current_pos][prev_pos] = transition_cost
        """
        graph = {}
        
        # 计算曼哈顿距离作为period（阶段）
        max_distance = (self.size - 1) * 2
        
        for period in range(max_distance + 1):
            graph[period] = {}
            
            # 遍历所有可能的当前位置
            for i in range(self.size):
                for j in range(self.size):
                    if self.maze[i][j] != Config.WALL:
                        current_pos = (i, j)
                        
                        # 计算当前位置到起点的曼哈顿距离
                        if hasattr(self, 'start_pos') and self.start_pos:
                            manhattan_dist = abs(i - self.start_pos[0]) + abs(j - self.start_pos[1])
                        else:
                            manhattan_dist = i + j  # 默认起点为(0,0)
                        
                        # 只处理当前阶段的位置
                        if manhattan_dist == period:
                            graph[period][current_pos] = {}
                            
                            # 四个方向的前驱位置
                            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                            
                            for dx, dy in directions:
                                prev_x, prev_y = i - dx, j - dy
                                
                                # 检查前驱位置的有效性
                                if (0 <= prev_x < self.size and 0 <= prev_y < self.size and 
                                    self.maze[prev_x][prev_y] != Config.WALL):
                                    
                                    prev_pos = (prev_x, prev_y)
                                    # 转移代价是当前位置的价值
                                    transition_cost = self._get_cell_value(i, j)
                                    graph[period][current_pos][prev_pos] = transition_cost
        
        return graph
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """
        从终点回溯构建最优路径（使用默认终点）
        
        Returns:
            List[Tuple[int, int]]: 最优路径坐标列表
        """
        return self._reconstruct_path_to_exit()
    
    def _reconstruct_path_to_exit(self) -> List[Tuple[int, int]]:
        """
        从终点回溯构建到出口的最优路径
        
        Returns:
            List[Tuple[int, int]]: 最优路径坐标列表
        """
        if self.dp[self.exit_pos[0]][self.exit_pos[1]] == -float('inf'):
            return []  # 无法到达终点
        
        path = []
        current = self.exit_pos
        visited_in_path = set()  # 防止循环
        max_path_length = self.size * self.size  # 最大路径长度限制
        
        while current is not None and len(path) < max_path_length:
            if current in visited_in_path:
                # 检测到循环，停止重构
                break
            
            path.append(current)
            visited_in_path.add(current)
            current = self.parent[current[0]][current[1]]
        
        path.reverse()
        return path
    
    def get_path_details(self, path: List[Tuple[int, int]]) -> Dict:
        """
        获取路径详细信息
        
        Args:
            path: 路径坐标列表
        
        Returns:
            Dict: 路径详细信息
        """
        if not path:
            return {
                'length': 0,
                'total_value': 0,
                'gold_collected': 0,
                'traps_encountered': 0,
                'path_elements': []
            }
        
        total_value = 0
        gold_collected = 0
        traps_encountered = 0
        path_elements = []
        
        for x, y in path:
            cell = self.maze[x][y]
            cell_value = self._get_cell_value(x, y)
            
            path_elements.append({
                'position': (x, y),
                'element': cell,
                'value': cell_value
            })
            
            total_value += cell_value
            
            if cell == Config.GOLD:
                gold_collected += 1
            elif cell == Config.TRAP:
                traps_encountered += 1
        
        return {
            'length': len(path),
            'total_value': total_value,
            'gold_collected': gold_collected,
            'traps_encountered': traps_encountered,
            'path_elements': path_elements
        }
    
    def visualize_dp_table(self) -> List[List[str]]:
        """
        可视化DP表，用于调试
        
        Returns:
            List[List[str]]: 格式化的DP表
        """
        result = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                if self.dp[i][j] == -float('inf'):
                    row.append('  #  ')
                else:
                    row.append(f'{self.dp[i][j]:4.0f} ')
            result.append(row)
        return result
    
    def find_all_paths_with_value(self, min_value: int) -> List[Tuple[List[Tuple[int, int]], int]]:
        """
        找到所有价值不低于指定值的路径
        
        Args:
            min_value: 最小价值要求
        
        Returns:
            List[Tuple[List[Tuple[int, int]], int]]: (路径, 价值)的列表
        """
        all_paths = []
        
        def dfs_all_paths(x: int, y: int, current_path: List[Tuple[int, int]], current_value: int, visited: set):
            """
            DFS搜索所有路径
            """
            if (x, y) == self.exit_pos:
                if current_value >= min_value:
                    all_paths.append((current_path.copy(), current_value))
                return
            
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.size and 0 <= ny < self.size and 
                    (nx, ny) not in visited and self.maze[nx][ny] != Config.WALL):
                    
                    new_value = current_value + self._get_cell_value(nx, ny)
                    visited.add((nx, ny))
                    current_path.append((nx, ny))
                    
                    dfs_all_paths(nx, ny, current_path, new_value, visited)
                    
                    current_path.pop()
                    visited.remove((nx, ny))
        
        if self.start_pos:
            start_value = self._get_cell_value(self.start_pos[0], self.start_pos[1])
            visited = {self.start_pos}
            dfs_all_paths(self.start_pos[0], self.start_pos[1], [self.start_pos], start_value, visited)
        
        # 按价值降序排序
        all_paths.sort(key=lambda x: x[1], reverse=True)
        return all_paths
    
    def compare_with_greedy(self, greedy_path: List[Tuple[int, int]]) -> Dict:
        """
        比较动态规划路径与贪心路径
        
        Args:
            greedy_path: 贪心算法得到的路径
        
        Returns:
            Dict: 比较结果
        """
        dp_value, dp_path = self.find_optimal_path()
        dp_details = self.get_path_details(dp_path)
        greedy_details = self.get_path_details(greedy_path)
        
        return {
            'dp_path': {
                'path': dp_path,
                'value': dp_value,
                'details': dp_details
            },
            'greedy_path': {
                'path': greedy_path,
                'details': greedy_details
            },
            'improvement': {
                'value_diff': dp_value - greedy_details['total_value'],
                'length_diff': dp_details['length'] - greedy_details['length'],
                'efficiency': dp_value / dp_details['length'] if dp_details['length'] > 0 else 0
            }
        }