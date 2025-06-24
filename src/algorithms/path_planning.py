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
            return Config.TRAP_DAMAGE
        elif cell in [Config.PATH, Config.START, Config.EXIT, Config.LOCKER, Config.BOSS]:
            return 0
        else:  # 墙壁
            return -float('inf')
    
    def find_optimal_path(self) -> Tuple[int, List[Tuple[int, int]]]:
        """
        使用动态规划找到最优路径
        
        Returns:
            Tuple[int, List[Tuple[int, int]]]: (最大资源值, 最优路径)
        """
        if not self.start_pos or not self.exit_pos:
            return 0, []
        
        # 初始化起点
        start_x, start_y = self.start_pos
        self.dp[start_x][start_y] = self._get_cell_value(start_x, start_y)
        
        # 动态规划填表
        self._fill_dp_table()
        
        # 回溯构建最优路径
        max_value = self.dp[self.exit_pos[0]][self.exit_pos[1]]
        optimal_path = self._reconstruct_path()
        
        return max_value, optimal_path
    
    def _fill_dp_table(self):
        """
        使用动态规划填充DP表
        采用拓扑排序的思想，按照从起点到终点的顺序更新
        """
        # 使用队列进行BFS式的DP更新
        from collections import deque
        
        queue = deque([self.start_pos])
        visited = set([self.start_pos])
        
        while queue:
            x, y = queue.popleft()
            current_value = self.dp[x][y]
            
            # 四个方向
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # 检查边界和墙壁
                if (0 <= nx < self.size and 0 <= ny < self.size and 
                    self.maze[nx][ny] != Config.WALL):
                    
                    # 计算到达(nx, ny)的价值
                    new_value = current_value + self._get_cell_value(nx, ny)
                    
                    # 如果找到更好的路径，更新DP表
                    if new_value > self.dp[nx][ny]:
                        self.dp[nx][ny] = new_value
                        self.parent[nx][ny] = (x, y)
                        
                        # 如果这个位置还没有被访问过，加入队列
                        if (nx, ny) not in visited:
                            queue.append((nx, ny))
                            visited.add((nx, ny))
    
    def _reconstruct_path(self) -> List[Tuple[int, int]]:
        """
        从终点回溯构建最优路径
        
        Returns:
            List[Tuple[int, int]]: 最优路径坐标列表
        """
        if self.dp[self.exit_pos[0]][self.exit_pos[1]] == -float('inf'):
            return []  # 无法到达终点
        
        path = []
        current = self.exit_pos
        
        while current is not None:
            path.append(current)
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