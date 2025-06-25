#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多怪物战斗系统
支持同时与多个怪物战斗，玩家可以选择攻击目标
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..config import Config

@dataclass
class Monster:
    """
    怪物类
    """
    id: int
    name: str
    max_hp: int
    current_hp: int
    attack_damage: int
    defense: int
    alive: bool = True
    
    def take_damage(self, damage: int) -> int:
        """受到伤害"""
        actual_damage = max(1, damage - self.defense)  # 至少造成1点伤害
        self.current_hp -= actual_damage
        if self.current_hp <= 0:
            self.current_hp = 0
            self.alive = False
        return actual_damage
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.alive and self.current_hp > 0
    
    def get_hp_percentage(self) -> float:
        """获取血量百分比"""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0

class MultiMonsterBattle:
    """
    多怪物战斗管理器
    """
    
    def __init__(self, monster_configs: List[Dict]):
        """
        初始化多怪物战斗
        
        Args:
            monster_configs: 怪物配置列表
        """
        self.monsters: List[Monster] = []
        self.player_hp = 100
        self.player_max_hp = 100
        self.player_resources = 100
        self.skill_cooldowns = {skill: 0 for skill in Config.SKILLS.keys()}
        self.battle_log = []
        self.turn_count = 0
        self.battle_active = True
        
        # 创建怪物
        for i, config in enumerate(monster_configs):
            monster = Monster(
                id=i,
                name=config.get('name', f'怪物{i+1}'),
                max_hp=config.get('hp', 30),
                current_hp=config.get('hp', 30),
                attack_damage=config.get('attack', 8),
                defense=config.get('defense', 0)
            )
            self.monsters.append(monster)
        
        self.add_log(f"战斗开始！面对{len(self.monsters)}个怪物！")
    
    def add_log(self, message: str):
        """添加战斗日志"""
        self.battle_log.append(f"回合{self.turn_count}: {message}")
    
    def get_alive_monsters(self) -> List[Monster]:
        """获取存活的怪物列表"""
        return [monster for monster in self.monsters if monster.is_alive()]
    
    def get_battle_state(self) -> Dict:
        """获取当前战斗状态"""
        return {
            'player_hp': self.player_hp,
            'player_max_hp': self.player_max_hp,
            'player_resources': self.player_resources,
            'monsters': [
                {
                    'id': monster.id,
                    'name': monster.name,
                    'current_hp': monster.current_hp,
                    'max_hp': monster.max_hp,
                    'alive': monster.is_alive(),
                    'hp_percentage': monster.get_hp_percentage()
                }
                for monster in self.monsters
            ],
            'skill_cooldowns': self.skill_cooldowns.copy(),
            'available_skills': self.get_available_skills(),
            'battle_active': self.battle_active,
            'turn_count': self.turn_count,
            'battle_log': self.battle_log[-5:]  # 只返回最近5条日志
        }
    
    def get_available_skills(self) -> Dict[str, bool]:
        """获取可用技能"""
        available = {}
        for skill_name, skill_info in Config.SKILLS.items():
            can_use = True
            
            # 移除资源检查，技能不消耗资源
            
            # 检查冷却
            if self.skill_cooldowns.get(skill_name, 0) > 0:
                can_use = False
            
            available[skill_name] = can_use
        
        return available
    
    def execute_player_turn(self, skill_name: str, target_monster_id: Optional[int] = None) -> Dict:
        """执行玩家回合"""
        if not self.battle_active:
            return {'success': False, 'message': '战斗已结束'}
        
        if skill_name not in Config.SKILLS:
            return {'success': False, 'message': '无效的技能'}
        
        skill_info = Config.SKILLS[skill_name]
        
        # 检查技能是否可用
        if not self.get_available_skills().get(skill_name, False):
            return {'success': False, 'message': f'无法使用技能: {skill_info["name"]}'}
        
        self.turn_count += 1
        
        # 更新冷却时间
        for skill in self.skill_cooldowns:
            if self.skill_cooldowns[skill] > 0:
                self.skill_cooldowns[skill] -= 1
        
        # 设置冷却（不消耗资源）
        self.skill_cooldowns[skill_name] = skill_info.get('cooldown', 0)
        
        result = {
            'success': True,
            'skill_used': skill_name,
            'skill_name': skill_info['name'],
            'damage_dealt': 0,
            'heal_amount': 0,
            'target_monster': None,
            'monster_defeated': False
        }
        
        # 处理攻击技能
        if 'damage' in skill_info:
            alive_monsters = self.get_alive_monsters()
            if not alive_monsters:
                return {'success': False, 'message': '没有可攻击的目标'}
            
            # 选择目标
            target = None
            if target_monster_id is not None:
                target = next((m for m in alive_monsters if m.id == target_monster_id), None)
            
            if target is None:
                # 如果没有指定目标或目标无效，选择第一个存活的怪物
                target = alive_monsters[0]
            
            # 造成伤害
            damage = skill_info['damage']
            actual_damage = target.take_damage(damage)
            result['damage_dealt'] = actual_damage
            result['target_monster'] = {
                'id': target.id,
                'name': target.name,
                'remaining_hp': target.current_hp
            }
            
            self.add_log(f"你对{target.name}使用了{skill_info['name']}，造成{actual_damage}点伤害")
            
            if not target.is_alive():
                result['monster_defeated'] = True
                self.add_log(f"{target.name}被击败了！")
        
        # 处理治疗技能
        if 'heal_amount' in skill_info:
            heal_amount = skill_info['heal_amount']
            old_hp = self.player_hp
            self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
            actual_heal = self.player_hp - old_hp
            result['heal_amount'] = actual_heal
            self.add_log(f"你使用了{skill_info['name']}，恢复了{actual_heal}点生命值")
        
        # 检查胜利条件
        if not self.get_alive_monsters():
            self.battle_active = False
            result['battle_status'] = 'victory'
            self.add_log("所有怪物都被击败了！战斗胜利！")
            return result
        
        # 怪物回合
        monster_actions = self.execute_monster_turns()
        result['monster_actions'] = monster_actions
        
        # 检查失败条件
        if self.player_hp <= 0:
            self.battle_active = False
            result['battle_status'] = 'defeat'
            self.add_log("你被击败了！")
        else:
            result['battle_status'] = 'ongoing'
        
        return result
    
    def execute_monster_turns(self) -> List[Dict]:
        """执行所有怪物的回合"""
        monster_actions = []
        alive_monsters = self.get_alive_monsters()
        
        for monster in alive_monsters:
            # 简单AI：直接攻击玩家
            damage = monster.attack_damage
            self.player_hp -= damage
            
            action = {
                'monster_id': monster.id,
                'monster_name': monster.name,
                'action': 'attack',
                'damage': damage
            }
            monster_actions.append(action)
            
            self.add_log(f"{monster.name}攻击了你，造成{damage}点伤害")
        
        return monster_actions
    
    def get_battle_result(self) -> Dict:
        """获取战斗结果"""
        if self.battle_active:
            return {'status': 'ongoing'}
        
        alive_monsters = self.get_alive_monsters()
        if not alive_monsters:
            # 胜利
            reward = len(self.monsters) * 20  # 每个怪物20资源奖励
            return {
                'status': 'victory',
                'reward': reward,
                'turns_used': self.turn_count,
                'message': f'战斗胜利！击败了{len(self.monsters)}个怪物，获得{reward}资源奖励'
            }
        else:
            # 失败
            return {
                'status': 'defeat',
                'turns_used': self.turn_count,
                'message': '战斗失败！'
            }
    
    def get_optimal_target_suggestion(self) -> Optional[int]:
        """获取最优攻击目标建议"""
        alive_monsters = self.get_alive_monsters()
        if not alive_monsters:
            return None
        
        # 简单策略：优先攻击血量最少的怪物
        target = min(alive_monsters, key=lambda m: m.current_hp)
        return target.id