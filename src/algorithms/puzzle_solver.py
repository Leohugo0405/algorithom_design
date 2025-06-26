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
        self.max_attempts = 1005  # 防止无限递归
    
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
    
    def solve_password_puzzle(self, clues: List[str], correct_password: Optional[List[int]] = None) -> Tuple[Optional[List[int]], int]:
        """
        使用回溯法解决密码谜题
        
        Args:
            clues: 线索列表
            correct_password: 正确的密码（可选）
        
        Returns:
            Tuple[Optional[List[int]], int]: (解答, 尝试次数)
        """
        self.attempt_count = 0
        
        # 解析线索为约束条件
        constraints = self._parse_clues(clues)
        
        # 使用回溯法求解
        solution = self._backtrack_solve([], constraints, correct_password)
        
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
                def unique_digits(pwd):
                    return len(pwd) == 0 or len(set(pwd)) == len(pwd)
                constraints.append(unique_digits)
            
            elif "第一位数字不为0" in clue:
                def first_not_zero(pwd):
                    return len(pwd) == 0 or pwd[0] != 0
                constraints.append(first_not_zero)
            
            elif "第一位数字是质数" in clue:
                def first_is_prime(pwd):
                    return len(pwd) == 0 or self._is_prime(pwd[0])
                constraints.append(first_is_prime)
            
            elif "第一位数字是合数" in clue:
                def first_is_composite(pwd):
                    return len(pwd) == 0 or (not self._is_prime(pwd[0]) and pwd[0] > 1)
                constraints.append(first_is_composite)
            
            elif "第二位数字是偶数" in clue:
                def second_is_even(pwd):
                    return len(pwd) <= 1 or pwd[1] % 2 == 0
                constraints.append(second_is_even)
            
            elif "第二位数字是奇数" in clue:
                def second_is_odd(pwd):
                    return len(pwd) <= 1 or pwd[1] % 2 == 1
                constraints.append(second_is_odd)
            
            elif "第一位数字大于第二位数字" in clue:
                def first_greater_than_second(pwd):
                    return len(pwd) <= 1 or pwd[0] > pwd[1]
                constraints.append(first_greater_than_second)
            
            elif "第一位数字小于第二位数字" in clue:
                def first_less_than_second(pwd):
                    return len(pwd) <= 1 or pwd[0] < pwd[1]
                constraints.append(first_less_than_second)
            
            elif "第三位数字大于第二位数字" in clue:
                def third_greater_than_second(pwd):
                    return len(pwd) <= 2 or pwd[2] > pwd[1]
                constraints.append(third_greater_than_second)
            
            elif "第三位数字小于第二位数字" in clue:
                def third_less_than_second(pwd):
                    return len(pwd) <= 2 or pwd[2] < pwd[1]
                constraints.append(third_less_than_second)
            
            elif "三个数字的和是偶数" in clue:
                def sum_is_even(pwd):
                    return len(pwd) != 3 or sum(pwd) % 2 == 0
                constraints.append(sum_is_even)
            
            elif "三个数字的和是奇数" in clue:
                def sum_is_odd(pwd):
                    return len(pwd) != 3 or sum(pwd) % 2 == 1
                constraints.append(sum_is_odd)
            
            elif "三个数字的和大于15" in clue:
                def sum_greater_than_15(pwd):
                    return len(pwd) != 3 or sum(pwd) > 15
                constraints.append(sum_greater_than_15)
            
            elif "三个数字的和不大于15" in clue:
                def sum_not_greater_than_15(pwd):
                    return len(pwd) != 3 or sum(pwd) <= 15
                constraints.append(sum_not_greater_than_15)
        
        return constraints
    
    def _backtrack_solve(self, current_password: List[int], constraints: List[Callable], correct_password: Optional[List[int]] = None) -> Optional[List[int]]:
        """
        回溯法求解密码
        
        Args:
            current_password: 当前部分密码
            constraints: 约束条件列表
            correct_password: 正确的密码（可选）
        
        Returns:
            Optional[List[int]]: 完整密码或None
        """
        self.attempt_count += 1
        
        if self.attempt_count > self.max_attempts:
            return None
        
        # 检查当前密码是否满足所有约束
        if not self._check_constraints(current_password, constraints):
            return None
        
        # 如果密码已完整，检查是否满足所有约束条件
        if len(current_password) == Config.LOCK_DIGITS:
            # if self._check_constraints(current_password, constraints):
            #     # 如果提供了正确密码，必须与正确密码匹配
            #     if correct_password is not None:
            #         if current_password == correct_password:
            #             return current_password[:]
            #         else:
            #             return None
            #     else:
            #         return current_password[:]
            if current_password == correct_password:
                return current_password[:]
            else:
                return None
        
        # 尝试下一位数字
        digit_range = range(1, 10) if len(current_password) == 0 else range(0, 10)
        
        
        for digit in digit_range:
            # 剪枝：避免重复数字
            if digit in current_password:
                continue
            
            # 添加数字并递归
            current_password.append(digit)
            result = self._backtrack_solve(current_password, constraints, correct_password)
            
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