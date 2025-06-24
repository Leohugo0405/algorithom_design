#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss战斗UI界面模块
提供可视化的战斗界面和交互
"""

import pygame
import sys
from typing import Dict, List, Tuple, Optional
from src.config import Config
from src.game_engine import GameEngine

class BattleUI:
    """
    Boss战斗用户界面类
    """
    
    def __init__(self, game_engine: GameEngine, boss_data: Dict):
        """
        初始化战斗UI
        """
        self.game_engine = game_engine
        self.boss_data = boss_data
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # 战斗状态
        self.running = True
        self.battle_result = None
        self.player_turn = True
        
        # 战斗动画
        self.animations = [] # 动画队列
        self.battle_log = ["战斗开始！"]
        
        # UI元素
        self.player_area = pygame.Rect(100, 250, 200, 200)
        self.boss_area = pygame.Rect(500, 200, 200, 200)
        self.skill_buttons = {}
        self.control_area = pygame.Rect(50, 520, 700, 200)
        self.show_optimal_btn = True
        self.optimal_btn_rect = pygame.Rect(600, 480, 180, 40)

        self._initialize_pygame()

    def _initialize_pygame(self):
        """
        初始化pygame组件
        """
        self.screen = pygame.display.set_mode((800, 750))
        pygame.display.set_caption("Boss战斗 - " + Config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        try:
            self.font = pygame.font.Font('font/msyh.ttc', 24)
            self.small_font = pygame.font.Font('font/msyh.ttc', 16)
            self.title_font = pygame.font.Font('font/msyh.ttc', 32)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.small_font = pygame.font.SysFont('Arial', 16)
            self.title_font = pygame.font.SysFont('Arial', 32)

    def run(self) -> Dict:
        """
        运行战斗界面主循环
        """
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(Config.FPS)
        
        return self.battle_result or {'success': False, 'message': '战斗被取消'}

    def _handle_events(self):
        """
        处理事件
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.battle_result = {'success': False, 'message': '战斗被取消'}
            
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_optimal_btn and self.optimal_btn_rect.collidepoint(event.pos):
                    self._show_optimal_strategy()
                elif self.player_turn:
                    self._handle_mouse_click(event.pos)

            elif event.type == pygame.USEREVENT: # Boss行动定时器
                self._handle_boss_turn()
                pygame.time.set_timer(pygame.USEREVENT, 0) # 关闭定时器

    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """
        处理鼠标点击技能按钮
        """
        if not self.player_turn:
            return

        for skill_name, rect in self.skill_buttons.items():
            if rect.collidepoint(pos):
                battle_state = self.game_engine.get_battle_state()
                if battle_state['available_skills'].get(skill_name):
                    self.player_turn = False
                    self._execute_turn(skill_name)
                    break
    
    def _execute_turn(self, skill_name: str):
        """
        执行一个战斗回合
        """
        result = self.game_engine.execute_battle_turn(skill_name)
        
        if not result['success']:
            self.add_log(result['message'])
            self.player_turn = True
            return

        # 玩家动画和日志
        player_action = result['player_action']
        skill_config = Config.SKILLS[player_action['skill']]
        self.add_log(f"你使用了 '{skill_config['name']}'!")
        if player_action['damage'] > 0:
            self.add_animation('player_attack', self.boss_area.center, f"-{player_action['damage']}")
            self.add_log(f"对Boss造成了 {player_action['damage']}点伤害。")
        if player_action['heal'] > 0:
            self.add_animation('heal', self.player_area.center, f"+{player_action['heal']}")
            self.add_log(f"你恢复了 {player_action['heal']}点生命值。")

        # 存储回合结果，以便Boss回合使用
        self.last_turn_result = result

        # 检查战斗状态，如果玩家获胜则直接结束
        if result['status'] == 'victory':
            self._check_battle_status(result['status'], result)
        else:
            # 延迟1秒后Boss行动
            pygame.time.set_timer(pygame.USEREVENT, 1000)

    def _handle_boss_turn(self):
        """
        处理Boss的回合，播放动画和日志
        """
        result = self.last_turn_result
        if not result or result['status'] != 'ongoing':
            return
            
        boss_action = result['boss_action']
        self.add_log("Boss攻击了你！")
        if boss_action['damage'] > 0:
            self.add_animation('boss_attack', self.player_area.center, f"-{boss_action['damage']}")
            self.add_log(f"你受到了 {boss_action['damage']}点伤害。")

        self._check_battle_status(result['status'], result)

    def _update(self):
        """
        更新动画状态
        """
        for anim in self.animations[:]:
            anim['timer'] -= 1
            if anim['timer'] <= 0:
                self.animations.remove(anim)

    def _check_battle_status(self, status: str, result: Dict):
        """
        检查战斗是否结束
        """
        if status == 'victory':
            self.add_log(f"战斗胜利！获得{result['reward']}资源奖励。")
            self.battle_result = result
            pygame.time.wait(2000)
            self.running = False
        elif status == 'defeat':
            self.add_log("战斗失败！")
            self.battle_result = result
            pygame.time.wait(2000)
            self.running = False
        else:
            self.player_turn = True

    def _render(self):
        """
        渲染所有战斗界面元素
        """
        self.screen.fill(Config.COLORS['BLACK'])
        self._render_battle_info()
        self._render_battle_area()
        self._render_control_panel()
        self._render_log_panel()
        self._render_animations()
        pygame.display.flip()

    def _render_battle_info(self):
        """
        渲染战斗信息
        """
        battle_state = self.game_engine.get_battle_state()
        if not battle_state: return

        title_text = self.title_font.render("Boss 激战", True, Config.COLORS['WHITE'])
        self.screen.blit(title_text, title_text.get_rect(center=(400, 30)))
        
        turn_text_str = "你的回合" if self.player_turn else "Boss回合"
        turn_text = self.font.render(turn_text_str, True, Config.COLORS['YELLOW'])
        self.screen.blit(turn_text, (650, 20))
        
    def _render_battle_area(self):
        """
        渲染战斗区域，包括玩家和Boss
        """
        # ... (reuse existing rendering for player and boss icons)
        self._render_character("⚔️", self.player_area)
        self._render_character("👹", self.boss_area)

        battle_state = self.game_engine.get_battle_state()
        if not battle_state: return
        
        self._render_hp_bar(battle_state['player_hp'], self.game_engine.active_battle['initial_player_hp'], self.player_area, Config.COLORS['GREEN'])
        self._render_resource_bar(battle_state['player_resources'], self.player_area)
        self._render_hp_bar(battle_state['boss_hp'], self.game_engine.active_battle['initial_boss_hp'], self.boss_area, Config.COLORS['RED'])
    
    def _render_character(self, icon: str, area: pygame.Rect):
        char_icon = self.font.render(icon, True, Config.COLORS['WHITE'])
        self.screen.blit(char_icon, char_icon.get_rect(center=area.center))

    def _render_hp_bar(self, current: int, total: int, area: pygame.Rect, color: Tuple):
        if total == 0: return
        ratio = current / total
        bar_rect = pygame.Rect(area.left, area.bottom + 5, area.width, 20)
        current_bar_rect = pygame.Rect(area.left, area.bottom + 5, int(area.width * ratio), 20)
        
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], bar_rect)
        pygame.draw.rect(self.screen, color, current_bar_rect)
        
        hp_text = self.small_font.render(f"HP: {current}/{total}", True, Config.COLORS['WHITE'])
        self.screen.blit(hp_text, hp_text.get_rect(center=bar_rect.center))

    def _render_resource_bar(self, current: int, area: pygame.Rect):
        # Placeholder for resource bar
        resource_text = self.small_font.render(f"资源: {current}", True, Config.COLORS['GOLD'])
        self.screen.blit(resource_text, (area.left, area.bottom + 30))

    def _render_control_panel(self):
        """
        渲染技能控制面板
        """
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], self.control_area, border_radius=5)
        
        battle_state = self.game_engine.get_battle_state()
        if not battle_state: return

        x_offset = 70
        self.skill_buttons.clear()
        
        for skill_name, props in Config.SKILLS.items():
            is_available = battle_state['available_skills'].get(skill_name, False)
            
            btn_rect = pygame.Rect(x_offset, 550, 150, 60)
            self.skill_buttons[skill_name] = btn_rect
            
            color = Config.COLORS['BLUE'] if is_available and self.player_turn else Config.COLORS['DARK_GREEN']
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], btn_rect, 2, border_radius=5)
            
            name_text = self.small_font.render(props['name'], True, Config.COLORS['WHITE'])
            self.screen.blit(name_text, (btn_rect.centerx - name_text.get_width() // 2, btn_rect.top + 5))
            
            cost_text = self.small_font.render(f"消耗: {props['cost']}", True, Config.COLORS['GOLD'])
            self.screen.blit(cost_text, (btn_rect.centerx - cost_text.get_width() // 2, btn_rect.top + 25))
            
            cooldown = battle_state['skill_cooldowns'].get(skill_name, 0)
            if cooldown > 0:
                cooldown_text = self.small_font.render(f"冷却: {cooldown}", True, Config.COLORS['RED'])
                self.screen.blit(cooldown_text, (btn_rect.centerx - cooldown_text.get_width() // 2, btn_rect.top + 45))

            x_offset += 170

        # 最优策略按钮
        if self.show_optimal_btn:
            pygame.draw.rect(self.screen, Config.COLORS['GREEN'], self.optimal_btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.optimal_btn_rect, 2, border_radius=5)
            btn_text = self.small_font.render("最优策略演示", True, Config.COLORS['WHITE'])
            self.screen.blit(btn_text, (self.optimal_btn_rect.centerx - btn_text.get_width() // 2, self.optimal_btn_rect.centery - btn_text.get_height() // 2))

    def _render_log_panel(self):
        """
        渲染战斗日志
        """
        log_area = pygame.Rect(50, 630, 700, 110)
        pygame.draw.rect(self.screen, (20, 20, 20), log_area, border_radius=5)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], log_area, 1, border_radius=5)

        y_offset = log_area.top + 5
        for log_entry in self.battle_log[-4:]:
             log_text = self.small_font.render(f"> {log_entry}", True, Config.COLORS['WHITE'])
             self.screen.blit(log_text, (log_area.left + 10, y_offset))
             y_offset += 25

    def _render_animations(self):
        """
        渲染战斗动画
        """
        for anim in self.animations:
            if anim['type'] in ['player_attack', 'boss_attack']:
                color = Config.COLORS['RED']
            elif anim['type'] == 'heal':
                color = Config.COLORS['GREEN']
            
            alpha = int(255 * (anim['timer'] / 60)) # Fade out effect
            text = self.font.render(anim['text'], True, color)
            text.set_alpha(alpha)
            
            pos = (anim['pos'][0], anim['pos'][1] - (60 - anim['timer'])) # Move up
            self.screen.blit(text, text.get_rect(center=pos))

    def add_animation(self, anim_type: str, pos: Tuple, text: str):
        """
        添加一个动画到队列
        """
        self.animations.append({'type': anim_type, 'pos': pos, 'text': text, 'timer': 60})

    def add_log(self, message: str):
        """
        添加一条日志
        """
        self.battle_log.append(message)
        if len(self.battle_log) > 20:
            self.battle_log.pop(0)

    def _show_optimal_strategy(self):
        from src.algorithms.boss_strategy import BossStrategy
        # 获取当前boss和玩家资源
        boss_hp = self.game_engine.get_battle_state()['boss_hp']
        player_resources = self.game_engine.get_battle_state()['player_resources']
        boss_strategy = BossStrategy(boss_hp=boss_hp, player_resources=player_resources)
        optimal_sequence, rounds_needed, stats = boss_strategy.find_optimal_strategy()
        if optimal_sequence:
            print("\n【分支限界法BOSS最优策略】")
            print(f"最小回合数: {rounds_needed}")
            print(f"技能序列: {optimal_sequence}")
            self.add_log(f"最优策略已输出到终端！")
        else:
            print("未找到可行的最优策略！")
            self.add_log("未找到可行的最优策略！") 