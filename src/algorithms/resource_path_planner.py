#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源路径规划算法
计算从起点到终点的最优资源收集路径，支持自动寻路和陷阱代价权衡
"""

import heapq
from itertools import combinations
from typing import List, Tuple, Dict, Optional, Set
from ..config import Config

class ResourcePathPlanner:
    """
    资源路径规划器
    结合A*算法和动态规划，实现最优资源收集路径规划
    支持陷阱代价权衡分析
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
        self.resource_dependencies = {}  # 资源依赖关系

        # 找到起点、终点和所有资源
        self._find_key_positions()
        # 分析资源依赖关系
        self._build_resource_dependencies()
        self.mov = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        # Corresponding direction characters
        self.ch = "RLDU"

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

    import heapq
    from typing import Tuple, List

    def _a_star_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> str:
        """
        使用A*算法找到两点间的最短路径，返回RLDU移动序列

        Args:
            start: 起始位置 (row, col)
            goal: 目标位置 (row, col)

        Returns:
            str: 由'R'（右）、'L'（左）、'D'（下）、'U'（上）组成的移动序列
        """
        if start == goal:
            return ""

        # 定义方向及其对应的字符
        directions = [(0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L'), (-1, 0, 'U')]

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._manhattan_distance(start, goal)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # 重构路径并转换为移动序列
                path = []
                while current in came_from:
                    prev = came_from[current]
                    # 找出移动方向
                    dx = current[0] - prev[0]
                    dy = current[1] - prev[1]
                    # 匹配方向字符
                    for d in directions:
                        if d[0] == dx and d[1] == dy:
                            path.append(d[2])
                            break
                    current = prev
                path.reverse()
                return ''.join(path)

            # 检查四个方向
            for dx, dy, direction in directions:
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

        return ""  # 无法到达目标
    def _find_all_paths_to_resource(self, target_pos: Tuple[int, int]) -> List[List[Tuple[int, int]]]:
        """
        找到从起点到目标资源的所有可能路径

        Args:
            target_pos: 目标资源位置

        Returns:
            List[List[Tuple[int, int]]]: 所有可能路径列表
        """
        all_paths = []
        visited = set()

        def dfs(current_pos: Tuple[int, int], path: List[Tuple[int, int]]):
            if current_pos == target_pos:
                all_paths.append(path.copy())
                return

            if len(path) > self.size * self.size:  # 防止无限循环
                return

            x, y = current_pos
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

            for dx, dy in directions:
                next_pos = (x + dx, y + dy)
                if (0 <= next_pos[0] < self.size and 0 <= next_pos[1] < self.size and
                    self.maze[next_pos[0]][next_pos[1]] != Config.WALL and
                    next_pos not in path):  # 避免回路

                    path.append(next_pos)
                    dfs(next_pos, path)
                    path.pop()

        dfs(self.start_pos, [self.start_pos])
        return all_paths[:5]  # 限制路径数量避免过度计算

    def _find_required_traps(self, paths: List[List[Tuple[int, int]]]) -> List[Dict]:
        """
        找出所有路径都必须经过的陷阱

        Args:
            paths: 到达目标的所有可能路径

        Returns:
            List[Dict]: 必经陷阱列表
        """
        if not paths:
            return []

        # 找出所有路径的交集中的陷阱
        common_positions = set(paths[0])
        for path in paths[1:]:
            common_positions &= set(path)

        required_traps = []
        for pos in common_positions:
            x, y = pos
            if self.maze[x][y] == Config.TRAP:
                trap_resource = next((r for r in self.resources if r['position'] == pos), None)
                if trap_resource:
                    required_traps.append(trap_resource)

        return required_traps

    def _build_resource_dependencies(self):
        """
        构建资源依赖关系图
        分析哪些金币必须通过特定陷阱才能到达
        """
        self.resource_dependencies = {}

        for gold_resource in [r for r in self.resources if r['value'] > 0]:
            gold_pos = gold_resource['position']

            # 检查从起点到该金币的所有可能路径
            possible_paths = self._find_all_paths_to_resource(gold_pos)

            # 找出路径上必经的陷阱
            required_traps = self._find_required_traps(possible_paths)

            self.resource_dependencies[gold_pos] = {
                'resource': gold_resource,
                'required_traps': required_traps,
                'all_paths': possible_paths
            }

    def _calculate_net_value_with_traps(self, target_resources: List[Dict]) -> int:
        """
        计算考虑陷阱代价后的净价值

        Args:
            target_resources: 目标资源列表

        Returns:
            int: 净价值（收益 - 陷阱代价）
        """
        total_gain = 0
        total_cost = 0

        for resource in target_resources:
            if resource['value'] > 0:
                total_gain += resource['value']
            else:
                total_cost += abs(resource['value'])

        return total_gain - total_cost

    def _generate_combinations(self, items: List, r: int) -> List[List]:
        """
        生成指定长度的组合

        Args:
            items: 项目列表
            r: 组合长度

        Returns:
            List[List]: 组合列表
        """
        return [list(combo) for combo in combinations(items, r)]

    def _is_combination_reachable(self, combo: List[Dict], dependencies: Dict) -> bool:
        """
        判断资源组合是否可达

        Args:
            combo: 资源组合
            dependencies: 依赖关系

        Returns:
            bool: 是否可达
        """
        # 检查组合中的每个金币是否都能满足其依赖的陷阱要求
        for resource in combo:
            if resource['value'] > 0:  # 金币
                pos = resource['position']
                if pos in dependencies:
                    required_traps = dependencies[pos]['required_traps']
                    # 检查所需陷阱是否都在组合中
                    for required_trap in required_traps:
                        if required_trap not in combo:
                            return False
        return True

    def _analyze_reachable_combinations(self) -> List[List[Dict]]:
        """
        分析所有可到达的资源组合
        考虑必须经过陷阱才能到达的金币

        Returns:
            List[List[Dict]]: 可到达的资源组合列表
        """
        combinations_list = []

        # 生成所有可能的有效组合
        for i in range(len(self.resources) + 1):
            for combo in self._generate_combinations(self.resources, i):
                if self._is_combination_reachable(combo, self.resource_dependencies):
                    combinations_list.append(combo)

        return combinations_list

    def _find_best_resource_combination(self) -> Dict:
        """
        找到最佳的资源组合（包含陷阱和金币的权衡）

        Returns:
            Dict: 最佳组合信息
        """
        if not self.resources:
            return {'resources': [], 'net_value': 0}

        # 分析可到达的资源路径
        reachable_combinations = self._analyze_reachable_combinations()

        best_net_value = -float('inf')
        best_combination = []

        for combination in reachable_combinations:
            net_value = self._calculate_net_value_with_traps(combination)

            if net_value > best_net_value:
                best_net_value = net_value
                best_combination = combination

        return {
            'resources': best_combination,
            'net_value': best_net_value
        }

    def find_maximum_value_path_with_traps(self) -> Dict:
        """
        找到考虑陷阱代价的最大价值路径
        会权衡踩陷阱获取后续金币的收益

        Returns:
            Dict: 最优路径结果
        """
        if not self.start_pos or not self.exit_pos:
            return {
                'success': False,
                'message': '未找到起点或终点',
                'path': [],
                'total_value': 0
            }

        # 分析所有可能的资源组合
        best_combination = self._find_best_resource_combination()

        if best_combination['net_value'] > 0:
            result = self._find_path_through_resources(best_combination['resources'])
            if result['success']:
                return {
                    'success': True,
                    'path': result['path'],
                    'total_value': result['total_value'],
                    'resources_collected': result['resources_collected'],
                    'strategy': 'value_with_trap_consideration',
                    'net_value': best_combination['net_value'],
                    'traps_crossed': len([r for r in result['resources_collected'] if r['value'] < 0]),
                    'coins_collected': len([r for r in result['resources_collected'] if r['value'] > 0])
                }

        # 回退到直接路径
        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        return {
            'success': True,
            'path': direct_path,
            'total_value': self._calculate_path_value(direct_path),
            'resources_collected': [],
            'strategy': 'direct_path_no_profit'
        }

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
        return total_value

    def _find_path_through_resources(self, resources: List[Dict]) -> Dict:
        """
        找到经过指定资源的最优路径
        优化版本：智能排序资源访问顺序

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

        # 使用优化的资源访问顺序策略
        resource_order = self._optimize_resource_order(resources)

        # 构建完整路径
        full_path = []
        current_pos = self.start_pos
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

    def _optimize_resource_order(self, resources: List[Dict]) -> List[Dict]:
        """
        优化资源访问顺序
        考虑价值、距离和依赖关系

        Args:
            resources: 资源列表

        Returns:
            List[Dict]: 优化后的资源访问顺序
        """
        if not resources:
            return []

        # 分离陷阱和金币
        traps = [r for r in resources if r['value'] < 0]
        golds = [r for r in resources if r['value'] > 0]

        ordered_resources = []
        current_pos = self.start_pos

        # 首先处理必需的陷阱（为了到达某些金币）
        required_traps = set()
        for gold in golds:
            gold_pos = gold['position']
            if gold_pos in self.resource_dependencies:
                for trap in self.resource_dependencies[gold_pos]['required_traps']:
                    required_traps.add(trap['position'])

        # 按价值和距离优化顺序
        remaining_resources = resources.copy()

        while remaining_resources:
            best_resource = None
            best_score = -float('inf')

            for resource in remaining_resources:
                # 计算综合评分：价值权重0.7，距离权重0.3
                value_score = resource['value']
                distance_score = -self._manhattan_distance(current_pos, resource['position'])
                
                # 如果是必需陷阱，提高优先级
                if resource['position'] in required_traps:
                    priority_bonus = 50
                else:
                    priority_bonus = 0

                total_score = value_score * 0.7 + distance_score * 0.3 + priority_bonus

                if total_score > best_score:
                    best_score = total_score
                    best_resource = resource

            if best_resource:
                ordered_resources.append(best_resource)
                remaining_resources.remove(best_resource)
                current_pos = best_resource['position']

        return ordered_resources

    def judge_dp(self, now: Tuple[int, int], maze: List[str], vis: List[List[bool]], dp: List[List[int]]) -> int:
        """
        使用动态规划方法计算从指定位置开始的可达区域的价值。

        Args:
            now (Tuple[int, int]): 当前位置的坐标 (row, col)
            maze (List[str]): 迷宫矩阵，每个元素代表一个格子的类型
            vis (List[List[bool]]): 二维布尔数组，用于标记每个格子是否被访问过
            dp (List[List[int]]): 二维数组，用于存储每个格子的价值

        Returns:
            int: 当前位置的最终价值
        """
        # 解包当前位置的行和列坐标
        row, col = now
        # 根据迷宫格子的字符类型设置基础价值
        cell = maze[row][col]
        if cell == ' ':  # 空白区域
            dp[row][col] = 0
        elif cell == 'T':  # 目标区域
            dp[row][col] = -3
        elif cell in ['B', 'L']:  # 不良区域
            dp[row][col] = 0
        elif cell == 'G':  # 优质区域
            dp[row][col] = 5
        elif cell == '#':  # 墙壁
            dp[row][col] = 0

        # 如果当前格子是墙壁，直接返回0
        if cell == '#':
            return 0

        # 检查当前位置的四个相邻方向
        for i in range(4):
            # 获取当前方向的偏移量
            dx, dy = self.mov[i]
            # 计算相邻位置的坐标
            new_row, new_col = row + dx, col + dy

            # 检查相邻位置是否在迷宫范围内且未被访问过
            if (0 <= new_row < len(maze) and 0 <= new_col < len(maze[0])
                    and not vis[new_row][new_col]):
                # 标记相邻位置为已访问
                vis[new_row][new_col] = True
                # 递归计算相邻位置的价值，并取其与0的最大值累加到当前位置的价值上
                dp[row][col] += max(0, self.judge_dp((new_row, new_col), maze, vis, dp))
                # 标记相邻位置为未访问，以便后续其他路径可以访问
                vis[new_row][new_col] = False

        return dp[row][col]

    def get_way(self, now: Tuple[int, int], maze: List[str], vis: List[List[bool]],
                way: List[str], pos: str, dp: List[List[int]]):
        """
        递归地寻找有价值区域的路径，并将路径方向添加到结果列表中。

        Args:
            now (Tuple[int, int]): 当前位置的坐标 (row, col)
            maze (List[str]): 迷宫矩阵，每个元素代表一个格子的类型
            vis (List[List[bool]]): 二维布尔数组，用于标记每个格子是否被访问过
            way (List[str]): 存储路径方向的列表
            pos (str): 当前移动的方向字符 ('R', 'L', 'D', 'U')
            dp (List[List[int]]): 二维数组，存储每个格子的价值
        """
        # 将当前移动方向添加到路径列表中
        way.append(pos)

        # 检查当前位置的四个相邻方向
        for i in range(4):
            # 获取当前方向的偏移量
            dx, dy = self.mov[i]
            # 计算相邻位置的坐标
            new_row, new_col = now[0] + dx, now[1] + dy

            # 检查相邻位置是否在迷宫范围内且未被访问过
            if (0 <= new_row < len(maze) and 0 <= new_col < len(maze[0])
                    and not vis[new_row][new_col]):
                # 标记相邻位置为已访问
                vis[new_row][new_col] = True
                # 如果相邻位置有价值，递归调用 get_way 方法继续寻找路径
                if dp[new_row][new_col] > 0:
                    self.get_way((new_row, new_col), maze, vis, way, self.ch[i], dp)
                # 标记相邻位置为未访问，以便后续其他路径可以访问
                vis[new_row][new_col] = False

        # 添加反向移动方向，用于回溯操作
        if pos == 'L':
            way.append('R')
        elif pos == 'R':
            way.append('L')
        elif pos == 'D':
            way.append('U')
        elif pos == 'U':
            way.append('D')

    def find_maximum_value_path(self) -> Dict:
        """
        寻找最大价值路径。结合 A* 算法找到的基础路径，探索路径周边有价值的区域，
        最终构建出包含这些有价值区域的完整路径。

        Returns:
            Dict: 包含路径信息的字典，包含成功标志、消息、路径和总价值
        """
        # 获取迷宫矩阵
        maze = self.maze
        # 使用 A* 算法找到从起点到终点的路径
        road = self._a_star_path(self.start_pos, self.exit_pos)
        # 用于存储最终的路径方向
        way = []
        # 获取迷宫的行数
        r = len(maze)
        # 获取迷宫的列数，如果迷宫为空则列数为 0
        c = len(maze[0]) if r > 0 else 0

        # 初始化访问标记数组，用于记录每个格子是否被访问过
        vis = [[False for _ in range(c)] for _ in range(r)]
        # 初始化动态规划数组，用于存储每个格子的价值
        dp = [[0 for _ in range(c)] for _ in range(r)]

        # 寻找起点位置
        start_pos = None
        for i in range(r):
            for j in range(c):
                if maze[i][j] == 'S':
                    start_pos = (i, j)
                    break
            if start_pos is not None:
                break

        # 如果未找到起点，按要求返回包含错误信息的字典
        if not start_pos:
            return {
                'success': False,
                'message': '未找到起点',
                'path': [],
                'total_value': 0
            }

        # 当前位置设为起点
        now = start_pos
        # 标记起点为已访问
        vis[now[0]][now[1]] = True

        # 沿着 A* 算法找到的路径移动，并标记路径上的位置为已访问
        for direction in road:
            i, j = now
            if direction == 'R':
                j += 1
            elif direction == 'L':
                j -= 1
            elif direction == 'D':
                i += 1
            elif direction == 'U':
                i -= 1

            if 0 <= i < r and 0 <= j < c:
                vis[i][j] = True
                now = (i, j)

        # 将当前位置重置为起点
        now = start_pos

        # 计算路径上每个位置周边可达区域的价值
        for step in range(len(road)):
            i, j = now
            # 为路径上的位置设置高价值
            dp[i][j] = 1000

            # 检查当前位置的四个相邻方向
            for dx, dy in self.mov:
                ni, nj = i + dx, j + dy
                if (0 <= ni < r and 0 <= nj < c
                        and not vis[ni][nj]):
                    # 标记相邻位置为已访问
                    vis[ni][nj] = True
                    # 计算相邻位置的价值
                    self.judge_dp((ni, nj), maze, vis, dp)
                    # 标记相邻位置为未访问，以便后续其他路径可以访问
                    vis[ni][nj] = False

            # 沿着 A* 算法找到的路径移动
            direction = road[step]
            if direction == 'R':
                now = (i, j + 1)
            elif direction == 'L':
                now = (i, j - 1)
            elif direction == 'D':
                now = (i + 1, j)
            elif direction == 'U':
                now = (i - 1, j)

        # 打印 dp 数组，用于调试
        for row in dp:
            print(" ".join(f"{val:5}" for val in row))
        print()

        # 将当前位置重置为起点
        now = start_pos

        # 构建最终路径
        for step in range(len(road)):
            i, j = now

            # 检查当前位置的四个相邻方向，寻找有价值的区域
            for dx, dy in self.mov:
                ni, nj = i + dx, j + dy
                if (0 <= ni < r and 0 <= nj < c
                        and not vis[ni][nj]):
                    # 标记相邻位置为已访问
                    vis[ni][nj] = True
                    if dp[ni][nj] > 0:
                        # 递归寻找有价值区域的路径
                        self.get_way((ni, nj), maze, vis, way, self.ch[self.mov.index((dx, dy))], dp)
                    # 标记相邻位置为未访问，以便后续其他路径可以访问
                    vis[ni][nj] = False

            # 沿着 A* 算法找到的路径移动
            direction = road[step]
            if direction == 'R':
                now = (i, j + 1)
            elif direction == 'L':
                now = (i, j - 1)
            elif direction == 'D':
                now = (i + 1, j)
            elif direction == 'U':
                now = (i - 1, j)
            # 将当前移动方向添加到路径列表中
            way.append(direction)

        # 初始化最终路径，起点为路径的第一个元素
        path = [self.start_pos]
        # 当前行和列坐标初始化为起点坐标
        current_row, current_col = self.start_pos
        # 方向字符到坐标偏移量的映射
        direction_map = {
            'R': (0, 1),
            'L': (0, -1),
            'D': (1, 0),
            'U': (-1, 0)
        }
        # 根据路径方向列表构建完整的路径坐标列表
        for direction in way:
            dr, dc = direction_map[direction]
            current_row += dr
            current_col += dc
            path.append((current_row, current_col))

        return {
            'success': True,
            'message': 'OK',
            'path': path,
            'total_value': dp[self.exit_pos[0]][self.exit_pos[1]],
        }

    def _find_maximum_value_path_without_traps(self) -> Dict:
        """
        原始的最大价值路径算法（不考虑陷阱权衡）

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

        # 只收集正价值资源
        positive_resources = [r for r in self.resources if r['value'] > 0]
        negative_resources = [r for r in self.resources if r['value'] < 0]

        positive_resources.sort(key=lambda r: r['value'], reverse=True)

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

        # 直接路径
        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        return {
            'success': True,
            'path': direct_path,
            'total_value': self._calculate_path_value(direct_path),
            'resources_collected': [],
            'strategy': 'direct_path_fallback'
        }

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

        path_length = len(path)
        total_value = self._calculate_path_value(path)

        resources_collected = 0
        for x, y in path:
            if self.maze[x][y] in [Config.GOLD, Config.TRAP]:
                resources_collected += 1

        direct_path = self._a_star_path(self.start_pos, self.exit_pos)
        direct_path_length = len(direct_path) if direct_path else 0

        detour_ratio = (path_length / max(1, direct_path_length)) - 1
        efficiency = total_value

        return {
            'path_length': path_length,
            'total_value': total_value,
            'efficiency': efficiency,
            'resources_collected': resources_collected,
            'direct_path_length': direct_path_length,
            'detour_ratio': detour_ratio,
            'resource_value_priority': total_value
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

        # 方案1：陷阱权衡最优路径
        trap_result = self.find_maximum_value_path_with_traps()
        if trap_result['success']:
            alternatives.append({
                'name': '陷阱权衡最优路径',
                'description': '权衡陷阱代价与金币收益的最优策略',
                **trap_result
            })

        # 方案2：直接路径
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

        # 方案3：仅正价值资源路径
        positive_resources = [r for r in self.resources if r['value'] > 0]
        if positive_resources:
            safe_result = self._find_path_through_resources(positive_resources)
            if safe_result['success']:
                alternatives.append({
                    'name': '安全收集路径',
                    'description': '只收集正价值资源，避开所有陷阱',
                    **safe_result
                })

        # 按净价值排序
        alternatives.sort(key=lambda x: x.get('net_value', x.get('total_value', 0)), reverse=True)

        return alternatives[:num_alternatives]