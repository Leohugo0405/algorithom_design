#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多怪物战斗UI界面模块
提供可视化的多怪物战斗界面和目标选择交互
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional
try:
    from ..config import Config
    from ..battle.multi_monster_battle import MultiMonsterBattle
    from ..algorithms.boss_strategy import BossStrategy
    from ..algorithms.multi_target_boss_strategy import MultiTargetBossStrategy
except ImportError:
    # 当作为独立模块运行时的导入方式
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import Config
    from battle.multi_monster_battle import MultiMonsterBattle
    from algorithms.boss_strategy import BossStrategy
    from algorithms.multi_target_boss_strategy import MultiTargetBossStrategy

class MultiMonsterBattleUI:
    """
    多怪物战斗用户界面类
    """
    
    def __init__(self, scenario_name: str = 'medium', player_resources: int = 100, auto_start_battle: bool = False):
        """
        初始化多怪物战斗UI
        
        Args:
            scenario_name: 战斗场景名称
            player_resources: 玩家当前资源值
            auto_start_battle: 是否自动开始战斗
        """
        self.scenario_name = scenario_name
        self.player_resources = player_resources
        self.auto_start_battle = auto_start_battle
        
        # 创建怪物配置 - 动态适应当前配置
        self._initialize_battle_from_current_config()
        
    def _initialize_battle_from_current_config(self):
        """
        根据当前配置初始化战斗系统
        """
        monster_configs = []
        
        # 检查是否有预定义场景且场景中的怪物类型存在
        if (self.scenario_name in Config.MULTI_BATTLE_SCENARIOS and 
            all(monster_type in Config.MONSTER_TYPES 
                for monster_type in Config.MULTI_BATTLE_SCENARIOS[self.scenario_name]['monsters'])):
            # 使用预定义场景
            self.scenario = Config.MULTI_BATTLE_SCENARIOS[self.scenario_name]
            for monster_type in self.scenario['monsters']:
                monster_config = Config.MONSTER_TYPES[monster_type].copy()
                monster_configs.append(monster_config)
        else:
            # 使用当前可用的怪物类型创建默认场景
            available_monsters = list(Config.MONSTER_TYPES.keys())
            if available_monsters:
                # 创建动态场景，使用JSON文件中所有的boss
                self.scenario = {
                    'name': '当前配置战斗',
                    'monsters': available_monsters  # 使用所有可用的怪物，不限制数量
                }
                for monster_type in self.scenario['monsters']:
                    monster_config = Config.MONSTER_TYPES[monster_type].copy()
                    monster_configs.append(monster_config)
            else:
                # 如果没有可用怪物，创建默认配置
                self.scenario = {'name': '默认战斗', 'monsters': []}
                monster_configs = [{'name': '默认敌人', 'hp': 50, 'attack': 10, 'defense': 2}]
        
        self.battle = MultiMonsterBattle(monster_configs, self.player_resources)
        
        # pygame组件
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # UI状态
        self.running = True
        self.selected_skill = None
        self.selected_target = None
        self.battle_result = None
        self.show_target_selection = False
        self.show_strategy_result = False
        self.optimal_strategy = None
        self.strategy_stats = None
        self.monster_targets = {}
        
        # 滚动状态 - 分别为技能区域、怪物区域和玩家区域
        self.skill_scroll_offset = 0
        self.skill_max_scroll_offset = 0
        self.monster_scroll_offset = 0
        self.monster_max_scroll_offset = 0
        self.player_scroll_offset = 0
        self.player_max_scroll_offset = 0
        
        # 策略结果滚动状态（保持原有功能）
        self.scroll_offset = 0
        self.max_scroll_offset = 0
        
        # 配置加载相关
        self.show_config_dialog = False
        self.config_files = []
        self.selected_config_file = None
        
        # UI布局
        self.player_area = pygame.Rect(50, 500, 300, 150)
        self.monsters_area = pygame.Rect(400, 100, 350, 400)
        self.skill_area = pygame.Rect(50, 300, 300, 180)
        self.log_area = pygame.Rect(50, 50, 300, 200)
        self.target_selection_area = pygame.Rect(400, 520, 350, 130)
        
        # 按钮
        self.skill_buttons = {}
        self.monster_buttons = {}
        self.confirm_button = pygame.Rect(600, 670, 100, 30)
        self.cancel_button = pygame.Rect(720, 670, 100, 30)
        self.strategy_button = pygame.Rect(50, 680, 150, 30)  # 策略优化按钮
        self.auto_battle_button = pygame.Rect(220, 680, 150, 30)  # 自动战斗按钮
        
        # 自动战斗相关状态
        self.auto_battle_active = False
        self.auto_battle_sequence = []
        self.auto_battle_targets = {}
        self.auto_battle_step = 0
        self.auto_battle_timer = 0
        self.auto_battle_delay = 1500  # 每步延迟1.5秒
        self.auto_battle_last_time = 0
        
        self._initialize_pygame()
    
    def _render_mixed_text(self, text: str, font_size: str = 'normal', color=(255, 255, 255)) -> pygame.Surface:
        """
        渲染混合文本（emoji + 普通文字）
        
        Args:
            text: 要渲染的文本
            font_size: 字体大小 ('small', 'normal', 'title')
            color: 文字颜色
        
        Returns:
            渲染后的Surface
        """
        # 处理空文本
        if not text or text.strip() == "":
            # 选择合适的字体来获取高度
            if font_size == 'small':
                font_height = 14  # 默认小字体高度
            elif font_size == 'title':
                font_height = 24  # 默认标题字体高度
            else:
                font_height = 20  # 默认普通字体高度
            return pygame.Surface((1, font_height), pygame.SRCALPHA)
        
        # 选择字体
        if font_size == 'small':
            text_font = self.small_font
            emoji_font = self.emoji_small_font
        elif font_size == 'title':
            text_font = self.title_font
            emoji_font = self.emoji_title_font
        else:
            text_font = self.font
            emoji_font = self.emoji_font
        
        # 分离emoji和普通文字
        parts = []
        current_part = ""
        is_emoji = False
        
        for char in text:
            # 检查是否为emoji字符（简单判断：Unicode范围）
            char_code = ord(char)
            char_is_emoji = (
                0x1F600 <= char_code <= 0x1F64F or  # 表情符号
                0x1F300 <= char_code <= 0x1F5FF or  # 杂项符号
                0x1F680 <= char_code <= 0x1F6FF or  # 交通和地图符号
                0x1F700 <= char_code <= 0x1F77F or  # 炼金术符号
                0x1F780 <= char_code <= 0x1F7FF or  # 几何形状扩展
                0x1F800 <= char_code <= 0x1F8FF or  # 补充箭头-C
                0x2600 <= char_code <= 0x26FF or   # 杂项符号
                0x2700 <= char_code <= 0x27BF or   # 装饰符号
                0xFE00 <= char_code <= 0xFE0F or   # 变体选择器
                0x1F900 <= char_code <= 0x1F9FF     # 补充符号和象形文字
            )
            
            if char_is_emoji != is_emoji:
                if current_part:
                    parts.append((current_part, is_emoji))
                current_part = char
                is_emoji = char_is_emoji
            else:
                current_part += char
        
        if current_part:
            parts.append((current_part, is_emoji))
        
        # 如果没有分离出不同类型的文字，直接使用普通字体
        if len(parts) == 1 and not parts[0][1]:
            part_text = parts[0][0]
            # 检查是否为不可见字符（如变体选择器）
            if not part_text or part_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in part_text):
                return pygame.Surface((1, 20), pygame.SRCALPHA)  # 默认高度
            return text_font.render(text, True, color)
        
        # 渲染各部分并组合
        surfaces = []
        total_width = 0
        max_height = 0
        
        for part_text, part_is_emoji in parts:
            # 跳过空的段落或不可见字符（如变体选择器）
            if not part_text or part_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in part_text):
                continue
            if part_is_emoji:
                surface = emoji_font.render(part_text, True, color)
            else:
                surface = text_font.render(part_text, True, color)
            surfaces.append(surface)
            total_width += surface.get_width()
            max_height = max(max_height, surface.get_height())
        
        # 创建组合Surface
        combined_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        x_offset = 0
        
        for surface in surfaces:
            y_offset = (max_height - surface.get_height()) // 2
            combined_surface.blit(surface, (x_offset, y_offset))
            x_offset += surface.get_width()
        
        return combined_surface
    
    def _initialize_pygame(self):
        """初始化pygame组件"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 720))
        pygame.display.set_caption(f"多怪物战斗 - {self.scenario['name']}")
        self.clock = pygame.time.Clock()
        
        # 初始化字体 - 分别为文字和emoji使用不同字体
        try:
            # 文字字体
            self.font = pygame.font.Font('font/msyh.ttc', 20)
            self.small_font = pygame.font.Font('font/msyh.ttc', 14)
            self.title_font = pygame.font.Font('font/msyh.ttc', 24)
            
            # emoji字体
            self.emoji_font = pygame.font.Font('font/seguiemj.ttf', 20)
            self.emoji_small_font = pygame.font.Font('font/seguiemj.ttf', 14)
            self.emoji_title_font = pygame.font.Font('font/seguiemj.ttf', 24)
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 备用字体
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 14)
            self.title_font = pygame.font.SysFont('Arial', 24)
            self.emoji_font = pygame.font.SysFont('Arial', 20)
            self.emoji_small_font = pygame.font.SysFont('Arial', 14)
            self.emoji_title_font = pygame.font.SysFont('Arial', 24)
    
    def run(self) -> Dict:
        """运行战斗界面主循环"""
        # 如果设置了自动开始战斗，则在主循环开始前启动自动战斗
        if self.auto_start_battle and self.battle.battle_active:
            self._start_auto_battle()
        
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(Config.FPS)
        
        return self.battle_result or {'status': 'cancelled'}
    
    def _handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.battle_result = {'status': 'cancelled'}
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_strategy_result:
                        self._close_strategy_result()
                    elif self.show_target_selection:
                        self.show_target_selection = False
                        self.selected_skill = None
                    else:
                        self.running = False
                        self.battle_result = {'status': 'cancelled'}
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 滚轮向上
                    self._handle_scroll_up(event.pos)
                elif event.button == 5:  # 滚轮向下
                    self._handle_scroll_down(event.pos)
                else:
                    self._handle_mouse_click(event.pos)
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """处理鼠标点击"""
        if not self.battle.battle_active:
            return
        
        if self.show_target_selection:
            # 目标选择模式
            if self.confirm_button.collidepoint(pos) and self.selected_target is not None:
                self._execute_attack()
            elif self.cancel_button.collidepoint(pos):
                self.show_target_selection = False
                self.selected_skill = None
                self.selected_target = None
            else:
                # 检查怪物按钮
                for monster_id, rect in self.monster_buttons.items():
                    if rect.collidepoint(pos):
                        # 检查怪物是否存活
                        monster_state = next((m for m in self.battle.get_battle_state()['monsters'] 
                                            if m['id'] == monster_id and m['alive']), None)
                        if monster_state:
                            self.selected_target = monster_id
                            break
        else:
            # 技能选择模式
            for skill_name, rect in self.skill_buttons.items():
                if rect.collidepoint(pos):
                    available_skills = self.battle.get_available_skills()
                    if available_skills.get(skill_name, False):
                        skill_info = Config.SKILLS[skill_name]
                        if 'damage' in skill_info:
                            # 攻击技能需要选择目标
                            self.selected_skill = skill_name
                            self.selected_target = None
                            self.show_target_selection = True
                        else:
                            # 非攻击技能直接执行
                            self._execute_skill(skill_name)
                    break
            
            # 检查策略优化按钮
            if self.strategy_button.collidepoint(pos):
                self._show_strategy_optimization()
            
            # 检查自动战斗按钮
            if self.auto_battle_button.collidepoint(pos):
                if not self.auto_battle_active:
                    self._start_auto_battle()
            

    
    def _execute_skill(self, skill_name: str, target_id: Optional[int] = None):
        """执行技能"""
        result = self.battle.execute_player_turn(skill_name, target_id)
        
        if result['success']:
            # 检查战斗状态
            battle_result = self.battle.get_battle_result()
            if battle_result['status'] != 'ongoing':
                self.battle_result = battle_result
                # 延迟2秒后关闭
                pygame.time.wait(2000)
                self.running = False
        
        # 重置选择状态
        self.selected_skill = None
        self.selected_target = None
        self.show_target_selection = False
    
    def _execute_attack(self):
        """执行攻击"""
        if self.selected_skill and self.selected_target is not None:
            self._execute_skill(self.selected_skill, self.selected_target)
    
    def _show_strategy_optimization(self):
        """显示BOSS战策略优化"""
        if not self.battle.battle_active:
            return
        
        # 获取当前战斗状态
        battle_state = self.battle.get_battle_state()
        alive_monsters = [m for m in battle_state['monsters'] if m['alive']]
        if not alive_monsters:
            return
        
        # 准备怪物信息
        monsters_info = []
        for monster in alive_monsters:
            monsters_info.append({
                'id': monster['id'],
                'name': monster['name'],
                'hp': monster['current_hp'],
                'max_hp': monster['max_hp']
            })
        
        player_resources = battle_state['player_resources']
        
        # 创建多目标战斗策略并寻找最优策略
        strategy_result = self._find_multi_target_strategy(monsters_info, player_resources)
        
        # 保存结果
        self.optimal_strategy = strategy_result['sequence']
        self.strategy_stats = strategy_result['stats']
        self.monster_targets = strategy_result.get('targets', {})
        self.show_strategy_result = True
    
    def _close_strategy_result(self):
        """关闭策略结果显示"""
        self.show_strategy_result = False
        self.optimal_strategy = None
        self.strategy_stats = None
        self.monster_targets = {}
        self.scroll_offset = 0
        self.max_scroll_offset = 0
    

    

    
    def _reinitialize_battle(self):
        """重新初始化战斗系统以应用新配置"""
        # 使用动态初始化逻辑重新创建战斗系统
        self._initialize_battle_from_current_config()
        
        # 强制刷新UI
        self._render()
        pygame.display.flip()
        # 重置UI状态
        self.show_target_selection = False
        self.selected_skill = None
        self.selected_target = None
        self.show_strategy_result = False
        self.optimal_strategy = None
        self.strategy_stats = None
        self.monster_targets = {}
        
        # 重置所有滚动状态
        self.skill_scroll_offset = 0
        self.skill_max_scroll_offset = 0
        self.monster_scroll_offset = 0
        self.monster_max_scroll_offset = 0
        self.scroll_offset = 0
        self.max_scroll_offset = 0
    
    def _handle_scroll_up(self, mouse_pos: Tuple[int, int]):
        """处理向上滚动"""
        if self.show_strategy_result:
            self.scroll_offset = max(0, self.scroll_offset - 30)
        elif self.skill_area.collidepoint(mouse_pos):
            # 技能区域滚动
            self.skill_scroll_offset = max(0, self.skill_scroll_offset - 30)
        elif self.monsters_area.collidepoint(mouse_pos):
            # 怪物区域滚动
            self.monster_scroll_offset = max(0, self.monster_scroll_offset - 30)
        elif self.player_area.collidepoint(mouse_pos):
            # 玩家区域滚动
            self.player_scroll_offset = max(0, self.player_scroll_offset - 30)
    
    def _handle_scroll_down(self, mouse_pos: Tuple[int, int]):
        """处理向下滚动"""
        if self.show_strategy_result:
            self.scroll_offset = min(self.max_scroll_offset, self.scroll_offset + 30)
        elif self.skill_area.collidepoint(mouse_pos):
            # 技能区域滚动
            self.skill_scroll_offset = min(self.skill_max_scroll_offset, self.skill_scroll_offset + 30)
        elif self.monsters_area.collidepoint(mouse_pos):
            # 怪物区域滚动
            self.monster_scroll_offset = min(self.monster_max_scroll_offset, self.monster_scroll_offset + 30)
        elif self.player_area.collidepoint(mouse_pos):
            # 玩家区域滚动
            self.player_scroll_offset = min(self.player_max_scroll_offset, self.player_scroll_offset + 30)
    
    def _find_multi_target_strategy(self, monsters_info: List[Dict], player_resources: int) -> Dict:
        """寻找Boss战斗策略"""
        # 导入BossStrategy
        from ..algorithms.boss_strategy import BossStrategy
        
        # 提取所有怪物的血量列表
        boss_hps = [monster['hp'] for monster in monsters_info]
        monster_names = [monster['name'] for monster in monsters_info]
        
        if len(monsters_info) > 1:
            strategy_description = f"针对多个目标的最优策略: {', '.join([f'{name}({hp}HP)' for name, hp in zip(monster_names, boss_hps)])}"
        else:
            strategy_description = f"针对 {monster_names[0]} (血量: {boss_hps[0]}) 的最优策略"
        
        # 使用BossStrategy算法（支持多Boss）
        strategy_optimizer = BossStrategy(
            boss_hps=boss_hps,
            player_resources=player_resources
        )
        
        # 寻找最优策略
        result = strategy_optimizer.find_optimal_strategy(max_rounds=25)
        if len(result) == 4:
            optimal_sequence, optimal_rounds, stats, best_targets = result
        else:
            # 向后兼容
            optimal_sequence, optimal_rounds, stats = result
            best_targets = None
        
        # 转换结果格式
        strategy_sequence = optimal_sequence if optimal_sequence else []
        target_assignments = {}
        
        if optimal_sequence:
            # 模拟技能序列执行，验证策略
            # 如果算法返回了目标序列，使用它；否则让模拟函数自动生成
            simulation = strategy_optimizer.simulate_battle(optimal_sequence, best_targets)
            
            if simulation['success']:
                # 为每个技能分配目标（基于算法返回的目标序列）
                for i, skill_name in enumerate(optimal_sequence):
                    if skill_name in Config.SKILLS and i < len(simulation['battle_log']):
                        skill_info = Config.SKILLS[skill_name]
                        damage = skill_info.get('damage', 0)
                        log_entry = simulation['battle_log'][i]
                        target_idx = log_entry.get('target_idx', -1)
                        
                        if damage > 0 and target_idx >= 0 and target_idx < len(monsters_info):
                            # 攻击技能
                            remaining_hp = log_entry['boss_hps'][target_idx] if 'boss_hps' in log_entry else 0
                            target_assignments[i] = {
                                'monster_id': target_idx,
                                'monster_name': monsters_info[target_idx]['name'],
                                'damage': damage,
                                'remaining_hp': remaining_hp
                            }
                        else:
                            # 非攻击技能
                            target_assignments[i] = {
                                'monster_id': -1,
                                'monster_name': '自身',
                                'damage': 0,
                                'remaining_hp': 'N/A'
                            }
        
        # 计算成功率
        success = optimal_sequence is not None and len(optimal_sequence) > 0
        
        # 合并统计信息
        final_stats = {
            'explored_states': stats.get('explored_states', 0),
            'pruned_states': stats.get('pruned_states', 0),
            'max_depth': stats.get('max_depth', 0),
            'computation_time': stats.get('computation_time', 0.0),
            'optimal_rounds': optimal_rounds,
            'success': success,
            'total_damage': sum(Config.SKILLS[skill].get('damage', 0) for skill in strategy_sequence if skill in Config.SKILLS),
            'average_damage_per_round': sum(Config.SKILLS[skill].get('damage', 0) for skill in strategy_sequence if skill in Config.SKILLS) / max(1, len(strategy_sequence)) if strategy_sequence else 0,
            'algorithm': 'BossStrategy'
        }
        
        return {
            'sequence': strategy_sequence if success else None,
            'targets': target_assignments,
            'stats': final_stats,
            'strategy_description': strategy_description if success else "未找到有效策略"
        }
    
    def _select_best_skill(self, target_hp: int, available_resources: int = None) -> Optional[str]:
        """选择最适合的技能（不考虑资源消耗）"""
        best_skill = None
        best_damage = 0
        
        for skill_name, skill_info in Config.SKILLS.items():
            damage = skill_info.get('damage', 0)
            
            # 跳过无伤害技能
            if damage == 0:
                continue
            
            # 如果能一击击败目标，优先选择伤害最高的
            if damage >= target_hp:
                if best_skill is None or damage > Config.SKILLS[best_skill].get('damage', 0):
                    best_skill = skill_name
                    best_damage = damage
            # 否则选择伤害最高的技能
            elif damage > best_damage:
                best_skill = skill_name
                best_damage = damage
        
        return best_skill
    
    def _start_auto_battle(self):
        """启动自动战斗"""
        if not self.battle.battle_active or self.auto_battle_active:
            return
        
        # 获取最优策略
        battle_state = self.battle.get_battle_state()
        alive_monsters = [m for m in battle_state['monsters'] if m['alive']]
        if not alive_monsters:
            return
        
        # 准备怪物信息
        monsters_info = []
        for monster in alive_monsters:
            monsters_info.append({
                'id': monster['id'],
                'name': monster['name'],
                'hp': monster['current_hp'],
                'max_hp': monster['max_hp']
            })
        
        player_resources = battle_state['player_resources']
        
        # 获取最优策略
        strategy_result = self._find_multi_target_strategy(monsters_info, player_resources)
        
        if strategy_result['sequence']:
            self.auto_battle_active = True
            self.auto_battle_sequence = strategy_result['sequence']
            self.auto_battle_targets = strategy_result.get('targets', {})
            self.auto_battle_step = 0
            self.auto_battle_last_time = pygame.time.get_ticks()
            
            # 关闭其他界面
            self.show_target_selection = False
            self.show_strategy_result = False
            self.selected_skill = None
            self.selected_target = None
    
    def _stop_auto_battle(self):
        """停止自动战斗"""
        self.auto_battle_active = False
        self.auto_battle_sequence = []
        self.auto_battle_targets = {}
        self.auto_battle_step = 0
        self.auto_battle_timer = 0
    
    def _update(self):
        """更新游戏状态"""
        if self.auto_battle_active:
            self._update_auto_battle()
    
    def _update_auto_battle(self):
        """更新自动战斗状态"""
        current_time = pygame.time.get_ticks()
        
        # 检查是否到了执行下一步的时间
        if current_time - self.auto_battle_last_time >= self.auto_battle_delay:
            if self.auto_battle_step < len(self.auto_battle_sequence):
                # 执行当前步骤
                skill_name = self.auto_battle_sequence[self.auto_battle_step]
                target_id = None
                
                # 获取目标ID
                if self.auto_battle_step in self.auto_battle_targets:
                    target_info = self.auto_battle_targets[self.auto_battle_step]
                    target_id = target_info.get('monster_id')
                    if target_id == -1:  # 非攻击技能
                        target_id = None
                
                # 执行技能
                result = self.battle.execute_player_turn(skill_name, target_id)
                
                if result['success']:
                    # 每回合资源值减一
                    current_state = self.battle.get_battle_state()
                    if current_state['player_resources'] > 0:
                        # 直接修改战斗系统中的玩家资源
                        self.battle.player_resources = max(0, self.battle.player_resources - 1)
                    
                    # 检查战斗状态
                    battle_result = self.battle.get_battle_result()
                    if battle_result['status'] != 'ongoing':
                        self.battle_result = battle_result
                        self._stop_auto_battle()
                        # 延迟2秒后关闭
                        pygame.time.wait(2000)
                        self.running = False
                        return
                    
                    # 进入下一步
                    self.auto_battle_step += 1
                    self.auto_battle_last_time = current_time
                else:
                    # 执行失败，停止自动战斗
                    self._stop_auto_battle()
            else:
                # 序列执行完毕，停止自动战斗
                self._stop_auto_battle()
    
    def _render(self):
        """渲染界面"""
        # 使用深色背景
        self.screen.fill(Config.COLORS['DARK_GRAY'])
        
        # 标题阴影
        title_shadow = self._render_mixed_text(f"⚔️ 多怪物战斗 - {self.scenario['name']}", 'title', Config.COLORS['SHADOW'])
        self.screen.blit(title_shadow, (22, 12))
        title_text = self._render_mixed_text(f"⚔️ 多怪物战斗 - {self.scenario['name']}", 'title', Config.COLORS['PRIMARY'])
        self.screen.blit(title_text, (20, 10))
        
        # 渲染各个区域
        self._render_log_area()
        self._render_skill_area()
        self._render_player_area()
        self._render_monsters_area()
        
        if self.show_target_selection:
            self._render_target_selection()
        
        # 渲染策略优化按钮
        self._render_strategy_button()
        
        # 渲染自动战斗按钮
        self._render_auto_battle_button()
        
        if self.show_strategy_result:
            self._render_strategy_result()
        
        pygame.display.flip()
    
    def _render_log_area(self):
        """渲染日志区域"""
        # 绘制阴影
        shadow_rect = pygame.Rect(self.log_area.x + 3, self.log_area.y + 3, self.log_area.width, self.log_area.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        # 绘制主体背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], self.log_area)
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], self.log_area, 2)
        
        # 标题栏
        title_rect = pygame.Rect(self.log_area.x, self.log_area.y, self.log_area.width, 25)
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], title_rect)
        
        # 标题文字
        log_title = self._render_mixed_text("📜 战斗日志", 'normal', Config.COLORS['WHITE'])
        title_text_rect = log_title.get_rect(center=(title_rect.centerx, title_rect.centery))
        self.screen.blit(log_title, title_text_rect)
        
        # 日志内容
        battle_state = self.battle.get_battle_state()
        logs = battle_state['battle_log']
        
        y_offset = 35
        for i, log in enumerate(logs[-7:]):  # 显示最近7条日志
            if y_offset + 20 > self.log_area.height:
                break
            # 交替背景色
            if i % 2 == 0:
                log_bg = pygame.Rect(self.log_area.x + 2, self.log_area.y + y_offset - 2, self.log_area.width - 4, 18)
                pygame.draw.rect(self.screen, Config.COLORS['DARK_GRAY'], log_bg)
            
            log_text = self._render_mixed_text(log, 'small', Config.COLORS['WHITE'])
            self.screen.blit(log_text, (self.log_area.x + 8, self.log_area.y + y_offset))
            y_offset += 20
    
    def _render_skill_area(self):
        """渲染技能区域"""
        # 绘制阴影
        shadow_rect = pygame.Rect(self.skill_area.x + 3, self.skill_area.y + 3, self.skill_area.width, self.skill_area.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        # 绘制主体背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], self.skill_area)
        pygame.draw.rect(self.screen, Config.COLORS['WARNING'], self.skill_area, 2)
        
        # 标题栏
        title_rect = pygame.Rect(self.skill_area.x, self.skill_area.y, self.skill_area.width, 25)
        pygame.draw.rect(self.screen, Config.COLORS['WARNING'], title_rect)
        
        # 标题文字
        skill_title = self._render_mixed_text("⚡ 技能面板", 'normal', Config.COLORS['WHITE'])
        title_text_rect = skill_title.get_rect(center=(title_rect.centerx, title_rect.centery))
        self.screen.blit(skill_title, title_text_rect)
        
        # 创建可滚动内容区域
        content_area = pygame.Rect(self.skill_area.x, self.skill_area.y + 25, self.skill_area.width - 15, self.skill_area.height - 25)
        
        # 计算总内容高度
        skill_count = len(Config.SKILLS)
        total_content_height = skill_count * 37 + 50  # 技能按钮 + 配置按钮
        
        # 更新滚动范围
        self.skill_max_scroll_offset = max(0, total_content_height - content_area.height)
        self.skill_scroll_offset = min(self.skill_scroll_offset, self.skill_max_scroll_offset)
        
        # 设置裁剪区域
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], content_area)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(content_area)
        
        # 技能按钮
        available_skills = self.battle.get_available_skills()
        self.skill_buttons.clear()
        
        y_offset = 35 - self.skill_scroll_offset
        for skill_name, skill_info in Config.SKILLS.items():
            button_rect = pygame.Rect(
                self.skill_area.x + 10,
                self.skill_area.y + y_offset,
                280, 32
            )
            self.skill_buttons[skill_name] = button_rect
            
            # 按钮阴影
            shadow_button = pygame.Rect(button_rect.x + 2, button_rect.y + 2, button_rect.width, button_rect.height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_button)
            
            # 按钮颜色和状态
            if available_skills.get(skill_name, False):
                if self.selected_skill == skill_name:
                    color = Config.COLORS['ACCENT']
                    border_color = Config.COLORS['PRIMARY']
                    text_color = Config.COLORS['WHITE']
                else:
                    color = Config.COLORS['SUCCESS']
                    border_color = Config.COLORS['SUCCESS']
                    text_color = Config.COLORS['WHITE']
            else:
                color = Config.COLORS['DARK_GRAY']
                border_color = Config.COLORS['DANGER']
                text_color = Config.COLORS['GRAY']
            
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, border_color, button_rect, 2)
            
            # 技能图标和文本
            skill_icons = {'普通攻击': '⚔️', '强力攻击': '💥', '治疗': '💚', '防御': '🛡️'}
            icon = skill_icons.get(skill_info['name'], '⚡')
            skill_text = f"{icon} {skill_info['name']} (CD: {skill_info.get('cooldown', 0)})"
            text_surface = self._render_mixed_text(skill_text, 'small', text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)
            
            y_offset += 37
        

        
        # 恢复裁剪区域
        self.screen.set_clip(old_clip)
        
        # 绘制滚动条（如果需要）
        if self.skill_max_scroll_offset > 0:
            scrollbar_x = self.skill_area.x + self.skill_area.width - 12
            scrollbar_y = self.skill_area.y + 25
            scrollbar_height = self.skill_area.height - 25
            
            # 滚动条背景
            scrollbar_bg = pygame.Rect(scrollbar_x, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], scrollbar_bg)
            
            # 滚动条滑块
            thumb_height = max(20, int(scrollbar_height * content_area.height / total_content_height))
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * self.skill_scroll_offset / self.skill_max_scroll_offset)
            thumb_rect = pygame.Rect(scrollbar_x + 1, thumb_y, 8, thumb_height)
            pygame.draw.rect(self.screen, Config.COLORS['WARNING'], thumb_rect)
    
    def _render_player_area(self):
        """渲染玩家区域"""
        # 绘制阴影
        shadow_rect = pygame.Rect(self.player_area.x + 3, self.player_area.y + 3, self.player_area.width, self.player_area.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        # 绘制主体背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], self.player_area)
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], self.player_area, 2)
        
        battle_state = self.battle.get_battle_state()
        
        # 标题栏
        title_rect = pygame.Rect(self.player_area.x, self.player_area.y, self.player_area.width, 25)
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], title_rect)
        
        # 玩家信息标题
        player_title = self._render_mixed_text("🚶 玩家状态", 'normal', Config.COLORS['WHITE'])
        title_text_rect = player_title.get_rect(center=(title_rect.centerx, title_rect.centery))
        self.screen.blit(player_title, title_text_rect)
        
        # 创建可滚动内容区域
        content_area = pygame.Rect(self.player_area.x, self.player_area.y + 25, self.player_area.width - 15, self.player_area.height - 25)
        
        # 计算总内容高度
        base_content_height = 50  # 基础信息高度
        auto_battle_height = 0
        if self.auto_battle_active:
            auto_battle_height = 105  # 自动战斗信息高度
        total_content_height = base_content_height + auto_battle_height
        
        # 更新滚动范围
        self.player_max_scroll_offset = max(0, total_content_height - content_area.height)
        self.player_scroll_offset = min(self.player_scroll_offset, self.player_max_scroll_offset)
        
        # 设置裁剪区域
        old_clip = self.screen.get_clip()
        self.screen.set_clip(content_area)
        
        # 计算滚动偏移后的Y位置
        y_offset = 35 - self.player_scroll_offset
        
        # 资源信息
        resource_text = f"💰 资源: {battle_state['player_resources']}"
        resource_surface = self._render_mixed_text(resource_text, 'small', Config.COLORS['GOLD'])
        self.screen.blit(resource_surface, (self.player_area.x + 15, self.player_area.y + y_offset))
        
        turn_text = f"🔄 回合: {battle_state['turn_count']}"
        turn_surface = self._render_mixed_text(turn_text, 'small', Config.COLORS['INFO'])
        self.screen.blit(turn_surface, (self.player_area.x + 15, self.player_area.y + y_offset + 20))
        

        
        # 自动战斗状态信息
        if self.auto_battle_active:
            y_pos = self.player_area.y + y_offset + 45
            
            # 自动战斗标题
            auto_title = self._render_mixed_text("⚡ 自动战斗中...", 'small', Config.COLORS['ACCENT'])
            self.screen.blit(auto_title, (self.player_area.x + 15, y_pos))
            y_pos += 25
            
            # 当前步骤信息
            if self.auto_battle_sequence and self.auto_battle_step < len(self.auto_battle_sequence):
                current_skill = self.auto_battle_sequence[self.auto_battle_step]
                current_target = self.auto_battle_targets[self.auto_battle_step] if self.auto_battle_step < len(self.auto_battle_targets) else None
                
                # 当前技能
                skill_text = f"🎯 技能: {current_skill}"
                skill_surface = self._render_mixed_text(skill_text, 'small', Config.COLORS['INFO'])
                self.screen.blit(skill_surface, (self.player_area.x + 15, y_pos))
                y_pos += 20
                
                # 目标信息
                if current_target is not None:
                    target_text = f"👹 目标: 怪物 #{current_target['monster_id']} ({current_target['monster_name']})"
                    target_surface = self._render_mixed_text(target_text, 'small', Config.COLORS['WARNING'])
                    self.screen.blit(target_surface, (self.player_area.x + 15, y_pos))
                    y_pos += 20
                
                # 进度信息
                progress_text = f"📊 进度: {self.auto_battle_step + 1}/{len(self.auto_battle_sequence)}"
                progress_surface = self._render_mixed_text(progress_text, 'small', Config.COLORS['SUCCESS'])
                self.screen.blit(progress_surface, (self.player_area.x + 15, y_pos))
                y_pos += 20
                
                # 资源消耗提示
                cost_text = "💰 每回合消耗: -1 资源"
                cost_surface = self._render_mixed_text(cost_text, 'small', Config.COLORS['DANGER'])
                self.screen.blit(cost_surface, (self.player_area.x + 15, y_pos))
        
        # 恢复裁剪区域
        self.screen.set_clip(old_clip)
        
        # 绘制滚动条（如果需要）
        if self.player_max_scroll_offset > 0:
            scrollbar_x = self.player_area.x + self.player_area.width - 12
            scrollbar_y = self.player_area.y + 25
            scrollbar_height = self.player_area.height - 25
            
            # 滚动条背景
            scrollbar_bg = pygame.Rect(scrollbar_x, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], scrollbar_bg)
            
            # 滚动条滑块
            thumb_height = max(20, int(scrollbar_height * content_area.height / total_content_height))
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * self.player_scroll_offset / self.player_max_scroll_offset)
            thumb_rect = pygame.Rect(scrollbar_x + 1, thumb_y, 8, thumb_height)
            pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], thumb_rect)
    
    def _render_monsters_area(self):
        """渲染怪物区域"""
        # 绘制阴影
        shadow_rect = pygame.Rect(self.monsters_area.x + 3, self.monsters_area.y + 3, self.monsters_area.width, self.monsters_area.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        # 绘制主体背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], self.monsters_area)
        pygame.draw.rect(self.screen, Config.COLORS['DANGER'], self.monsters_area, 2)
        
        # 标题栏
        title_rect = pygame.Rect(self.monsters_area.x, self.monsters_area.y, self.monsters_area.width, 25)
        pygame.draw.rect(self.screen, Config.COLORS['DANGER'], title_rect)
        
        # 标题
        monster_title = self._render_mixed_text("👹 敌方单位", 'normal', Config.COLORS['WHITE'])
        title_text_rect = monster_title.get_rect(center=(title_rect.centerx, title_rect.centery))
        self.screen.blit(monster_title, title_text_rect)
        
        # 创建可滚动内容区域
        content_area = pygame.Rect(self.monsters_area.x, self.monsters_area.y + 25, self.monsters_area.width - 15, self.monsters_area.height - 25)
        
        # 怪物列表
        battle_state = self.battle.get_battle_state()
        monsters = battle_state['monsters']
        self.monster_buttons.clear()
        
        # 计算总内容高度
        monster_card_height = 65
        total_content_height = len(monsters) * monster_card_height
        
        # 更新滚动范围
        self.monster_max_scroll_offset = max(0, total_content_height - content_area.height)
        self.monster_scroll_offset = min(self.monster_scroll_offset, self.monster_max_scroll_offset)
        
        # 设置裁剪区域
        old_clip = self.screen.get_clip()
        self.screen.set_clip(content_area)
        
        y_offset = 35 - self.monster_scroll_offset
        for monster in monsters:
            monster_rect = pygame.Rect(
                self.monsters_area.x + 10,
                self.monsters_area.y + y_offset,
                330, 55
            )
            
            # 怪物卡片阴影
            card_shadow = pygame.Rect(monster_rect.x + 2, monster_rect.y + 2, monster_rect.width, monster_rect.height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], card_shadow)
            
            if monster['alive']:
                self.monster_buttons[monster['id']] = monster_rect
                
                # 怪物背景色
                if self.show_target_selection and self.selected_target == monster['id']:
                    bg_color = Config.COLORS['ACCENT']
                    border_color = Config.COLORS['PRIMARY']
                elif monster['alive']:
                    bg_color = Config.COLORS['DARK_RED']
                    border_color = Config.COLORS['DANGER']
                else:
                    bg_color = Config.COLORS['DARK_GRAY']
                    border_color = Config.COLORS['GRAY']
            else:
                bg_color = Config.COLORS['DARK_GRAY']
                border_color = Config.COLORS['GRAY']
            
            pygame.draw.rect(self.screen, bg_color, monster_rect)
            pygame.draw.rect(self.screen, border_color, monster_rect, 2)
            
            # 怪物图标和信息
            monster_icons = {'哥布林': '👺', '兽人': '👹', '巨魔': '🧌', '骷髅': '💀', '恶魔': '😈'}
            icon = monster_icons.get(monster['name'], '👹')
            
            # 怪物名称和图标
            name_text = f"{icon} {monster['name']} #{monster['id']}"
            name_surface = self._render_mixed_text(name_text, 'small', Config.COLORS['WHITE'])
            self.screen.blit(name_surface, (monster_rect.x + 8, monster_rect.y + 5))
            
            # HP信息
            hp_text = f"❤️ {monster['current_hp']}/{monster['max_hp']}"
            hp_surface = self._render_mixed_text(hp_text, 'small', Config.COLORS['WHITE'])
            self.screen.blit(hp_surface, (monster_rect.x + 8, monster_rect.y + 22))
            
            # 现代化血量条
            hp_bar_rect = pygame.Rect(monster_rect.x + 8, monster_rect.y + 40, 200, 12)
            # 血量条阴影
            hp_bar_shadow = pygame.Rect(hp_bar_rect.x + 1, hp_bar_rect.y + 1, hp_bar_rect.width, hp_bar_rect.height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], hp_bar_shadow)
            
            # 血量条背景
            pygame.draw.rect(self.screen, Config.COLORS['DARK_GRAY'], hp_bar_rect)
            
            if monster['max_hp'] > 0:
                hp_fill_width = int(hp_bar_rect.width * monster['hp_percentage'])
                if hp_fill_width > 0:
                    hp_fill_rect = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, hp_fill_width, hp_bar_rect.height)
                    # 根据血量百分比选择颜色
                    if monster['hp_percentage'] > 0.6:
                        hp_color = Config.COLORS['SUCCESS']
                    elif monster['hp_percentage'] > 0.3:
                        hp_color = Config.COLORS['WARNING']
                    else:
                        hp_color = Config.COLORS['DANGER']
                    pygame.draw.rect(self.screen, hp_color, hp_fill_rect)
            
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], hp_bar_rect, 1)
            
            # 状态标识
            if monster['alive']:
                status_text = "🟢 存活"
                status_color = Config.COLORS['SUCCESS']
            else:
                status_text = "💀 已死亡"
                status_color = Config.COLORS['DANGER']
            
            status_surface = self._render_mixed_text(status_text, 'small', status_color)
            self.screen.blit(status_surface, (monster_rect.x + 240, monster_rect.y + 22))
            
            y_offset += 65
        
        # 恢复裁剪区域
        self.screen.set_clip(old_clip)
        
        # 绘制滚动条（如果需要）
        if self.monster_max_scroll_offset > 0:
            scrollbar_x = self.monsters_area.x + self.monsters_area.width - 12
            scrollbar_y = self.monsters_area.y + 25
            scrollbar_height = self.monsters_area.height - 25
            
            # 滚动条背景
            scrollbar_bg = pygame.Rect(scrollbar_x, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], scrollbar_bg)
            
            # 滚动条滑块
            thumb_height = max(20, int(scrollbar_height * content_area.height / total_content_height))
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * self.monster_scroll_offset / self.monster_max_scroll_offset)
            thumb_rect = pygame.Rect(scrollbar_x + 1, thumb_y, 8, thumb_height)
            pygame.draw.rect(self.screen, Config.COLORS['DANGER'], thumb_rect)
    
    def _render_target_selection(self):
        """渲染目标选择区域"""
        # 绘制阴影
        shadow_rect = pygame.Rect(self.target_selection_area.x + 3, self.target_selection_area.y + 3, 
                                self.target_selection_area.width, self.target_selection_area.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        # 主体背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], self.target_selection_area)
        pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], self.target_selection_area, 3)
        
        # 标题栏
        title_rect = pygame.Rect(self.target_selection_area.x, self.target_selection_area.y, 
                               self.target_selection_area.width, 25)
        pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], title_rect)
        
        # 标题
        skill_name = Config.SKILLS[self.selected_skill]['name']
        title_text = self._render_mixed_text(f"🎯 选择目标 - {skill_name}", 'normal', Config.COLORS['WHITE'])
        title_text_rect = title_text.get_rect(center=(title_rect.centerx, title_rect.centery))
        self.screen.blit(title_text, title_text_rect)
        
        # 提示文本
        hint_text = "💡 点击上方怪物选择目标，然后点击确认"
        hint_surface = self._render_mixed_text(hint_text, 'small', Config.COLORS['INFO'])
        self.screen.blit(hint_surface, (self.target_selection_area.x + 15, self.target_selection_area.y + 35))
        
        # 选中的目标信息
        if self.selected_target is not None:
            battle_state = self.battle.get_battle_state()
            target_monster = next((m for m in battle_state['monsters'] if m['id'] == self.selected_target), None)
            if target_monster:
                target_text = f"✅ 已选中: {target_monster['name']} (❤️ {target_monster['current_hp']}/{target_monster['max_hp']})"
                target_surface = self._render_mixed_text(target_text, 'small', Config.COLORS['SUCCESS'])
                self.screen.blit(target_surface, (self.target_selection_area.x + 15, self.target_selection_area.y + 55))
        
        # 现代化按钮
        # 确认按钮阴影
        confirm_shadow = pygame.Rect(self.confirm_button.x + 2, self.confirm_button.y + 2, 
                                   self.confirm_button.width, self.confirm_button.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], confirm_shadow)
        
        # 确认按钮
        if self.selected_target is not None:
            confirm_color = Config.COLORS['SUCCESS']
            confirm_border = Config.COLORS['SUCCESS']
            confirm_text_color = Config.COLORS['WHITE']
        else:
            confirm_color = Config.COLORS['DARK_GRAY']
            confirm_border = Config.COLORS['GRAY']
            confirm_text_color = Config.COLORS['GRAY']
            
        pygame.draw.rect(self.screen, confirm_color, self.confirm_button)
        pygame.draw.rect(self.screen, confirm_border, self.confirm_button, 2)
        confirm_text = self._render_mixed_text("✅ 确认", 'small', confirm_text_color)
        confirm_rect = confirm_text.get_rect(center=self.confirm_button.center)
        self.screen.blit(confirm_text, confirm_rect)
        
        # 取消按钮阴影
        cancel_shadow = pygame.Rect(self.cancel_button.x + 2, self.cancel_button.y + 2, 
                                  self.cancel_button.width, self.cancel_button.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], cancel_shadow)
        
        # 取消按钮
        pygame.draw.rect(self.screen, Config.COLORS['DANGER'], self.cancel_button)
        pygame.draw.rect(self.screen, Config.COLORS['DANGER'], self.cancel_button, 2)
        cancel_text = self._render_mixed_text("❌ 取消", 'small', Config.COLORS['WHITE'])
        cancel_rect = cancel_text.get_rect(center=self.cancel_button.center)
        self.screen.blit(cancel_text, cancel_rect)
    
    def _render_strategy_button(self):
        """渲染策略优化按钮"""
        if not self.battle.battle_active or self.show_target_selection or self.show_strategy_result or self.auto_battle_active:
            return
        
        # 按钮阴影
        shadow_button = pygame.Rect(self.strategy_button.x + 2, self.strategy_button.y + 2, 
                                   self.strategy_button.width, self.strategy_button.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_button)
        
        # 按钮背景
        pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], self.strategy_button)
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], self.strategy_button, 2)
        
        # 按钮文字
        button_text = self._render_mixed_text("🧠 BOSS战策略优化", 'small', Config.COLORS['WHITE'])
        text_rect = button_text.get_rect(center=self.strategy_button.center)
        self.screen.blit(button_text, text_rect)
    
    def _render_auto_battle_button(self):
        """渲染自动战斗按钮"""
        if not self.battle.battle_active or self.show_target_selection or self.show_strategy_result or self.auto_battle_active:
            return
        
        # 按钮阴影
        shadow_button = pygame.Rect(self.auto_battle_button.x + 2, self.auto_battle_button.y + 2, 
                                   self.auto_battle_button.width, self.auto_battle_button.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_button)
        
        # 按钮颜色和文字
        button_color = Config.COLORS['SUCCESS']
        border_color = Config.COLORS['SUCCESS']
        button_text_content = "⚡ 自动战斗"
        
        # 按钮背景
        pygame.draw.rect(self.screen, button_color, self.auto_battle_button)
        pygame.draw.rect(self.screen, border_color, self.auto_battle_button, 2)
        
        # 按钮文字
        button_text = self._render_mixed_text(button_text_content, 'small', Config.COLORS['WHITE'])
        text_rect = button_text.get_rect(center=self.auto_battle_button.center)
        self.screen.blit(button_text, text_rect)
    
    def _render_strategy_result(self):
        """渲染策略优化结果"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((800, 720))
        overlay.set_alpha(180)
        overlay.fill(Config.COLORS['BLACK'])
        self.screen.blit(overlay, (0, 0))
        
        # 结果窗口
        result_rect = pygame.Rect(100, 100, 600, 520)
        
        # 窗口阴影
        shadow_rect = pygame.Rect(result_rect.x + 4, result_rect.y + 4,
                                 result_rect.width, result_rect.height)
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], shadow_rect)
        
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], result_rect)
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], result_rect, 3)
        
        # 创建可滚动内容区域
        content_rect = pygame.Rect(result_rect.x + 10, result_rect.y + 60, result_rect.width - 20, result_rect.height - 100)
        
        # 标题栏背景
        title_bar = pygame.Rect(result_rect.x, result_rect.y, result_rect.width, 40)
        pygame.draw.rect(self.screen, Config.COLORS['SUCCESS'], title_bar)
        
        # 标题
        title_text = self._render_mixed_text("🎯 BOSS战策略优化结果", 'title', Config.COLORS['WHITE'])
        title_rect = title_text.get_rect(center=(title_bar.centerx, title_bar.centery))
        self.screen.blit(title_text, title_rect)
        
        # 创建内容表面用于滚动
        content_surface = pygame.Surface((content_rect.width, 2000))  # 足够大的表面
        content_surface.fill(Config.COLORS['BLUE'])
        
        y_offset = 10  # 在内容表面上的偏移
        
        if self.optimal_strategy:
            # 最优策略信息
            strategy_title = self._render_mixed_text(f"最优技能序列 (共{len(self.optimal_strategy)}回合):", 'normal', Config.COLORS['YELLOW'])
            content_surface.blit(strategy_title, (10, y_offset))
            y_offset += 40
            
            # 技能序列
            for i, skill_name in enumerate(self.optimal_strategy):
                skill_info = Config.SKILLS[skill_name]
                
                # 基本技能信息
                skill_text = f"{i+1}. {skill_info['name']} (伤害: {skill_info.get('damage', 0)}, 冷却: {skill_info.get('cooldown', 0)}回合)"
                skill_surface = self._render_mixed_text(skill_text, 'small', Config.COLORS['WHITE'])
                content_surface.blit(skill_surface, (30, y_offset))
                y_offset += 20
                
                # 目标信息
                if i in self.monster_targets:
                    target_info = self.monster_targets[i]
                    target_text = f"   → 攻击目标: {target_info['monster_name']} (ID: {target_info['monster_id']}) 剩余血量: {target_info['remaining_hp']}"
                    target_surface = self._render_mixed_text(target_text, 'small', Config.COLORS['YELLOW'])
                    content_surface.blit(target_surface, (30, y_offset))
                    y_offset += 20
                else:
                    y_offset += 5
        else:
            # 无解情况
            no_solution_text = self._render_mixed_text("在当前条件下无法找到可行的策略", 'normal', Config.COLORS['RED'])
            content_surface.blit(no_solution_text, (10, y_offset))
            y_offset += 40
        
        # 统计信息
        if self.strategy_stats:
            y_offset += 20
            stats_title = self._render_mixed_text("算法统计信息:", 'normal', Config.COLORS['YELLOW'])
            content_surface.blit(stats_title, (10, y_offset))
            y_offset += 30
            
            stats_info = [
                f"探索节点数: {self.strategy_stats.get('explored_states', self.strategy_stats.get('nodes_explored', 0))}",
                f"剪枝节点数: {self.strategy_stats.get('pruned_states', self.strategy_stats.get('nodes_pruned', 0))}",
                f"最大深度: {self.strategy_stats.get('max_depth', 0)}",
                f"计算时间: {self.strategy_stats.get('computation_time', 0.0):.3f}秒",
                f"最优回合数: {self.strategy_stats['optimal_rounds']}",
                f"策略成功: {'是' if self.strategy_stats.get('success', False) else '否'}",
                f"算法类型: {self.strategy_stats.get('algorithm', 'Unknown')}"
            ]
            
            # 添加击败顺序信息
            if self.strategy_stats.get('defeated_order'):
                defeated_order = self.strategy_stats['defeated_order']
                order_text = f"击败顺序: {[f'目标{id+1}' for id in defeated_order]}"
                stats_info.append(order_text)
                
                order_score = self.strategy_stats.get('order_score', 0)
                score_text = f"顺序评分: {order_score:.1f}"
                stats_info.append(score_text)
            
            for stat in stats_info:
                stat_surface = self._render_mixed_text(stat, 'small', Config.COLORS['WHITE'])
                content_surface.blit(stat_surface, (30, y_offset))
                y_offset += 25
        
        # 计算最大滚动偏移量
        content_height = y_offset + 50  # 添加一些底部边距
        self.max_scroll_offset = max(0, content_height - content_rect.height)
        
        # 限制滚动偏移量
        self.scroll_offset = min(self.scroll_offset, self.max_scroll_offset)
        
        # 绘制可滚动内容
        visible_area = pygame.Rect(0, self.scroll_offset, content_rect.width, content_rect.height)
        self.screen.blit(content_surface, content_rect, visible_area)
        
        # 绘制滚动条（如果需要）
        if self.max_scroll_offset > 0:
            scrollbar_rect = pygame.Rect(result_rect.x + result_rect.width - 15, content_rect.y, 10, content_rect.height)
            # 滚动条背景
            pygame.draw.rect(self.screen, Config.COLORS['DARK_GRAY'], scrollbar_rect)
            pygame.draw.rect(self.screen, Config.COLORS['GRAY'], scrollbar_rect, 1)
            
            # 滚动条滑块
            thumb_height = max(20, int(content_rect.height * content_rect.height / content_height))
            thumb_y = content_rect.y + int(self.scroll_offset * (content_rect.height - thumb_height) / self.max_scroll_offset)
            thumb_rect = pygame.Rect(scrollbar_rect.x + 1, thumb_y, scrollbar_rect.width - 2, thumb_height)
            pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], thumb_rect)
            pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], thumb_rect, 1)
        
        # 关闭提示背景
        hint_bg = pygame.Rect(result_rect.x, result_rect.y + result_rect.height - 35,
                             result_rect.width, 35)
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], hint_bg)
        
        # 关闭提示和滚动提示（固定位置）
        if self.max_scroll_offset > 0:
            hint_text = self._render_mixed_text("⌨️ 按ESC关闭 | 🖱️ 滚轮滚动", 'small', Config.COLORS['WHITE'])
        else:
            hint_text = self._render_mixed_text("⌨️ 按ESC键关闭", 'small', Config.COLORS['WHITE'])
        hint_rect = hint_text.get_rect(center=(hint_bg.centerx, hint_bg.centery))
        self.screen.blit(hint_text, hint_rect)