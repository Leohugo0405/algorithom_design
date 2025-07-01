#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分支限界算法BOSS战策略优化
在限定回合内找到击败BOSS的最小代价技能序列
"""

import heapq
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
try:
    from ..config import Config
except ImportError:
    # 当作为独立模块导入时，使用绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import Config

@dataclass
class BattleState:
    """
    战斗状态类（支持多Boss战斗）
    """
    boss_hps: List[int]  # 所有BOSS的当前血量列表
    player_resources: int  # 玩家剩余资源
    rounds_used: int  # 已使用回合数
    skill_cooldowns: Dict[str, int]  # 各技能冷却剩余回合
    skill_sequence: List[str]  # 技能序列
    target_sequence: List[int]  # 每个技能的目标序列（Boss索引）
    
    def __lt__(self, other):
        """用于优先队列排序"""
        return self.get_priority() < other.get_priority()
    
    def get_priority(self) -> float:
        """计算状态优先级（f(n) = g(n) + h(n)）"""
        g_n = self.rounds_used  # 已用回合数
        # 启发式函数：基于剩余总血量和平均伤害
        if Config.SKILLS:
            damages = [skill.get('damage', 0) for skill in Config.SKILLS.values()]
            avg_damage = sum(damages) / len(damages) if damages else 1
        else:
            avg_damage = 1
        
        # 计算剩余总血量
        total_remaining_hp = sum(max(0, hp) for hp in self.boss_hps)
        h_n = max(0, total_remaining_hp / avg_damage)  # 预估剩余回合数
        return g_n + h_n
    
    def is_victory(self) -> bool:
        """检查是否获胜（所有Boss都被击败）"""
        return all(hp <= 0 for hp in self.boss_hps)
    
    def is_valid(self) -> bool:
        """检查状态是否有效"""
        return self.rounds_used >= 0 and self.player_resources >= 0

class BossStrategy:
    """
    分支限界BOSS战策略优化器（支持多Boss）
    """
    
    def __init__(self, boss_hps=None, player_resources: int = 100):
        """
        初始化BOSS战策略
        
        Args:
            boss_hps: BOSS初始血量列表，如果为None则使用单Boss模式
            player_resources: 玩家初始资源
        """
        if boss_hps is None:
            self.initial_boss_hps = [Config.BOSS_HP]
        elif isinstance(boss_hps, int):
            # 向后兼容：如果传入单个整数，转换为列表
            self.initial_boss_hps = [boss_hps]
        else:
            self.initial_boss_hps = list(boss_hps)
        
        self.initial_player_resources = player_resources
        
        # 技能定义现在直接从Config获取
        self.skills = Config.SKILLS
        
        self.explored_states = set()
        self.best_solution = None
        self.best_state = None  # 保存最优状态
        self.explored_count = 0
        self.pruned_count = 0
    
    def find_optimal_strategy(self, max_rounds: int = 20) -> Tuple[Optional[List[str]], int, Dict]:
        """
        使用优化的分支限界算法找到最优战斗策略
        
        Args:
            max_rounds: 最大回合数限制
        
        Returns:
            Tuple[Optional[List[str]], int, Dict]: (最优技能序列, 最少回合数, 统计信息)
        """
        import time
        
        start_time = time.time()
        max_depth = 0
        
        # 初始化
        initial_state = BattleState(
            boss_hps=self.initial_boss_hps[:],  # 复制列表
            player_resources=self.initial_player_resources,
            rounds_used=0,
            skill_cooldowns={skill_name: 0 for skill_name in self.skills.keys()},
            skill_sequence=[],
            target_sequence=[]
        )
        
        # 优先队列（最小堆），使用启发式函数
        priority_queue = [initial_state]
        self.explored_states = set()
        self.best_solution = None
        self.explored_count = 0
        self.pruned_count = 0
        
        # 状态压缩缓存
        self.state_cache = {}
        
        while priority_queue:
            current_state = heapq.heappop(priority_queue)
            self.explored_count += 1
            
            # 更新最大深度
            max_depth = max(max_depth, current_state.rounds_used)
            
            # 优化的状态去重：使用压缩的状态键
            state_key = self._compress_state(current_state)
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
                    self.best_state = current_state  # 保存最优状态
                    print(f"找到更优解，回合数: {len(self.best_solution)}")
                continue
            
            # 剪枝条件
            if self._should_prune(current_state, max_rounds):
                self.pruned_count += 1
                continue
            
            # 生成后继状态
            successors = self._generate_successors(current_state)
            
            for successor in successors:
                if successor.is_valid():
                    successor_key = self._compress_state(successor)
                    if successor_key not in self.explored_states:
                        heapq.heappush(priority_queue, successor)
        
        # 统计信息
        computation_time = time.time() - start_time
        stats = {
            'explored_states': self.explored_count,
            'pruned_states': self.pruned_count,
            'max_depth': max_depth,
            'computation_time': computation_time,
            'optimal_rounds': len(self.best_solution) if self.best_solution else -1
        }
        
        print(f"探索状态数: {self.explored_count}")
        print(f"剪枝状态数: {self.pruned_count}")
        if self.best_solution:
            print(f"最优解回合数: {len(self.best_solution)}")
        
        # 如果找到最优解，还需要返回对应的目标序列
        best_targets = None
        if self.best_solution and self.best_state:
            # 从最优状态中直接获取目标序列
            best_targets = self.best_state.target_sequence[:]
        elif self.best_solution:
            # 备用方案：重新模拟最优序列以获取目标序列
            simulation = self.simulate_battle(self.best_solution)
            if simulation['success']:
                best_targets = [log['target_idx'] for log in simulation['battle_log']]

        return self.best_solution, len(self.best_solution) if self.best_solution else -1, stats, best_targets
    
    def _compress_state(self, state: BattleState) -> tuple:
        """
        压缩状态表示，减少内存使用和提高比较效率
        
        Args:
            state: 战斗状态
        
        Returns:
            tuple: 压缩的状态键
        """
        # 只保留关键信息：回合数、Boss血量、关键技能冷却
        active_cooldowns = tuple(sorted(
            (skill, cd) for skill, cd in state.skill_cooldowns.items() if cd > 0
        ))
        return (state.rounds_used, tuple(state.boss_hps), active_cooldowns)
    
    def _get_state_key(self, state: BattleState) -> Tuple:
        """
        生成状态的唯一键
        
        Args:
            state: 战斗状态
        
        Returns:
            Tuple: 状态键
        """
        # 将技能冷却字典转换为有序元组
        cooldown_tuple = tuple(sorted(state.skill_cooldowns.items()))
        # 使用所有Boss血量的元组
        boss_hps_tuple = tuple(state.boss_hps)
        return (boss_hps_tuple, cooldown_tuple)
    
    def _should_prune(self, state: BattleState, max_rounds: int) -> bool:
        """
        优化的剪枝策略：丢弃代价超过当前最优解的节点
        
        Args:
            state: 当前状态
            max_rounds: 最大回合数
        
        Returns:
            bool: 是否剪枝
        """
        # 1. 超过最大回合数限制
        if state.rounds_used >= max_rounds:
            return True
        
        # 2. 严格的最优解剪枝：如果当前回合数已经达到或超过最优解，直接剪枝
        if (self.best_solution is not None and 
            state.rounds_used >= len(self.best_solution)):
            return True
        
        # 3. 更精确的下界估计剪枝：如果下界估计已经不优于当前最优解
        lower_bound = self._calculate_lower_bound(state)
        if (self.best_solution is not None and 
            lower_bound >= len(self.best_solution)):
            return True
        
        # 3.5. 动态剪枝：根据搜索深度动态调整剪枝阈值
        if self._dynamic_pruning_check(state):
            return True
        
        # 4. 乐观估计剪枝：即使使用最优策略也无法在剩余回合内获胜
        if not self._can_possibly_win(state, max_rounds):
            return True
        
        # 5. 支配性剪枝：如果存在更优的状态已被探索
        if self._is_dominated_state(state):
            return True
        
        return False
    
    def _dynamic_pruning_check(self, state: BattleState) -> bool:
        """
        动态剪枝检查：根据搜索进度和当前状态质量进行剪枝
        
        Args:
            state: 当前状态
        
        Returns:
            bool: 是否应该剪枝
        """
        # 如果搜索深度过深且没有明显进展，进行剪枝
        if hasattr(self, 'explored_count') and self.explored_count > 10000:
            # 在大量搜索后，对质量较差的状态进行更激进的剪枝
            if (self.best_solution is not None and 
                state.rounds_used >= len(self.best_solution) * 0.8):
                return True
        
        # 资源耗尽检查：如果玩家资源不足以完成战斗
        if hasattr(state, 'player_resources'):
            # 这里可以添加更复杂的资源检查逻辑
            pass
        
        return False
    
    def _calculate_lower_bound(self, state: BattleState) -> int:
        """
        计算完成战斗所需的最少回合数下界
        
        Args:
            state: 当前状态
        
        Returns:
            int: 下界估计
        """
        total_remaining_hp = sum(max(0, hp) for hp in state.boss_hps)
        if total_remaining_hp <= 0:
            return state.rounds_used
        
        # 考虑技能冷却的最优伤害序列
        available_skills = []
        for skill_name, skill_info in self.skills.items():
            damage = skill_info.get('damage', 0)
            cooldown = skill_info.get('cooldown', 0)
            if damage > 0:
                available_skills.append((damage, cooldown, skill_name))
        
        if not available_skills:
            return float('inf')
        
        # 排序：优先考虑伤害/冷却比率高的技能
        available_skills.sort(key=lambda x: x[0] / (x[1] + 1), reverse=True)
        
        # 模拟最优技能使用序列
        remaining_hp = total_remaining_hp
        rounds_needed = 0
        skill_cooldowns = state.skill_cooldowns.copy()
        
        while remaining_hp > 0 and rounds_needed < 50:  # 防止无限循环
            best_skill = None
            best_damage = 0
            
            # 找到当前可用的最佳技能
            for damage, cooldown, skill_name in available_skills:
                if skill_cooldowns.get(skill_name, 0) <= 0 and damage > best_damage:
                    best_skill = (damage, cooldown, skill_name)
                    best_damage = damage
            
            if best_skill is None:
                # 没有可用技能，所有技能冷却减1
                for skill_name in skill_cooldowns:
                    skill_cooldowns[skill_name] = max(0, skill_cooldowns[skill_name] - 1)
                rounds_needed += 1
                continue
            
            # 使用最佳技能
            damage, cooldown, skill_name = best_skill
            remaining_hp -= damage
            rounds_needed += 1
            
            # 更新冷却
            for skill_name_cd in skill_cooldowns:
                skill_cooldowns[skill_name_cd] = max(0, skill_cooldowns[skill_name_cd] - 1)
            skill_cooldowns[skill_name] = cooldown
        
        return state.rounds_used + rounds_needed
    
    def _can_possibly_win(self, state: BattleState, max_rounds: int) -> bool:
        """
        检查在剩余回合内是否可能获胜
        
        Args:
            state: 当前状态
            max_rounds: 最大回合数
        
        Returns:
            bool: 是否可能获胜
        """
        remaining_rounds = max_rounds - state.rounds_used
        if remaining_rounds <= 0:
            return state.is_victory()
        
        total_remaining_hp = sum(max(0, hp) for hp in state.boss_hps)
        if total_remaining_hp <= 0:
            return True
        
        # 计算理论最大伤害输出
        max_damage_per_round = 0
        if self.skills:
            damages = [skill.get('damage', 0) for skill in self.skills.values()]
            max_damage_per_round = max(damages) if damages else 0
        
        # 乐观估计：假设每回合都能造成最大伤害
        max_possible_damage = max_damage_per_round * remaining_rounds
        
        return max_possible_damage >= total_remaining_hp
    
    def _is_dominated_state(self, state: BattleState) -> bool:
        """
        检查当前状态是否被已探索的状态支配
        一个状态A支配状态B，当且仅当：
        1. A的回合数 <= B的回合数
        2. A的所有Boss血量 <= B的对应Boss血量
        3. A的技能冷却状态 <= B的技能冷却状态
        
        Args:
            state: 当前状态
        
        Returns:
            bool: 是否被支配
        """
        # 为了性能考虑，这里使用简化的支配性检查
        # 只检查相同回合数下的状态
        current_key = (state.rounds_used, tuple(state.boss_hps))
        
        # 检查是否存在更优的相似状态
        for explored_key in self.explored_states:
            if isinstance(explored_key, tuple) and len(explored_key) >= 2:
                explored_rounds = explored_key[0] if isinstance(explored_key[0], int) else 0
                explored_boss_hps = explored_key[1] if isinstance(explored_key[1], tuple) else ()
                
                # 如果找到回合数相同但Boss血量更低的状态，则当前状态被支配
                if (explored_rounds == state.rounds_used and 
                    len(explored_boss_hps) == len(state.boss_hps) and
                    all(explored_hp <= current_hp for explored_hp, current_hp in zip(explored_boss_hps, state.boss_hps)) and
                    explored_boss_hps != tuple(state.boss_hps)):  # 不是完全相同的状态
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
            
            # 如果是攻击技能，为每个活着的Boss生成后继状态
            if skill_info.get('damage', 0) > 0:
                for target_idx, boss_hp in enumerate(state.boss_hps):
                    if boss_hp > 0:  # 只攻击活着的Boss
                        new_state = self._apply_skill(state, skill_name, target_idx)
                        if new_state.is_valid():
                            successors.append(new_state)
            else:
                # 非攻击技能（如治疗、增益等），不需要目标
                new_state = self._apply_skill(state, skill_name, -1)
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
        # 检查技能冷却
        if skill_name in state.skill_cooldowns and state.skill_cooldowns[skill_name] > 0:
            return False
        
        return True
    
    def _apply_skill(self, state: BattleState, skill_name: str, target_idx: int = -1) -> BattleState:
        """
        应用技能效果，生成新状态
        
        Args:
            state: 当前状态
            skill_name: 技能名称
            target_idx: 目标Boss索引，-1表示非攻击技能
        
        Returns:
            BattleState: 新状态
        """
        skill = self.skills[skill_name]
        
        # 计算伤害
        damage = skill.get('damage', 0)
        
        # 更新技能冷却：所有技能冷却减1，当前使用的技能设置新冷却
        new_cooldowns = {}
        for skill_key in state.skill_cooldowns:
            new_cooldowns[skill_key] = max(0, state.skill_cooldowns[skill_key] - 1)
        
        # 设置当前技能的冷却
        new_cooldowns[skill_name] = skill.get('cooldown', 0)
        
        # 更新Boss血量
        new_boss_hps = state.boss_hps[:]
        if target_idx >= 0 and target_idx < len(new_boss_hps) and damage > 0:
            new_boss_hps[target_idx] = max(0, new_boss_hps[target_idx] - damage)
        
        # 创建新状态（不消耗资源）
        new_state = BattleState(
            boss_hps=new_boss_hps,
            player_resources=state.player_resources,  # 不消耗资源
            rounds_used=state.rounds_used + 1,
            skill_cooldowns=new_cooldowns,
            skill_sequence=state.skill_sequence + [skill_name],
            target_sequence=state.target_sequence + [target_idx]
        )
        
        return new_state
    

    
    def simulate_battle(self, skill_sequence: List[str], target_sequence: List[int] = None) -> Dict:
        """
        模拟战斗过程
        
        Args:
            skill_sequence: 技能序列
            target_sequence: 目标序列（Boss索引），如果为None则自动选择目标
        
        Returns:
            Dict: 战斗结果
        """
        boss_hps = self.initial_boss_hps[:]
        player_resources = self.initial_player_resources  # 保留但不消耗
        skill_cooldowns = {skill_name: 0 for skill_name in self.skills.keys()}
        battle_log = []
        
        # 如果没有提供目标序列，自动生成（动态选择目标）
        if target_sequence is None:
            target_sequence = []
            current_boss_hps = boss_hps[:]
            
            for skill_name in skill_sequence:
                skill = self.skills[skill_name]
                if skill.get('damage', 0) > 0:
                    # 选择血量最高的活着的Boss
                    alive_bosses = [(i, hp) for i, hp in enumerate(current_boss_hps) if hp > 0]
                    if alive_bosses:
                        target_idx = max(alive_bosses, key=lambda x: x[1])[0]
                        target_sequence.append(target_idx)
                        # 模拟伤害以更新血量，用于下次目标选择
                        damage = skill.get('damage', 0)
                        current_boss_hps[target_idx] = max(0, current_boss_hps[target_idx] - damage)
                    else:
                        target_sequence.append(-1)
                else:
                    # 非攻击技能使用-1表示无目标
                    target_sequence.append(-1)
        
        for i, skill_name in enumerate(skill_sequence):
            if skill_name not in self.skills:
                return {'success': False, 'reason': f'未知技能: {skill_name}', 'battle_log': battle_log}
                
            skill = self.skills[skill_name]
            target_idx = target_sequence[i] if i < len(target_sequence) else -1
            
            # 更新所有技能冷却
            for skill_key in skill_cooldowns:
                skill_cooldowns[skill_key] = max(0, skill_cooldowns[skill_key] - 1)

            # 检查技能是否可用
            if skill_cooldowns.get(skill_name, 0) > 0:
                return {'success': False, 'reason': f'技能 {skill["name"]} 冷却中', 'battle_log': battle_log}

            # 使用技能（不消耗资源）
            damage = skill.get('damage', 0)
            if target_idx >= 0 and target_idx < len(boss_hps) and damage > 0:
                boss_hps[target_idx] = max(0, boss_hps[target_idx] - damage)
            
            skill_cooldowns[skill_name] = skill.get('cooldown', 0)
            
            log_entry = {
                'round': i + 1,
                'skill': skill['name'],
                'damage': damage,
                'target_idx': target_idx,
                'boss_hps': boss_hps[:],
                'player_resources': player_resources,  # 资源不变
                'skill_cooldowns': skill_cooldowns.copy()
            }
            battle_log.append(log_entry)
            
            # 检查是否所有Boss都被击败
            if all(hp <= 0 for hp in boss_hps):
                return {
                    'success': True,
                    'rounds_used': i + 1,
                    'final_resources': player_resources,
                    'battle_log': battle_log
                }
        
        return {
            'success': False,
            'reason': '未能击败所有Boss',
            'rounds_used': len(skill_sequence),
            'final_boss_hps': boss_hps,
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
        
        if not skill_names:
            return strategies
        
        # 找到冷却时间最短的技能（通常是基础攻击）
        min_cooldown_skill = min(skill_names, key=lambda x: self.skills[x].get('cooldown', 0))
        
        for _ in range(count):
            length = random.randint(3, max_length)
            strategy = []
            
            for _ in range(length):
                # 随机选择技能，但增加低冷却技能的概率
                if random.random() < 0.6:
                    strategy.append(min_cooldown_skill)
                else:
                    strategy.append(random.choice(skill_names))
            
            strategies.append(strategy)
        
        return strategies