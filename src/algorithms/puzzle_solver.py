#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回溯法解谜算法
用于破解密码锁和其他谜题
"""

import random
from typing import List, Tuple, Dict, Optional, Callable
from ..config import Config

class PuzzleSolver:
    """
    回溯法谜题解决器
    """
    
    def __init__(self):
        """
        初始化谜题解决器
        """
        self.attempt_count = 0
        self.max_attempts = 1000  # 防止无限递归
    
    def generate_password_puzzle(self) -> Dict:
        """
        生成一个3位密码锁谜题
        
        Returns:
            Dict: 包含密码和线索的谜题
        """
        # 生成随机密码
        password = []
        
        # 第一位：1-9的数字
        password.append(random.randint(1, 9))
        
        # 第二位：0-9的数字，但不能与第一位相同
        second_digit = random.randint(0, 9)
        while second_digit == password[0]:
            second_digit = random.randint(0, 9)
        password.append(second_digit)
        
        # 第三位：0-9的数字，但不能与前两位相同
        third_digit = random.randint(0, 9)
        while third_digit in password:
            third_digit = random.randint(0, 9)
        password.append(third_digit)
        
        # 生成线索
        clues = self._generate_clues(password)
        
        return {
            'password': password,
            'clues': clues,
            'description': '破解这个3位密码锁'
        }
    
    def _generate_clues(self, password: List[int]) -> List[str]:
        """
        根据密码生成线索
        
        Args:
            password: 密码列表
        
        Returns:
            List[str]: 线索列表
        """
        clues = []
        
        # 基本线索：数字范围和唯一性
        clues.append("密码由3个不同的数字组成")
        clues.append("第一位数字不为0")
        
        # 根据密码特征生成具体线索
        if self._is_prime(password[0]):
            clues.append("第一位数字是质数")
        else:
            clues.append("第一位数字是合数")
        
        if password[1] % 2 == 0:
            clues.append("第二位数字是偶数")
        else:
            clues.append("第二位数字是奇数")
        
        # 数字关系线索
        if password[0] > password[1]:
            clues.append("第一位数字大于第二位数字")
        else:
            clues.append("第一位数字小于第二位数字")
        
        if password[2] > password[1]:
            clues.append("第三位数字大于第二位数字")
        else:
            clues.append("第三位数字小于第二位数字")
        
        # 数学关系线索
        total = sum(password)
        if total % 2 == 0:
            clues.append("三个数字的和是偶数")
        else:
            clues.append("三个数字的和是奇数")
        
        if total > 15:
            clues.append("三个数字的和大于15")
        else:
            clues.append("三个数字的和不大于15")
        
        return clues
    
    def _is_prime(self, n: int) -> bool:
        """
        判断是否为质数
        
        Args:
            n: 待判断的数字
        
        Returns:
            bool: 是否为质数
        """
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def solve_password_puzzle(self, clues: List[str]) -> Tuple[Optional[List[int]], int]:
        """
        使用回溯法解决密码谜题
        
        Args:
            clues: 线索列表
        
        Returns:
            Tuple[Optional[List[int]], int]: (解答, 尝试次数)
        """
        self.attempt_count = 0
        
        # 解析线索为约束条件
        constraints = self._parse_clues(clues)
        
        # 使用回溯法求解
        solution = self._backtrack_solve([], constraints)
        
        return solution, self.attempt_count
    
    def _parse_clues(self, clues: List[str]) -> List[Callable]:
        """
        将线索解析为约束函数
        
        Args:
            clues: 线索列表
        
        Returns:
            List[Callable]: 约束函数列表
        """
        constraints = []
        
        for clue in clues:
            if "3个不同的数字" in clue:
                constraints.append(lambda pwd: len(set(pwd)) == 3)
            
            elif "第一位数字不为0" in clue:
                constraints.append(lambda pwd: len(pwd) > 0 and pwd[0] != 0)
            
            elif "第一位数字是质数" in clue:
                constraints.append(lambda pwd: len(pwd) > 0 and self._is_prime(pwd[0]))
            
            elif "第一位数字是合数" in clue:
                constraints.append(lambda pwd: len(pwd) > 0 and not self._is_prime(pwd[0]) and pwd[0] > 1)
            
            elif "第二位数字是偶数" in clue:
                constraints.append(lambda pwd: len(pwd) > 1 and pwd[1] % 2 == 0)
            
            elif "第二位数字是奇数" in clue:
                constraints.append(lambda pwd: len(pwd) > 1 and pwd[1] % 2 == 1)
            
            elif "第一位数字大于第二位数字" in clue:
                constraints.append(lambda pwd: len(pwd) > 1 and pwd[0] > pwd[1])
            
            elif "第一位数字小于第二位数字" in clue:
                constraints.append(lambda pwd: len(pwd) > 1 and pwd[0] < pwd[1])
            
            elif "第三位数字大于第二位数字" in clue:
                constraints.append(lambda pwd: len(pwd) > 2 and pwd[2] > pwd[1])
            
            elif "第三位数字小于第二位数字" in clue:
                constraints.append(lambda pwd: len(pwd) > 2 and pwd[2] < pwd[1])
            
            elif "三个数字的和是偶数" in clue:
                constraints.append(lambda pwd: len(pwd) == 3 and sum(pwd) % 2 == 0)
            
            elif "三个数字的和是奇数" in clue:
                constraints.append(lambda pwd: len(pwd) == 3 and sum(pwd) % 2 == 1)
            
            elif "三个数字的和大于15" in clue:
                constraints.append(lambda pwd: len(pwd) == 3 and sum(pwd) > 15)
            
            elif "三个数字的和不大于15" in clue:
                constraints.append(lambda pwd: len(pwd) == 3 and sum(pwd) <= 15)
        
        return constraints
    
    def _backtrack_solve(self, current_password: List[int], constraints: List[Callable]) -> Optional[List[int]]:
        """
        回溯法求解密码
        
        Args:
            current_password: 当前部分密码
            constraints: 约束条件列表
        
        Returns:
            Optional[List[int]]: 完整密码或None
        """
        self.attempt_count += 1
        
        if self.attempt_count > self.max_attempts:
            return None
        
        # 检查当前密码是否满足所有约束
        if not self._check_constraints(current_password, constraints):
            return None
        
        # 如果密码已完整，返回结果
        if len(current_password) == Config.LOCK_DIGITS:
            return current_password[:]
        
        # 尝试下一位数字
        digit_range = range(1, 10) if len(current_password) == 0 else range(0, 10)
        
        for digit in digit_range:
            # 剪枝：避免重复数字
            if digit in current_password:
                continue
            
            # 添加数字并递归
            current_password.append(digit)
            result = self._backtrack_solve(current_password, constraints)
            
            if result is not None:
                return result
            
            # 回溯
            current_password.pop()
        
        return None
    
    def _check_constraints(self, password: List[int], constraints: List[Callable]) -> bool:
        """
        检查密码是否满足约束条件
        
        Args:
            password: 当前密码
            constraints: 约束条件列表
        
        Returns:
            bool: 是否满足所有约束
        """
        try:
            for constraint in constraints:
                if not constraint(password):
                    return False
            return True
        except:
            # 如果约束检查出错（比如索引越界），返回True继续尝试
            return True
    
    def generate_sudoku_puzzle(self, size: int = 4) -> Dict:
        """
        生成简化的数独谜题（4x4）
        
        Args:
            size: 数独大小
        
        Returns:
            Dict: 数独谜题
        """
        # 生成完整的数独解
        solution = self._generate_sudoku_solution(size)
        
        # 移除一些数字创建谜题
        puzzle = [row[:] for row in solution]
        remove_count = size * size // 2
        
        positions = [(i, j) for i in range(size) for j in range(size)]
        random.shuffle(positions)
        
        for i in range(remove_count):
            x, y = positions[i]
            puzzle[x][y] = 0
        
        return {
            'puzzle': puzzle,
            'solution': solution,
            'size': size,
            'description': f'填入1-{size}的数字，使每行每列都不重复'
        }
    
    def _generate_sudoku_solution(self, size: int) -> List[List[int]]:
        """
        生成数独解
        
        Args:
            size: 数独大小
        
        Returns:
            List[List[int]]: 数独解
        """
        grid = [[0 for _ in range(size)] for _ in range(size)]
        
        def is_valid(grid, row, col, num):
            # 检查行
            for j in range(size):
                if grid[row][j] == num:
                    return False
            
            # 检查列
            for i in range(size):
                if grid[i][col] == num:
                    return False
            
            return True
        
        def solve_sudoku(grid):
            for i in range(size):
                for j in range(size):
                    if grid[i][j] == 0:
                        numbers = list(range(1, size + 1))
                        random.shuffle(numbers)
                        
                        for num in numbers:
                            if is_valid(grid, i, j, num):
                                grid[i][j] = num
                                
                                if solve_sudoku(grid):
                                    return True
                                
                                grid[i][j] = 0
                        
                        return False
            return True
        
        solve_sudoku(grid)
        return grid
    
    def solve_sudoku_puzzle(self, puzzle: List[List[int]]) -> Tuple[Optional[List[List[int]]], int]:
        """
        使用回溯法解决数独谜题
        
        Args:
            puzzle: 数独谜题
        
        Returns:
            Tuple[Optional[List[List[int]]], int]: (解答, 尝试次数)
        """
        self.attempt_count = 0
        size = len(puzzle)
        solution = [row[:] for row in puzzle]
        
        def is_valid(grid, row, col, num):
            # 检查行
            for j in range(size):
                if grid[row][j] == num:
                    return False
            
            # 检查列
            for i in range(size):
                if grid[i][col] == num:
                    return False
            
            return True
        
        def backtrack_sudoku(grid):
            self.attempt_count += 1
            
            if self.attempt_count > self.max_attempts:
                return False
            
            for i in range(size):
                for j in range(size):
                    if grid[i][j] == 0:
                        for num in range(1, size + 1):
                            if is_valid(grid, i, j, num):
                                grid[i][j] = num
                                
                                if backtrack_sudoku(grid):
                                    return True
                                
                                grid[i][j] = 0
                        
                        return False
            return True
        
        success = backtrack_sudoku(solution)
        return solution if success else None, self.attempt_count
    
    def analyze_puzzle_complexity(self, puzzle_type: str, puzzle_data: Dict) -> Dict:
        """
        分析谜题复杂度
        
        Args:
            puzzle_type: 谜题类型
            puzzle_data: 谜题数据
        
        Returns:
            Dict: 复杂度分析
        """
        if puzzle_type == 'password':
            solution, attempts = self.solve_password_puzzle(puzzle_data['clues'])
            
            return {
                'puzzle_type': puzzle_type,
                'solvable': solution is not None,
                'attempts_needed': attempts,
                'clue_count': len(puzzle_data['clues']),
                'complexity_score': attempts / 100.0,  # 归一化复杂度
                'solution': solution
            }
        
        elif puzzle_type == 'sudoku':
            solution, attempts = self.solve_sudoku_puzzle(puzzle_data['puzzle'])
            
            # 计算空格数量
            empty_cells = sum(row.count(0) for row in puzzle_data['puzzle'])
            total_cells = len(puzzle_data['puzzle']) ** 2
            
            return {
                'puzzle_type': puzzle_type,
                'solvable': solution is not None,
                'attempts_needed': attempts,
                'empty_cells': empty_cells,
                'fill_rate': (total_cells - empty_cells) / total_cells,
                'complexity_score': attempts / 500.0,  # 归一化复杂度
                'solution': solution
            }
        
        return {'error': 'Unknown puzzle type'}