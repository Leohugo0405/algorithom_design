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
        
        # 初始化DP表：存储(最大资源值, 最小步数)
        self.dp = [[(-float('inf'), float('inf')) for _ in range(self.size)] for _ in range(self.size)]
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
            return Config.RESOURCE_VALUE
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
        
        # 重新初始化DP表：存储(最大资源值, 最小步数)
        self.dp = [[(-float('inf'), float('inf')) for _ in range(self.size)] for _ in range(self.size)]
        self.parent = [[None for _ in range(self.size)] for _ in range(self.size)]
        
        # 初始化起点
        start_x, start_y = start_pos
        start_value = self._get_cell_value(start_x, start_y)
        self.dp[start_x][start_y] = (start_value, 0)  # (资源值, 步数)
        
        # 动态规划填表
        self._fill_dp_table_from_start(start_pos)
        
        # 回溯构建最优路径
        max_value, min_steps = self.dp[self.exit_pos[0]][self.exit_pos[1]]
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
        优化目标：最大化资源收集效率（资源/步数比）
        
        Args:
            start_pos: 起点位置
        """
        # 使用优先队列进行效率优先的路径搜索
        import heapq
        
        # 优先队列：(-效率值, 步数, 位置)
        # 使用负效率值是因为heapq是最小堆，我们要最大效率
        queue = []
        heapq.heappush(queue, (0, 0, start_pos))  # 起点效率为0
        visited = set()
        
        while queue:
            neg_efficiency, steps, current_pos = heapq.heappop(queue)
            
            if current_pos in visited:
                continue
            visited.add(current_pos)
            
            x, y = current_pos
            current_value, current_steps = self.dp[x][y]
            
            # 四个方向的移动
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            for dx, dy in directions:
                next_x, next_y = x + dx, y + dy
                next_pos = (next_x, next_y)
                
                # 检查边界和墙壁
                if (0 <= next_x < self.size and 0 <= next_y < self.size and 
                    self.maze[next_x][next_y] != Config.WALL):
                    
                    # 计算到达下一个位置的资源值和步数
                    next_value = current_value + self._get_cell_value(next_x, next_y)
                    next_steps = current_steps + 1
                    
                    # 计算效率值（资源/步数比，避免除零）
                    next_efficiency = next_value / max(1, next_steps)
                    
                    # 获取下一个位置的当前最优值
                    existing_value, existing_steps = self.dp[next_x][next_y]
                    existing_efficiency = existing_value / max(1, existing_steps) if existing_steps > 0 else 0
                    
                    # 效率优先的智能路径选择
                    should_update = False
                    
                    # 检查下一个位置是否是陷阱
                    is_trap = self.maze[next_x][next_y] == Config.TRAP
                    
                    # 主要判断：效率优先
                    if next_efficiency > existing_efficiency:
                        # 效率更高的路径
                        if is_trap:
                            # 陷阱路径需要效率明显更高才选择
                            efficiency_gain = next_efficiency - existing_efficiency
                            if efficiency_gain > 0.5:  # 效率提升阈值
                                should_update = True
                        else:
                            should_update = True
                    elif abs(next_efficiency - existing_efficiency) < 0.1:  # 效率相近
                        # 效率相近时，优先选择非陷阱且步数更少的路径
                        if not is_trap and next_steps <= existing_steps:
                            should_update = True
                        elif is_trap and next_steps < existing_steps - 3:  # 陷阱路径需要明显更短
                            should_update = True
                    elif next_efficiency > existing_efficiency - 0.2:  # 效率略低但可接受
                        # 效率略低但能避免陷阱的路径
                        if not is_trap and next_steps <= existing_steps + 2:
                            should_update = True
                    
                    if should_update:
                        self.dp[next_x][next_y] = (next_value, next_steps)
                        self.parent[next_x][next_y] = current_pos
                        
                        # 将下一个位置加入优先队列，按效率排序
                        if next_pos not in visited:
                            # 使用负效率值，因为heapq是最小堆
                            heapq.heappush(queue, (-next_efficiency, next_steps, next_pos))

    def _reconstruct_path_to_exit(self) -> List[Tuple[int, int]]:
        """
        从终点回溯构建到出口的最优路径
        
        Returns:
            List[Tuple[int, int]]: 最优路径坐标列表
        """
        exit_value, exit_steps = self.dp[self.exit_pos[0]][self.exit_pos[1]]
        if exit_value == -float('inf'):
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
        获取路径详细信息（仅显示步数和资源统计）
        
        Args:
            path: 路径坐标列表
        
        Returns:
            Dict: 路径详细信息
        """
        if not path:
            return {
                'length': 0,
                'gold_collected': 0,
                'traps_encountered': 0,
                'path_elements': []
            }
        
        gold_collected = 0
        traps_encountered = 0
        path_elements = []
        
        for x, y in path:
            cell = self.maze[x][y]
            
            path_elements.append({
                'position': (x, y),
                'element': cell
            })
            
            if cell == Config.GOLD:
                gold_collected += 1
            elif cell == Config.TRAP:
                traps_encountered += 1
        
        return {
            'length': len(path),
            'gold_collected': gold_collected,
            'traps_encountered': traps_encountered,
            'path_elements': path_elements
        }