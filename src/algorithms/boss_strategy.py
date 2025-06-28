#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分支限界算法BOSS战策略优化
在限定回合内找到击败BOSS的最小代价技能序列
"""

import heapq
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from ..config import Config

@dataclass
class BattleState:
    """
    战斗状态类（移除玩家血量和治疗相关）
    """
    boss_hp: int  # BOSS当前血量
    player_resources: int  # 玩家剩余资源
    rounds_used: int  # 已使用回合数
    special_cooldown: int  # 大招冷却剩余回合
    skill_sequence: List[str]  # 技能序列
    
    def __lt__(self, other):
        """用于优先队列排序"""
        return self.get_priority() < other.get_priority()
    
    def get_priority(self) -> float:
        """计算状态优先级（f(n) = g(n) + h(n)）"""
        g_n = self.rounds_used  # 已用回合数
        # 启发式函数：考虑普通攻击和大招的平均伤害
        normal_damage = Config.SKILLS['normal_attack']['damage']
        special_damage = Config.SKILLS['special_attack']['damage']
        avg_damage = (normal_damage + special_damage) / 2
        h_n = max(0, self.boss_hp / avg_damage)  # 预估剩余回合数
        return g_n + h_n
    
    def is_victory(self) -> bool:
        """检查是否获胜"""
        return self.boss_hp <= 0
    
    def is_valid(self) -> bool:
        """检查状态是否有效"""
        return self.rounds_used >= 0 and self.player_resources >= 0

class BossStrategy:
    """
    分支限界BOSS战策略优化器
    """
    
    def __init__(self, boss_hp: int = Config.BOSS_HP, player_resources: int = 100):
        """
        初始化BOSS战策略
        
        Args:
            boss_hp: BOSS初始血量
            player_resources: 玩家初始资源
        """
        self.initial_boss_hp = boss_hp
        self.initial_player_resources = player_resources
        
        # 技能定义现在直接从Config获取
        self.skills = Config.SKILLS
        
        self.explored_states = set()
        self.best_solution = None
        self.nodes_explored = 0
        self.nodes_pruned = 0
    
    def find_optimal_strategy(self, max_rounds: int = 20) -> Tuple[Optional[List[str]], int, Dict]:
        """
        使用分支限界算法找到最优战斗策略
        
        Args:
            max_rounds: 最大回合数限制
        
        Returns:
            Tuple[Optional[List[str]], int, Dict]: (最优技能序列, 最少回合数, 统计信息)
        """
        # 初始化
        initial_state = BattleState(
            boss_hp=self.initial_boss_hp,
            player_resources=self.initial_player_resources,
            rounds_used=0,
            special_cooldown=0,
            skill_sequence=[]
        )
        
        # 优先队列（最小堆）
        priority_queue = [initial_state]
        self.explored_states = set()
        self.best_solution = None
        self.nodes_explored = 0
        self.nodes_pruned = 0
        
        while priority_queue:
            current_state = heapq.heappop(priority_queue)
            self.nodes_explored += 1
            
            # 生成状态键用于去重
            state_key = self._get_state_key(current_state)
            if state_key in self.explored_states:
                continue
            self.explored_states.add(state_key)
            
            # 检查是否获胜
            if current_state.is_victory():
                is_better = False
                if self.best_solution is None:
                    is_better = True
                else:
                    # 比较回合数，选择最少回合数的方案
                    current_rounds = current_state.rounds_used
                    best_rounds = len(self.best_solution)
                    
                    if current_rounds < best_rounds:
                        is_better = True
                
                if is_better:
                    self.best_solution = current_state.skill_sequence[:]
                continue
            
            # 剪枝条件
            if self._should_prune(current_state, max_rounds):
                self.nodes_pruned += 1
                continue
            
            # 生成后继状态
            successors = self._generate_successors(current_state)
            
            for successor in successors:
                if successor.is_valid():
                    heapq.heappush(priority_queue, successor)
        
        # 统计信息
        stats = {
            'nodes_explored': self.nodes_explored,
            'nodes_pruned': self.nodes_pruned,
            'states_cached': len(self.explored_states),
            'optimal_rounds': len(self.best_solution) if self.best_solution else -1
        }
        
        return self.best_solution, len(self.best_solution) if self.best_solution else -1, stats
    
    def _get_state_key(self, state: BattleState) -> Tuple:
        """
        生成状态的唯一键
        
        Args:
            state: 战斗状态
        
        Returns:
            Tuple: 状态键
        """
        return (state.boss_hp, state.special_cooldown)
    
    def _should_prune(self, state: BattleState, max_rounds: int) -> bool:
        """
        判断是否应该剪枝
        
        Args:
            state: 当前状态
            max_rounds: 最大回合数
        
        Returns:
            bool: 是否剪枝
        """
        # 超过最大回合数
        if state.rounds_used >= max_rounds:
            return True
        
        # 如果已有最优解，且当前路径不可能更优
        if (self.best_solution is not None and 
            state.rounds_used >= len(self.best_solution)):
            return True
        
        # 乐观估计：即使每回合都用最高伤害也无法获胜
        max_damage_per_round = max(s['damage'] for s in Config.SKILLS.values() if 'damage' in s)
        remaining_rounds = max_rounds - state.rounds_used
        if state.boss_hp > max_damage_per_round * remaining_rounds:
            return True
        
        return False
    
    def _generate_successors(self, state: BattleState) -> List[BattleState]:
        """
        生成后继状态
        
        Args:
            state: 当前状态
        
        Returns:
            List[BattleState]: 后继状态列表
        """
        successors = []
        
        for skill_name, skill_info in self.skills.items():
            # 检查技能是否可用
            if not self._can_use_skill(state, skill_name):
                continue
            
            # 创建新状态
            new_state = self._apply_skill(state, skill_name)
            if new_state.is_valid():
                successors.append(new_state)
        
        return successors
    
    def _can_use_skill(self, state: BattleState, skill_name: str) -> bool:
        """
        检查是否可以使用技能
        
        Args:
            state: 当前状态
            skill_name: 技能名称
        
        Returns:
            bool: 是否可用
        """
        # 只检查冷却，不检查资源
        if skill_name == 'special_attack' and state.special_cooldown > 0:
            return False
        
        return True
    
    def _apply_skill(self, state: BattleState, skill_name: str) -> BattleState:
        """
        应用技能效果，生成新状态
        
        Args:
            state: 当前状态
            skill_name: 技能名称
        
        Returns:
            BattleState: 新状态
        """
        skill = self.skills[skill_name]
        
        # 计算伤害
        damage = skill.get('damage', 0)
        
        # 创建新状态（不消耗资源）
        new_state = BattleState(
            boss_hp=max(0, state.boss_hp - damage),
            player_resources=state.player_resources,  # 不消耗资源
            rounds_used=state.rounds_used + 1,
            special_cooldown=max(0, state.special_cooldown - 1),
            skill_sequence=state.skill_sequence + [skill_name]
        )
        
        # 设置技能冷却
        if skill_name == 'special_attack':
            new_state.special_cooldown = skill['cooldown']
        
        return new_state
    

    
    def simulate_battle(self, skill_sequence: List[str]) -> Dict:
        """
        模拟战斗过程
        
        Args:
            skill_sequence: 技能序列
        
        Returns:
            Dict: 战斗结果
        """
        boss_hp = self.initial_boss_hp
        player_resources = self.initial_player_resources  # 保留但不消耗
        special_cooldown = 0
        battle_log = []
        
        for i, skill_name in enumerate(skill_sequence):
            skill = self.skills[skill_name]
            
            # 更新冷却
            if special_cooldown > 0:
                special_cooldown -= 1

            # 只检查冷却，不检查资源
            if skill_name == 'special_attack' and special_cooldown > 0:
                return {'success': False, 'reason': '技能冷却中', 'battle_log': battle_log}

            # 使用技能（不消耗资源）
            boss_hp -= skill.get('damage', 0)
            if skill_name == 'special_attack':
                special_cooldown = skill['cooldown']
            
            log_entry = {
                'round': i + 1,
                'skill': skill['name'],
                'damage': skill.get('damage', 0),
                'boss_hp': boss_hp,
                'player_resources': player_resources,  # 资源不变
                'special_cooldown': special_cooldown
            }
            battle_log.append(log_entry)
            
            if boss_hp <= 0:
                return {
                    'success': True,
                    'rounds_used': i + 1,
                    'final_resources': player_resources,
                    'battle_log': battle_log
                }
        
        return {
            'success': False,
            'reason': 'BOSS未被击败',
            'rounds_used': len(skill_sequence),
            'final_boss_hp': boss_hp,
            'battle_log': battle_log
        }
    
    def analyze_strategy_efficiency(self, skill_sequence: List[str]) -> Dict:
        """
        分析策略效率
        
        Args:
            skill_sequence: 技能序列
        
        Returns:
            Dict: 效率分析
        """
        simulation = self.simulate_battle(skill_sequence)
        
        if not simulation['success']:
            return {
                'valid': False,
                'reason': simulation['reason']
            }
        
        # 计算各种效率指标
        total_damage = sum(log['damage'] for log in simulation['battle_log'])
        # 移除资源消耗计算，因为技能不再消耗资源
        
        skill_usage = {}
        for skill in skill_sequence:
            skill_name = self.skills[skill]['name']
            skill_usage[skill_name] = skill_usage.get(skill_name, 0) + 1
        
        return {
            'valid': True,
            'rounds_used': simulation['rounds_used'],
            'total_damage': total_damage,
            'damage_per_round': total_damage / simulation['rounds_used'],
            'damage_efficiency': total_damage / simulation['rounds_used'],  # 伤害效率
            'skill_usage': skill_usage,
            'final_resources': simulation['final_resources'],
            'battle_log': simulation['battle_log']
        }
    

    
    def generate_random_strategies(self, count: int = 5, max_length: int = 15) -> List[List[str]]:
        """
        生成随机策略用于比较
        
        Args:
            count: 生成策略数量
            max_length: 最大策略长度
        
        Returns:
            List[List[str]]: 随机策略列表
        """
        import random
        
        strategies = []
        skill_names = list(self.skills.keys())
        
        for _ in range(count):
            length = random.randint(3, max_length)
            strategy = []
            
            for _ in range(length):
                # 随机选择技能，但增加普通攻击的概率
                if random.random() < 0.6:
                    strategy.append('normal_attack')
                else:
                    strategy.append(random.choice(skill_names))
            
            strategies.append(strategy)
        
        return strategies