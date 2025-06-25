# -*- coding: utf-8 -*-
"""
多目标BOSS战策略优化
考虑回合冷却和固定击败顺序的最优策略算法
"""

import heapq
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from ..config import Config

@dataclass
class MultiTargetState:
    """
    多目标战斗状态类
    """
    monster_hps: List[int]  # 各怪物当前血量
    player_resources: int  # 玩家剩余资源
    rounds_used: int  # 已使用回合数
    special_cooldown: int  # 大招冷却剩余回合
    heal_cooldown: int  # 治疗冷却剩余回合
    skill_sequence: List[Tuple[str, int]]  # 技能序列（技能名，目标ID）
    defeated_order: List[int]  # 已击败怪物的顺序
    
    def __lt__(self, other):
        """用于优先队列排序"""
        return self.get_priority() < other.get_priority()
    
    def get_priority(self) -> float:
        """计算状态优先级（f(n) = g(n) + h(n)）"""
        g_n = self.rounds_used  # 已用回合数
        # 预估剩余回合数：剩余血量总和除以平均伤害
        remaining_hp = sum(hp for hp in self.monster_hps if hp > 0)
        avg_damage = Config.SKILLS['normal_attack']['damage']
        h_n = max(0, remaining_hp / avg_damage)
        return g_n + h_n
    
    def is_victory(self) -> bool:
        """检查是否获胜（所有怪物被击败）"""
        return all(hp <= 0 for hp in self.monster_hps)
    
    def is_valid(self) -> bool:
        """检查状态是否有效"""
        return self.rounds_used >= 0
    
    def get_alive_monsters(self) -> List[int]:
        """获取存活怪物的ID列表"""
        return [i for i, hp in enumerate(self.monster_hps) if hp > 0]

class MultiTargetBossStrategy:
    """
    多目标BOSS战策略优化器
    考虑回合冷却和固定击败顺序
    """
    
    def __init__(self, monster_hps: List[int], target_priorities: List[int], 
                 player_resources: int = 100):
        """
        初始化多目标BOSS战策略
        
        Args:
            monster_hps: 各怪物初始血量列表
            target_priorities: 目标击败优先级顺序（怪物ID列表）
            player_resources: 玩家初始资源
        """
        self.initial_monster_hps = monster_hps[:]
        self.target_priorities = target_priorities[:]
        self.initial_player_resources = player_resources
        
        # 技能定义
        self.skills = Config.SKILLS
        
        self.explored_states = set()
        self.best_solution = None
        self.best_defeated_order = None
        self.nodes_explored = 0
        self.nodes_pruned = 0
    
    def find_optimal_strategy(self, max_rounds: int = 30) -> Tuple[Optional[List[Tuple[str, int]]], int, Dict]:
        """
        使用分支限界算法找到最优多目标战斗策略
        
        Args:
            max_rounds: 最大回合数限制
        
        Returns:
            Tuple[Optional[List[Tuple[str, int]]], int, Dict]: (最优技能序列, 最少回合数, 统计信息)
        """
        # 初始化
        initial_state = MultiTargetState(
            monster_hps=self.initial_monster_hps[:],
            player_resources=self.initial_player_resources,
            rounds_used=0,
            special_cooldown=0,
            heal_cooldown=0,
            skill_sequence=[],
            defeated_order=[]
        )
        
        # 优先队列（最小堆）
        priority_queue = [initial_state]
        self.explored_states = set()
        self.best_solution = None
        self.best_defeated_order = None
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
                    # 比较回合数和目标击败顺序
                    current_rounds = current_state.rounds_used
                    best_rounds = len(self.best_solution)
                    current_order_score = self._evaluate_defeat_order(current_state.defeated_order)
                    best_order_score = self._evaluate_defeat_order(self.best_defeated_order)
                    
                    if current_rounds < best_rounds:
                        is_better = True
                    elif current_rounds == best_rounds and current_order_score > best_order_score:
                        # 回合数相同时，优先选择击败顺序更好的方案
                        is_better = True
                
                if is_better:
                    self.best_solution = current_state.skill_sequence[:]
                    self.best_defeated_order = current_state.defeated_order[:]
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
            'optimal_rounds': len(self.best_solution) if self.best_solution else -1,
            'defeated_order': self.best_defeated_order if self.best_defeated_order else [],
            'order_score': self._evaluate_defeat_order(self.best_defeated_order) if self.best_defeated_order else 0
        }
        
        return self.best_solution, len(self.best_solution) if self.best_solution else -1, stats
    
    def _get_state_key(self, state: MultiTargetState) -> Tuple:
        """生成状态的唯一键"""
        return (tuple(state.monster_hps), state.special_cooldown, state.heal_cooldown, tuple(state.defeated_order))
    
    def _should_prune(self, state: MultiTargetState, max_rounds: int) -> bool:
        """判断是否应该剪枝"""
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
        total_remaining_hp = sum(hp for hp in state.monster_hps if hp > 0)
        if total_remaining_hp > max_damage_per_round * remaining_rounds:
            return True
        
        return False
    
    def _generate_successors(self, state: MultiTargetState) -> List[MultiTargetState]:
        """生成后继状态"""
        successors = []
        alive_monsters = state.get_alive_monsters()
        
        for skill_name in self.skills.keys():
            # 检查技能是否可用
            if not self._can_use_skill(state, skill_name):
                continue
            
            # 对每个存活的怪物生成攻击状态
            if skill_name in ['normal_attack', 'special_attack']:
                for target_id in alive_monsters:
                    new_state = self._apply_skill(state, skill_name, target_id)
                    if new_state.is_valid():
                        successors.append(new_state)
            else:
                # 治疗等非攻击技能不需要目标
                new_state = self._apply_skill(state, skill_name, -1)
                if new_state.is_valid():
                    successors.append(new_state)
        
        return successors
    
    def _can_use_skill(self, state: MultiTargetState, skill_name: str) -> bool:
        """检查是否可以使用技能"""
        # 只检查冷却，不检查资源
        if skill_name == 'special_attack' and state.special_cooldown > 0:
            return False
        
        if skill_name == 'heal' and state.heal_cooldown > 0:
            return False
        
        return True
    
    def _apply_skill(self, state: MultiTargetState, skill_name: str, target_id: int) -> MultiTargetState:
        """应用技能效果，生成新状态"""
        skill = self.skills[skill_name]
        
        # 复制当前状态
        new_monster_hps = state.monster_hps[:]
        new_defeated_order = state.defeated_order[:]
        
        # 应用技能效果
        if skill_name in ['normal_attack', 'special_attack'] and target_id >= 0:
            damage = skill.get('damage', 0)
            if target_id < len(new_monster_hps) and new_monster_hps[target_id] > 0:
                new_monster_hps[target_id] = max(0, new_monster_hps[target_id] - damage)
                
                # 如果怪物被击败，记录击败顺序
                if new_monster_hps[target_id] == 0 and target_id not in new_defeated_order:
                    new_defeated_order.append(target_id)
        
        # 创建新状态
        new_state = MultiTargetState(
            monster_hps=new_monster_hps,
            player_resources=state.player_resources,  # 不消耗资源
            rounds_used=state.rounds_used + 1,
            special_cooldown=max(0, state.special_cooldown - 1),
            heal_cooldown=max(0, state.heal_cooldown - 1),
            skill_sequence=state.skill_sequence + [(skill_name, target_id)],
            defeated_order=new_defeated_order
        )
        
        # 设置技能冷却
        if skill_name == 'special_attack':
            new_state.special_cooldown = skill['cooldown']
        elif skill_name == 'heal':
            new_state.heal_cooldown = skill['cooldown']
        
        return new_state
    
    def _evaluate_defeat_order(self, defeated_order: List[int]) -> float:
        """评估击败顺序的优劣"""
        if not self.target_priorities or not defeated_order:
            return 0.0
        
        score = 0.0
        # 计算与理想顺序的匹配度
        for i, actual_target in enumerate(defeated_order):
            if i < len(self.target_priorities):
                expected_target = self.target_priorities[i]
                if actual_target == expected_target:
                    # 按正确顺序击败，给予递减奖励
                    score += (len(self.target_priorities) - i) * 10
                else:
                    # 顺序错误，给予惩罚
                    score -= 5
        
        return score
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        if not self.best_solution:
            return "未找到有效策略"
        
        description = f"最优策略（{len(self.best_solution)}回合）：\n"
        for i, (skill_name, target_id) in enumerate(self.best_solution):
            skill_display = Config.SKILLS[skill_name]['name']
            if target_id >= 0:
                description += f"回合{i+1}: {skill_display} -> 目标{target_id+1}\n"
            else:
                description += f"回合{i+1}: {skill_display}\n"
        
        if self.best_defeated_order:
            description += f"\n击败顺序: {[f'目标{id+1}' for id in self.best_defeated_order]}\n"
            order_score = self._evaluate_defeat_order(self.best_defeated_order)
            description += f"顺序评分: {order_score:.1f}\n"
        
        return description