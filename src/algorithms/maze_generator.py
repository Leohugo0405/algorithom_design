#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分治法迷宫生成算法
使用递归分治策略生成连通的迷宫
"""

import random
import json
from typing import List, Tuple, Dict
from ..config import Config

class MazeGenerator:
    """
    分治法迷宫生成器
    """
    
    def __init__(self, size: int = Config.DEFAULT_MAZE_SIZE):
        """
        初始化迷宫生成器
        
        Args:
            size: 迷宫大小 (size x size)
        """
        self.size = max(Config.MIN_MAZE_SIZE, min(size, Config.MAX_MAZE_SIZE))
        # 确保迷宫大小为奇数，便于生成算法
        if self.size % 2 == 0:
            self.size += 1
        
        self.maze = [[Config.WALL for _ in range(self.size)] for _ in range(self.size)]
        
    def generate_maze(self) -> List[List[str]]:
        """
        生成迷宫主函数
        
        Returns:
            二维迷宫矩阵
        """
        # 初始化迷宫为全墙壁
        self._initialize_maze()
        
        # 使用分治法生成迷宫
        self._divide_and_conquer(1, 1, self.size - 2, self.size - 2)
        
        # 设置起点和终点
        self._set_start_and_exit()
        
        # 添加游戏元素
        self._add_game_elements()
        
        return self.maze
    
    def _initialize_maze(self):
        """
        初始化迷宫，设置边界为墙壁
        """
        for i in range(self.size):
            for j in range(self.size):
                if i == 0 or i == self.size - 1 or j == 0 or j == self.size - 1:
                    self.maze[i][j] = Config.WALL
                else:
                    self.maze[i][j] = Config.PATH
    
    def _divide_and_conquer(self, x1: int, y1: int, x2: int, y2: int):
        """
        分治法递归生成迷宫
        
        Args:
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
        """
        # 递归终止条件：区域太小无法继续分割
        if x2 - x1 < 2 or y2 - y1 < 2:
            return
        
        # 随机选择分割方向
        if random.choice([True, False]):
            # 垂直分割
            self._vertical_divide(x1, y1, x2, y2)
        else:
            # 水平分割
            self._horizontal_divide(x1, y1, x2, y2)
    
    def _vertical_divide(self, x1: int, y1: int, x2: int, y2: int):
        """
        垂直分割区域
        """
        # 选择分割线位置（必须是偶数，确保墙壁位置正确）
        wall_x = random.randrange(x1 + 1, x2, 2)
        
        # 在分割线上建墙
        for y in range(y1, y2 + 1):
            self.maze[wall_x][y] = Config.WALL
        
        # 在墙上随机开一个门
        door_y = random.randrange(y1, y2 + 1, 2)
        self.maze[wall_x][door_y] = Config.PATH
        
        # 递归处理左右两个子区域
        self._divide_and_conquer(x1, y1, wall_x - 1, y2)
        self._divide_and_conquer(wall_x + 1, y1, x2, y2)
    
    def _horizontal_divide(self, x1: int, y1: int, x2: int, y2: int):
        """
        水平分割区域
        """
        # 选择分割线位置（必须是偶数，确保墙壁位置正确）
        wall_y = random.randrange(y1 + 1, y2, 2)
        
        # 在分割线上建墙
        for x in range(x1, x2 + 1):
            self.maze[x][wall_y] = Config.WALL
        
        # 在墙上随机开一个门
        door_x = random.randrange(x1, x2 + 1, 2)
        self.maze[door_x][wall_y] = Config.PATH
        
        # 递归处理上下两个子区域
        self._divide_and_conquer(x1, y1, x2, wall_y - 1)
        self._divide_and_conquer(x1, wall_y + 1, x2, y2)
    
    def _set_start_and_exit(self):
        """
        设置起点和终点
        """
        # 起点设在左上角附近的通路
        for i in range(1, self.size):
            for j in range(1, self.size):
                if self.maze[i][j] == Config.PATH:
                    self.maze[i][j] = Config.START
                    self.start_pos = (i, j)
                    break
            else:
                continue
            break
        
        # 终点设在右下角附近的通路
        for i in range(self.size - 2, 0, -1):
            for j in range(self.size - 2, 0, -1):
                if self.maze[i][j] == Config.PATH:
                    self.maze[i][j] = Config.EXIT
                    self.exit_pos = (i, j)
                    return
    
    def _add_game_elements(self):
        """
        添加游戏元素：资源、陷阱、机关、BOSS
        """
        # 获取所有可用的通路位置
        available_positions = []
        for i in range(1, self.size - 1):
            for j in range(1, self.size - 1):
                if self.maze[i][j] == Config.PATH:
                    available_positions.append((i, j))
        
        if not available_positions:
            return
        
        # 添加资源
        gold_count = max(1, int(len(available_positions) * Config.RESOURCE_DENSITY))
        gold_positions = random.sample(available_positions, min(gold_count, len(available_positions)))
        for pos in gold_positions:
            self.maze[pos[0]][pos[1]] = Config.GOLD
            available_positions.remove(pos)
        
        if not available_positions:
            return
        
        # 添加陷阱
        trap_count = max(1, int(len(available_positions) * Config.TRAP_DENSITY))
        trap_positions = random.sample(available_positions, min(trap_count, len(available_positions)))
        for pos in trap_positions:
            self.maze[pos[0]][pos[1]] = Config.TRAP
            available_positions.remove(pos)
        
        if not available_positions:
            return
        
        # 添加机关
        locker_positions = random.sample(available_positions, min(Config.LOCKER_COUNT, len(available_positions)))
        for pos in locker_positions:
            self.maze[pos[0]][pos[1]] = Config.LOCKER
            available_positions.remove(pos)
        
        if not available_positions:
            return
        
        # 添加BOSS
        boss_positions = random.sample(available_positions, min(Config.BOSS_COUNT, len(available_positions)))
        for pos in boss_positions:
            self.maze[pos[0]][pos[1]] = Config.BOSS
            available_positions.remove(pos)
    
    def save_maze_to_json(self, filename: str):
        """
        将迷宫保存为JSON文件
        
        Args:
            filename: 保存的文件名
        """
        maze_data = {
            'size': self.size,
            'maze': self.maze,
            'start_pos': getattr(self, 'start_pos', None),
            'exit_pos': getattr(self, 'exit_pos', None)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(maze_data, f, ensure_ascii=False, indent=2)
    
    def is_connected(self) -> bool:
        """
        检查迷宫连通性
        使用DFS验证从起点能否到达终点
        
        Returns:
            bool: 迷宫是否连通
        """
        if not hasattr(self, 'start_pos') or not hasattr(self, 'exit_pos'):
            return False
        
        visited = [[False for _ in range(self.size)] for _ in range(self.size)]
        return self._dfs_connectivity(self.start_pos[0], self.start_pos[1], visited)
    
    def _dfs_connectivity(self, x: int, y: int, visited: List[List[bool]]) -> bool:
        """
        深度优先搜索检查连通性
        
        Args:
            x, y: 当前位置
            visited: 访问标记数组
        
        Returns:
            bool: 是否能到达终点
        """
        if (x, y) == self.exit_pos:
            return True
        
        visited[x][y] = True
        
        # 四个方向
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            if (0 <= nx < self.size and 0 <= ny < self.size and 
                not visited[nx][ny] and self.maze[nx][ny] != Config.WALL):
                
                if self._dfs_connectivity(nx, ny, visited):
                    return True
        
        return False
    
    def get_maze_info(self) -> Dict:
        """
        获取迷宫信息统计
        
        Returns:
            Dict: 迷宫统计信息
        """
        info = {
            'size': self.size,
            'total_cells': self.size * self.size,
            'walls': 0,
            'paths': 0,
            'gold': 0,
            'traps': 0,
            'lockers': 0,
            'bosses': 0,
            'connected': self.is_connected()
        }
        
        for row in self.maze:
            for cell in row:
                if cell == Config.WALL:
                    info['walls'] += 1
                elif cell in [Config.PATH, Config.START, Config.EXIT]:
                    info['paths'] += 1
                elif cell == Config.GOLD:
                    info['gold'] += 1
                elif cell == Config.TRAP:
                    info['traps'] += 1
                elif cell == Config.LOCKER:
                    info['lockers'] += 1
                elif cell == Config.BOSS:
                    info['bosses'] += 1
        
        return info