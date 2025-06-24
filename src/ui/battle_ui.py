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
        
        Args:
            game_engine: 游戏引擎实例
            boss_data: Boss数据
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
        self.selected_strategy = 'optimal'  # 'optimal' 或 'random'
        
        # 战斗动画
        self.animation_frame = 0
        self.animation_speed = 5
        self.battle_log = []
        self.show_battle_log = False
        
        # UI元素位置
        self.battle_area = pygame.Rect(50, 100, 700, 400)
        self.player_area = pygame.Rect(100, 300, 200, 150)
        self.boss_area = pygame.Rect(500, 150, 200, 150)
        self.control_area = pygame.Rect(50, 520, 700, 200)
        
        # 初始化pygame
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """
        初始化pygame组件
        """
        # 创建战斗窗口
        self.screen = pygame.display.set_mode((800, 750))
        pygame.display.set_caption("Boss战斗 - " + Config.WINDOW_TITLE)
        
        # 创建时钟
        self.clock = pygame.time.Clock()
        
        # 初始化字体
        try:
            self.font = pygame.font.Font('font/msyh.ttc', 24)
            self.small_font = pygame.font.Font('font/msyh.ttc', 18)
            self.title_font = pygame.font.Font('font/msyh.ttc', 32)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.small_font = pygame.font.SysFont('Arial', 18)
            self.title_font = pygame.font.SysFont('Arial', 32)
    
    def run(self) -> Dict:
        """
        运行战斗界面
        
        Returns:
            Dict: 战斗结果
        """
        # 主战斗循环
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # 处理事件
            self._handle_events()
            
            # 更新动画
            if self.animation_frame > 0:
                self.animation_frame -= 1
            
            # 渲染战斗界面
            self._render()
            
            # 控制帧率
            self.clock.tick(Config.FPS)
        
        return self.battle_result or {'success': False, 'message': '战斗被取消'}
    
    def _handle_events(self):
        """
        处理pygame事件
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.battle_result = {'success': False, 'message': '战斗被取消'}
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.pos)
    
    def _handle_keydown(self, key):
        """
        处理键盘按下事件
        
        Args:
            key: 按下的键
        """
        if key == pygame.K_ESCAPE:
            self.running = False
            self.battle_result = {'success': False, 'message': '战斗被取消'}
        
        elif key == pygame.K_1:
            # 选择最优策略
            self.selected_strategy = 'optimal'
        
        elif key == pygame.K_2:
            # 选择随机策略
            self.selected_strategy = 'random'
        
        elif key == pygame.K_SPACE:
            # 开始战斗
            self._start_battle()
        
        elif key == pygame.K_l:
            # 切换战斗日志显示
            self.show_battle_log = not self.show_battle_log
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """
        处理鼠标点击事件
        
        Args:
            pos: 鼠标位置
        """
        # 检查策略选择按钮
        optimal_btn = pygame.Rect(100, 580, 150, 40)
        random_btn = pygame.Rect(270, 580, 150, 40)
        battle_btn = pygame.Rect(440, 580, 150, 40)
        
        if optimal_btn.collidepoint(pos):
            self.selected_strategy = 'optimal'
        elif random_btn.collidepoint(pos):
            self.selected_strategy = 'random'
        elif battle_btn.collidepoint(pos):
            self._start_battle()
    
    def _start_battle(self):
        """
        开始战斗
        
        Returns:
            Dict: 战斗结果
        """
        # 执行战斗
        result = self.game_engine.fight_boss(self.selected_strategy)
        
        if result['success']:
            # 战斗成功
            self.battle_log = result.get('battle_log', [])
            self.battle_result = result
            self.add_battle_message(f"战斗胜利！用时{result['rounds_used']}回合")
            self.add_battle_message(f"获得{result['reward']}资源奖励")
        else:
            # 战斗失败
            self.battle_result = result
            self.add_battle_message(f"战斗失败: {result['message']}")
        
        # 如果是AI模式，直接返回结果
        if hasattr(self, '_ai_mode') and self._ai_mode:
            return result
        
        # 延迟关闭窗口，让玩家看到结果
        pygame.time.wait(2000)
        self.running = False
        
        return result
    
    def _render(self):
        """
        渲染战斗界面
        """
        # 清空屏幕
        self.screen.fill(Config.COLORS['BLACK'])
        
        # 渲染标题
        self._render_title()
        
        # 渲染战斗区域
        self._render_battle_area()
        
        # 渲染控制面板
        self._render_control_panel()
        
        # 渲染战斗日志
        if self.show_battle_log:
            self._render_battle_log()
        
        # 更新显示
        pygame.display.flip()
    
    def _render_title(self):
        """
        渲染标题
        """
        title_text = self.title_font.render("Boss战斗", True, Config.COLORS['WHITE'])
        title_rect = title_text.get_rect(center=(400, 30))
        self.screen.blit(title_text, title_rect)
        
        # 显示Boss信息
        boss_info = f"Boss血量: {self.boss_data['boss_hp']}"
        boss_text = self.font.render(boss_info, True, Config.COLORS['RED'])
        self.screen.blit(boss_text, (50, 60))
        
        # 显示玩家信息
        game_state = self.game_engine.get_game_state()
        player_info = f"玩家资源: {game_state['player_resources']}"
        player_text = self.font.render(player_info, True, Config.COLORS['GREEN'])
        self.screen.blit(player_text, (300, 60))
    
    def _render_battle_area(self):
        """
        渲染战斗区域
        """
        # 绘制战斗区域背景
        pygame.draw.rect(self.screen, Config.COLORS['DARK_GREEN'], self.battle_area)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.battle_area, 3)
        
        # 渲染Boss
        self._render_boss()
        
        # 渲染玩家
        self._render_player()
        
        # 渲染战斗动画
        if self.animation_frame > 0:
            self._render_battle_animation()
    
    def _render_boss(self):
        """
        渲染Boss
        """
        # Boss图标
        boss_icon = self.font.render("👹", True, Config.COLORS['RED'])
        boss_rect = boss_icon.get_rect(center=self.boss_area.center)
        self.screen.blit(boss_icon, boss_rect)
        
        # Boss血量条
        boss_hp = self.boss_data['boss_hp']
        max_hp = Config.BOSS_HP
        hp_ratio = boss_hp / max_hp
        
        hp_bar_rect = pygame.Rect(self.boss_area.x, self.boss_area.bottom + 10, 
                                 self.boss_area.width, 20)
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], hp_bar_rect)
        
        current_hp_rect = pygame.Rect(self.boss_area.x, self.boss_area.bottom + 10,
                                     int(self.boss_area.width * hp_ratio), 20)
        pygame.draw.rect(self.screen, Config.COLORS['RED'], current_hp_rect)
        
        # 血量文字
        hp_text = self.small_font.render(f"{boss_hp}/{max_hp}", True, Config.COLORS['WHITE'])
        hp_text_rect = hp_text.get_rect(center=hp_bar_rect.center)
        self.screen.blit(hp_text, hp_text_rect)
    
    def _render_player(self):
        """
        渲染玩家
        """
        # 玩家图标
        player_icon = self.font.render("⚔️", True, Config.COLORS['BLUE'])
        player_rect = player_icon.get_rect(center=self.player_area.center)
        self.screen.blit(player_icon, player_rect)
        
        # 玩家资源条
        game_state = self.game_engine.get_game_state()
        resources = game_state['player_resources']
        max_resources = 100
        
        resource_bar_rect = pygame.Rect(self.player_area.x, self.player_area.bottom + 10,
                                       self.player_area.width, 20)
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], resource_bar_rect)
        
        current_resource_rect = pygame.Rect(self.player_area.x, self.player_area.bottom + 10,
                                           int(self.player_area.width * (resources / max_resources)), 20)
        pygame.draw.rect(self.screen, Config.COLORS['GOLD'], current_resource_rect)
        
        # 资源文字
        resource_text = self.small_font.render(f"{resources}/{max_resources}", True, Config.COLORS['WHITE'])
        resource_text_rect = resource_text.get_rect(center=resource_bar_rect.center)
        self.screen.blit(resource_text, resource_text_rect)
    
    def _render_battle_animation(self):
        """
        渲染战斗动画
        """
        # 简单的攻击动画
        if self.animation_frame > 0:
            # 绘制攻击效果
            attack_pos = (400, 250)
            attack_color = Config.COLORS['YELLOW']
            attack_size = 20 + (self.animation_frame * 2)
            
            pygame.draw.circle(self.screen, attack_color, attack_pos, attack_size)
            pygame.draw.circle(self.screen, Config.COLORS['ORANGE'], attack_pos, attack_size - 5)
    
    def _render_control_panel(self):
        """
        渲染控制面板
        """
        # 控制面板背景
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], self.control_area)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], self.control_area, 2)
        
        # 策略选择
        strategy_title = self.font.render("选择战斗策略:", True, Config.COLORS['WHITE'])
        self.screen.blit(strategy_title, (70, 540))
        
        # 最优策略按钮
        optimal_color = Config.COLORS['GREEN'] if self.selected_strategy == 'optimal' else Config.COLORS['DARK_GREEN']
        optimal_btn = pygame.Rect(100, 580, 150, 40)
        pygame.draw.rect(self.screen, optimal_color, optimal_btn)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], optimal_btn, 2)
        
        optimal_text = self.small_font.render("最优策略 (1)", True, Config.COLORS['WHITE'])
        optimal_text_rect = optimal_text.get_rect(center=optimal_btn.center)
        self.screen.blit(optimal_text, optimal_text_rect)
        
        # 随机策略按钮
        random_color = Config.COLORS['BLUE'] if self.selected_strategy == 'random' else Config.COLORS['DARK_GREEN']
        random_btn = pygame.Rect(270, 580, 150, 40)
        pygame.draw.rect(self.screen, random_color, random_btn)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], random_btn, 2)
        
        random_text = self.small_font.render("随机策略 (2)", True, Config.COLORS['WHITE'])
        random_text_rect = random_text.get_rect(center=random_btn.center)
        self.screen.blit(random_text, random_text_rect)
        
        # 开始战斗按钮
        battle_btn = pygame.Rect(440, 580, 150, 40)
        pygame.draw.rect(self.screen, Config.COLORS['RED'], battle_btn)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], battle_btn, 2)
        
        battle_text = self.small_font.render("开始战斗 (空格)", True, Config.COLORS['WHITE'])
        battle_text_rect = battle_text.get_rect(center=battle_btn.center)
        self.screen.blit(battle_text, battle_text_rect)
        
        # 其他控制提示
        controls_text = self.small_font.render("ESC: 退出战斗  L: 显示战斗日志", True, Config.COLORS['WHITE'])
        self.screen.blit(controls_text, (70, 640))
        
        # 策略说明
        if self.selected_strategy == 'optimal':
            desc_text = self.small_font.render("最优策略: 使用分支限界算法找到最佳战斗序列", True, Config.COLORS['YELLOW'])
        else:
            desc_text = self.small_font.render("随机策略: 生成多个随机策略并选择最佳方案", True, Config.COLORS['YELLOW'])
        
        self.screen.blit(desc_text, (70, 670))
    
    def _render_battle_log(self):
        """
        渲染战斗日志
        """
        if not self.battle_log:
            return
        
        # 日志面板背景
        log_panel = pygame.Rect(50, 50, 700, 600)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], log_panel)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], log_panel, 2)
        
        # 日志标题
        log_title = self.font.render("战斗日志", True, Config.COLORS['WHITE'])
        self.screen.blit(log_title, (70, 70))
        
        # 显示最近的战斗日志
        y_offset = 110
        for i, log_entry in enumerate(self.battle_log[-15:]):  # 显示最近15条
            if y_offset > 600:
                break
            
            log_text = self.small_font.render(log_entry, True, Config.COLORS['WHITE'])
            self.screen.blit(log_text, (70, y_offset))
            y_offset += 25
    
    def add_battle_message(self, message: str):
        """
        添加战斗消息
        
        Args:
            message: 消息内容
        """
        self.battle_log.append(message)
        if len(self.battle_log) > 50:  # 限制日志长度
            self.battle_log.pop(0) 