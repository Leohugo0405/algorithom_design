#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多怪物战斗UI界面模块
提供可视化的多怪物战斗界面和目标选择交互
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional
from ..config import Config
from ..battle.multi_monster_battle import MultiMonsterBattle
from ..algorithms.boss_strategy import BossStrategy

class MultiMonsterBattleUI:
    """
    多怪物战斗用户界面类
    """
    
    def __init__(self, scenario_name: str = 'medium'):
        """
        初始化多怪物战斗UI
        
        Args:
            scenario_name: 战斗场景名称
        """
        self.scenario_name = scenario_name
        self.scenario = Config.MULTI_BATTLE_SCENARIOS[scenario_name]
        
        # 创建怪物配置
        monster_configs = []
        for monster_type in self.scenario['monsters']:
            monster_config = Config.MONSTER_TYPES[monster_type].copy()
            monster_configs.append(monster_config)
        
        self.battle = MultiMonsterBattle(monster_configs)
        
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
        
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """初始化pygame组件"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 720))
        pygame.display.set_caption(f"多怪物战斗 - {self.scenario['name']}")
        self.clock = pygame.time.Clock()
        
        try:
            self.font = pygame.font.Font('font/msyh.ttc', 20)
            self.small_font = pygame.font.Font('font/msyh.ttc', 14)
            self.title_font = pygame.font.Font('font/msyh.ttc', 24)
        except:
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 14)
            self.title_font = pygame.font.SysFont('Arial', 24)
    
    def run(self) -> Dict:
        """运行战斗界面主循环"""
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
    
    def _find_multi_target_strategy(self, monsters_info: List[Dict], player_resources: int) -> Dict:
        """寻找多目标战斗策略"""
        # 按血量从低到高排序怪物（优先击败血量少的）
        sorted_monsters = sorted(monsters_info, key=lambda m: m['hp'])
        
        strategy_sequence = []
        target_assignments = {}
        total_damage_needed = sum(m['hp'] for m in monsters_info)
        current_resources = player_resources
        
        # 统计信息
        nodes_explored = 0
        
        # 贪心策略：优先使用高效技能击败血量最少的怪物（不消耗资源）
        remaining_monsters = sorted_monsters.copy()
        step = 0
        
        while remaining_monsters and step < 20:
            step += 1
            nodes_explored += 1
            
            # 选择当前血量最少的怪物作为目标
            target_monster = remaining_monsters[0]
            
            # 选择最适合的技能（不考虑资源）
            best_skill = self._select_best_skill(target_monster['hp'])
            if not best_skill:
                break
            
            skill_info = Config.SKILLS[best_skill]
            damage = skill_info.get('damage', 0)
            
            # 记录技能和目标
            strategy_sequence.append(best_skill)
            target_assignments[len(strategy_sequence) - 1] = {
                'monster_id': target_monster['id'],
                'monster_name': target_monster['name'],
                'damage': damage,
                'remaining_hp': max(0, target_monster['hp'] - damage)
            }
            
            # 更新状态（不消耗资源）
            target_monster['hp'] -= damage
            
            # 如果怪物被击败，从列表中移除
            if target_monster['hp'] <= 0:
                remaining_monsters.remove(target_monster)
            else:
                # 重新排序（血量可能发生变化）
                remaining_monsters.sort(key=lambda m: m['hp'])
        
        # 计算成功率
        success = len(remaining_monsters) == 0
        
        stats = {
            'nodes_explored': nodes_explored,
            'nodes_pruned': 0,
            'states_cached': len(monsters_info),
            'optimal_rounds': len(strategy_sequence),
            'success': success,
            'remaining_monsters': len(remaining_monsters)
        }
        
        return {
            'sequence': strategy_sequence if success else None,
            'targets': target_assignments,
            'stats': stats
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
    
    def _update(self):
        """更新游戏状态"""
        pass
    
    def _render(self):
        """渲染界面"""
        self.screen.fill(Config.COLORS['BLACK'])
        
        # 渲染标题
        title_text = self.title_font.render(f"多怪物战斗 - {self.scenario['name']}", True, Config.COLORS['WHITE'])
        self.screen.blit(title_text, (10, 10))
        
        # 渲染各个区域
        self._render_log_area()
        self._render_skill_area()
        self._render_player_area()
        self._render_monsters_area()
        
        if self.show_target_selection:
            self._render_target_selection()
        
        # 渲染策略优化按钮
        self._render_strategy_button()
        
        if self.show_strategy_result:
            self._render_strategy_result()
        
        pygame.display.flip()
    
    def _render_log_area(self):
        """渲染日志区域"""
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], self.log_area, 2)
        
        # 标题
        log_title = self.font.render("战斗日志", True, Config.COLORS['WHITE'])
        self.screen.blit(log_title, (self.log_area.x + 5, self.log_area.y + 5))
        
        # 日志内容
        battle_state = self.battle.get_battle_state()
        logs = battle_state['battle_log']
        
        y_offset = 30
        for log in logs[-8:]:  # 显示最近8条日志
            if y_offset + 20 > self.log_area.height:
                break
            log_text = self.small_font.render(log, True, Config.COLORS['WHITE'])
            self.screen.blit(log_text, (self.log_area.x + 5, self.log_area.y + y_offset))
            y_offset += 20
    
    def _render_skill_area(self):
        """渲染技能区域"""
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], self.skill_area, 2)
        
        # 标题
        skill_title = self.font.render("技能", True, Config.COLORS['WHITE'])
        self.screen.blit(skill_title, (self.skill_area.x + 5, self.skill_area.y + 5))
        
        # 技能按钮
        available_skills = self.battle.get_available_skills()
        self.skill_buttons.clear()
        
        y_offset = 30
        for skill_name, skill_info in Config.SKILLS.items():
            button_rect = pygame.Rect(
                self.skill_area.x + 10,
                self.skill_area.y + y_offset,
                280, 35
            )
            self.skill_buttons[skill_name] = button_rect
            
            # 按钮颜色
            if available_skills.get(skill_name, False):
                if self.selected_skill == skill_name:
                    color = Config.COLORS['YELLOW']
                else:
                    color = Config.COLORS['GREEN']
            else:
                color = Config.COLORS['DARK_RED']
            
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], button_rect, 2)
            
            # 技能文本
            skill_text = f"{skill_info['name']} (冷却: {skill_info.get('cooldown', 0)}回合)"
            text_surface = self.small_font.render(skill_text, True, Config.COLORS['BLACK'])
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)
            
            y_offset += 40
    
    def _render_player_area(self):
        """渲染玩家区域"""
        pygame.draw.rect(self.screen, Config.COLORS['BLUE'], self.player_area, 2)
        
        battle_state = self.battle.get_battle_state()
        
        # 玩家信息
        player_title = self.font.render("玩家状态", True, Config.COLORS['WHITE'])
        self.screen.blit(player_title, (self.player_area.x + 5, self.player_area.y + 5))
        
        hp_text = f"生命值: {battle_state['player_hp']}/{battle_state['player_max_hp']}"
        hp_surface = self.small_font.render(hp_text, True, Config.COLORS['WHITE'])
        self.screen.blit(hp_surface, (self.player_area.x + 10, self.player_area.y + 35))
        
        resource_text = f"资源: {battle_state['player_resources']}"
        resource_surface = self.small_font.render(resource_text, True, Config.COLORS['WHITE'])
        self.screen.blit(resource_surface, (self.player_area.x + 10, self.player_area.y + 55))
        
        turn_text = f"回合: {battle_state['turn_count']}"
        turn_surface = self.small_font.render(turn_text, True, Config.COLORS['WHITE'])
        self.screen.blit(turn_surface, (self.player_area.x + 10, self.player_area.y + 75))
        
        # 生命值条
        hp_bar_rect = pygame.Rect(self.player_area.x + 10, self.player_area.y + 100, 200, 20)
        pygame.draw.rect(self.screen, Config.COLORS['RED'], hp_bar_rect)
        
        hp_percentage = battle_state['player_hp'] / battle_state['player_max_hp']
        hp_fill_width = int(hp_bar_rect.width * hp_percentage)
        hp_fill_rect = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, hp_fill_width, hp_bar_rect.height)
        pygame.draw.rect(self.screen, Config.COLORS['GREEN'], hp_fill_rect)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], hp_bar_rect, 2)
    
    def _render_monsters_area(self):
        """渲染怪物区域"""
        pygame.draw.rect(self.screen, Config.COLORS['RED'], self.monsters_area, 2)
        
        # 标题
        monster_title = self.font.render("怪物", True, Config.COLORS['WHITE'])
        self.screen.blit(monster_title, (self.monsters_area.x + 5, self.monsters_area.y + 5))
        
        # 怪物列表
        battle_state = self.battle.get_battle_state()
        monsters = battle_state['monsters']
        self.monster_buttons.clear()
        
        y_offset = 30
        for monster in monsters:
            monster_rect = pygame.Rect(
                self.monsters_area.x + 10,
                self.monsters_area.y + y_offset,
                330, 60
            )
            
            if monster['alive']:
                self.monster_buttons[monster['id']] = monster_rect
                
                # 怪物背景色
                if self.show_target_selection and self.selected_target == monster['id']:
                    bg_color = Config.COLORS['YELLOW']
                elif monster['alive']:
                    bg_color = Config.COLORS['DARK_RED']
                else:
                    bg_color = Config.COLORS['GRAY']
            else:
                bg_color = Config.COLORS['GRAY']
            
            pygame.draw.rect(self.screen, bg_color, monster_rect)
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], monster_rect, 2)
            
            # 怪物信息
            name_text = f"{monster['name']} (ID: {monster['id']})"
            name_surface = self.small_font.render(name_text, True, Config.COLORS['WHITE'])
            self.screen.blit(name_surface, (monster_rect.x + 5, monster_rect.y + 5))
            
            hp_text = f"HP: {monster['current_hp']}/{monster['max_hp']}"
            hp_surface = self.small_font.render(hp_text, True, Config.COLORS['WHITE'])
            self.screen.blit(hp_surface, (monster_rect.x + 5, monster_rect.y + 25))
            
            # 血量条
            hp_bar_rect = pygame.Rect(monster_rect.x + 5, monster_rect.y + 45, 200, 10)
            pygame.draw.rect(self.screen, Config.COLORS['RED'], hp_bar_rect)
            
            if monster['max_hp'] > 0:
                hp_fill_width = int(hp_bar_rect.width * monster['hp_percentage'])
                hp_fill_rect = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, hp_fill_width, hp_bar_rect.height)
                pygame.draw.rect(self.screen, Config.COLORS['GREEN'], hp_fill_rect)
            
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], hp_bar_rect, 1)
            
            # 状态文本
            status_text = "存活" if monster['alive'] else "已死亡"
            status_color = Config.COLORS['GREEN'] if monster['alive'] else Config.COLORS['RED']
            status_surface = self.small_font.render(status_text, True, status_color)
            self.screen.blit(status_surface, (monster_rect.x + 250, monster_rect.y + 25))
            
            y_offset += 70
    
    def _render_target_selection(self):
        """渲染目标选择区域"""
        pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], self.target_selection_area, 3)
        
        # 半透明背景
        overlay = pygame.Surface((self.target_selection_area.width, self.target_selection_area.height))
        overlay.set_alpha(200)
        overlay.fill(Config.COLORS['BLACK'])
        self.screen.blit(overlay, self.target_selection_area.topleft)
        
        # 标题
        title_text = self.font.render(f"选择攻击目标 - {Config.SKILLS[self.selected_skill]['name']}", True, Config.COLORS['WHITE'])
        self.screen.blit(title_text, (self.target_selection_area.x + 10, self.target_selection_area.y + 10))
        
        # 提示文本
        hint_text = "点击上方怪物选择目标，然后点击确认"
        hint_surface = self.small_font.render(hint_text, True, Config.COLORS['WHITE'])
        self.screen.blit(hint_surface, (self.target_selection_area.x + 10, self.target_selection_area.y + 40))
        
        # 选中的目标信息
        if self.selected_target is not None:
            battle_state = self.battle.get_battle_state()
            target_monster = next((m for m in battle_state['monsters'] if m['id'] == self.selected_target), None)
            if target_monster:
                target_text = f"选中目标: {target_monster['name']} (HP: {target_monster['current_hp']}/{target_monster['max_hp']})"
                target_surface = self.small_font.render(target_text, True, Config.COLORS['YELLOW'])
                self.screen.blit(target_surface, (self.target_selection_area.x + 10, self.target_selection_area.y + 65))
        
        # 按钮
        # 确认按钮
        confirm_color = Config.COLORS['GREEN'] if self.selected_target is not None else Config.COLORS['GRAY']
        pygame.draw.rect(self.screen, confirm_color, self.confirm_button)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.confirm_button, 2)
        confirm_text = self.small_font.render("确认", True, Config.COLORS['BLACK'])
        confirm_rect = confirm_text.get_rect(center=self.confirm_button.center)
        self.screen.blit(confirm_text, confirm_rect)
        
        # 取消按钮
        pygame.draw.rect(self.screen, Config.COLORS['RED'], self.cancel_button)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.cancel_button, 2)
        cancel_text = self.small_font.render("取消", True, Config.COLORS['WHITE'])
        cancel_rect = cancel_text.get_rect(center=self.cancel_button.center)
        self.screen.blit(cancel_text, cancel_rect)
    
    def _render_strategy_button(self):
        """渲染策略优化按钮"""
        if not self.battle.battle_active or self.show_target_selection or self.show_strategy_result:
            return
        
        # 按钮背景
        pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], self.strategy_button)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.strategy_button, 2)
        
        # 按钮文字
        button_text = self.small_font.render("BOSS战策略优化", True, Config.COLORS['WHITE'])
        text_rect = button_text.get_rect(center=self.strategy_button.center)
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
        pygame.draw.rect(self.screen, Config.COLORS['BLUE'], result_rect)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], result_rect, 3)
        
        # 标题
        title_text = self.title_font.render("BOSS战策略优化结果", True, Config.COLORS['WHITE'])
        self.screen.blit(title_text, (result_rect.x + 20, result_rect.y + 20))
        
        y_offset = 70
        
        if self.optimal_strategy:
            # 最优策略信息
            strategy_title = self.font.render(f"最优技能序列 (共{len(self.optimal_strategy)}回合):", True, Config.COLORS['YELLOW'])
            self.screen.blit(strategy_title, (result_rect.x + 20, result_rect.y + y_offset))
            y_offset += 40
            
            # 技能序列
            for i, skill_name in enumerate(self.optimal_strategy):
                skill_info = Config.SKILLS[skill_name]
                
                # 基本技能信息
                skill_text = f"{i+1}. {skill_info['name']} (伤害: {skill_info.get('damage', 0)}, 冷却: {skill_info.get('cooldown', 0)}回合)"
                skill_surface = self.small_font.render(skill_text, True, Config.COLORS['WHITE'])
                self.screen.blit(skill_surface, (result_rect.x + 40, result_rect.y + y_offset))
                y_offset += 20
                
                # 目标信息
                if i in self.monster_targets:
                    target_info = self.monster_targets[i]
                    target_text = f"   → 攻击目标: {target_info['monster_name']} (ID: {target_info['monster_id']}) 剩余血量: {target_info['remaining_hp']}"
                    target_surface = self.small_font.render(target_text, True, Config.COLORS['YELLOW'])
                    self.screen.blit(target_surface, (result_rect.x + 40, result_rect.y + y_offset))
                    y_offset += 20
                else:
                    y_offset += 5
                
                if y_offset > result_rect.height - 120:  # 防止超出窗口
                    break
        else:
            # 无解情况
            no_solution_text = self.font.render("在当前条件下无法找到可行的策略", True, Config.COLORS['RED'])
            self.screen.blit(no_solution_text, (result_rect.x + 20, result_rect.y + y_offset))
            y_offset += 40
        
        # 统计信息
        if self.strategy_stats:
            y_offset += 20
            stats_title = self.font.render("算法统计信息:", True, Config.COLORS['YELLOW'])
            self.screen.blit(stats_title, (result_rect.x + 20, result_rect.y + y_offset))
            y_offset += 30
            
            stats_info = [
                f"探索节点数: {self.strategy_stats['nodes_explored']}",
                f"剪枝节点数: {self.strategy_stats['nodes_pruned']}",
                f"缓存状态数: {self.strategy_stats['states_cached']}",
                f"最优回合数: {self.strategy_stats['optimal_rounds']}",
                f"策略成功: {'是' if self.strategy_stats.get('success', False) else '否'}",
                f"剩余怪物: {self.strategy_stats.get('remaining_monsters', 0)}只"
            ]
            
            for stat in stats_info:
                stat_surface = self.small_font.render(stat, True, Config.COLORS['WHITE'])
                self.screen.blit(stat_surface, (result_rect.x + 40, result_rect.y + y_offset))
                y_offset += 25
        
        # 关闭提示
        close_hint = self.small_font.render("按ESC键关闭", True, Config.COLORS['GRAY'])
        self.screen.blit(close_hint, (result_rect.x + result_rect.width - 120, result_rect.y + result_rect.height - 30))