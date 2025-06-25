#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码锁解谜UI界面模块
提供可视化的解谜界面和交互
"""

import pygame
import sys
from typing import Dict, List, Tuple, Optional
from src.config import Config
from src.game_engine import GameEngine

class LockUI:
    def __init__(self, game_engine: GameEngine, lock_data: Dict):
        self.game_engine = game_engine
        self.lock_data = lock_data
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # 解谜状态
        self.running = True
        self.puzzle_solved = False
        self.current_input = []
        self.input_complete = False
        self.result_message = ""
        self.show_result = False
        self.result_start_time = 0  # 结果显示开始时间
        
        # UI元素
        self.input_boxes = []
        self.submit_button = None
        self.auto_solve_button = None
        self.number_buttons = []  # 数字按键
        self.clear_button = None  # 清除按钮
        
        # 在终端输出密码锁答案（调试用）
        correct_password = self.lock_data['puzzle']['password']
        print(f"密码锁答案: {''.join(map(str, correct_password))}")
        
        # 初始化pygame
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """
        初始化pygame组件
        """
        # 创建窗口
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("密码锁解谜")
        
        # 创建时钟
        self.clock = pygame.time.Clock()
        
        # 初始化字体
        try:
            self.title_font = pygame.font.Font('font/msyh.ttc', 32)
            self.font = pygame.font.Font('font/msyh.ttc', 20)
            self.small_font = pygame.font.Font('font/msyh.ttc', 16)
        except:
            self.title_font = pygame.font.SysFont('Arial', 32)
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
        
        # 初始化UI元素
        self._initialize_ui_elements()
    
    def _initialize_ui_elements(self):
        """
        初始化UI元素
        """
        # 输入框位置
        box_width = 60
        box_height = 60
        box_spacing = 20
        start_x = 400 - (Config.LOCK_DIGITS * box_width + (Config.LOCK_DIGITS - 1) * box_spacing) // 2
        start_y = 350
        
        self.input_boxes = []
        for i in range(Config.LOCK_DIGITS):
            x = start_x + i * (box_width + box_spacing)
            self.input_boxes.append(pygame.Rect(x, start_y, box_width, box_height))
        
        # 数字按键 (0-9)
        number_button_size = 50
        number_button_spacing = 10
        numbers_per_row = 5
        start_x = 400 - (numbers_per_row * number_button_size + (numbers_per_row - 1) * number_button_spacing) // 2
        start_y = 430
        
        self.number_buttons = []
        for i in range(10):
            row = i // numbers_per_row
            col = i % numbers_per_row
            x = start_x + col * (number_button_size + number_button_spacing)
            y = start_y + row * (number_button_size + number_button_spacing)
            self.number_buttons.append(pygame.Rect(x, y, number_button_size, number_button_size))
        
        # 功能按钮
        button_width = 100
        button_height = 35
        
        self.clear_button = pygame.Rect(320, 540, button_width, button_height)
        self.submit_button = pygame.Rect(430, 540, button_width, button_height)
        self.auto_solve_button = pygame.Rect(540, 540, button_width, button_height)
    
    def run(self) -> Dict:
        """
        运行解谜界面主循环
        
        Returns:
            Dict: 解谜结果
        """
        while self.running:
            # 处理事件
            self._handle_events()
            
            # 渲染界面
            self._render()
            
            # 控制帧率
            self.clock.tick(Config.FPS)
        
        # 返回解谜结果
        return {
            'success': self.puzzle_solved,
            'message': self.result_message
        }
    
    def _handle_events(self):
        """
        处理pygame事件
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.pos)
            
            elif event.type == pygame.USEREVENT + 1:
                # 定时器事件，用于成功解谜后自动退出
                self.running = False
        
        # 检查结果信息是否需要自动隐藏（1秒后）
        if self.show_result and not self.puzzle_solved:
            current_time = pygame.time.get_ticks()
            if current_time - self.result_start_time >= 1000:  # 1秒后隐藏
                self.show_result = False
    
    def _handle_keydown(self, key):
        """
        处理键盘按下事件（仅允许ESC和回车键）
        
        Args:
            key: 按下的键
        """
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_RETURN:
            self._submit_answer()
        
        # 禁用键盘数字输入和退格键，只能通过鼠标点击数字按键
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """
        处理鼠标点击事件
        
        Args:
            pos: 鼠标点击位置
        """
        # 检查数字按键点击
        for i, button in enumerate(self.number_buttons):
            if button.collidepoint(pos) and len(self.current_input) < Config.LOCK_DIGITS:
                self.current_input.append(i)
                return
        
        # 检查功能按钮点击
        if self.clear_button.collidepoint(pos):
            self.current_input = []
        
        elif self.submit_button.collidepoint(pos):
            self._submit_answer()
        
        elif self.auto_solve_button.collidepoint(pos):
            self._auto_solve()
    
    def _submit_answer(self):
        """
        提交玩家输入的答案
        """
        if len(self.current_input) != Config.LOCK_DIGITS:
            self.result_message = f"请输入{Config.LOCK_DIGITS}位数字！"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
            return
        
        # 检查答案是否正确
        correct_password = self.lock_data['puzzle']['password']
        if self.current_input == correct_password:
            self.puzzle_solved = True
            self.result_message = "密码正确！解锁成功！"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
            # 延迟2秒后退出
            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
        else:
            self.result_message = "密码错误，请重试！"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
            self.current_input = []
    
    def _auto_solve(self):
        """
        使用AI自动解谜
        """
        puzzle_data = self.lock_data['puzzle']
        solution, attempts = self.game_engine.puzzle_solver.solve_password_puzzle(puzzle_data['clues'])
        
        if solution:
            self.current_input = solution
            self.puzzle_solved = True
            self.result_message = f"AI解谜成功！密码是{''.join(map(str, solution))}，尝试了{attempts}次"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
            # 延迟3秒后退出
            pygame.time.set_timer(pygame.USEREVENT + 1, 3000)
        else:
            self.result_message = f"AI解谜失败，尝试了{attempts}次"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
    
    def _render(self):
        """
        渲染解谜界面
        """
        # 清空屏幕
        self.screen.fill(Config.COLORS['WHITE'])
        
        # 渲染标题
        self._render_title()
        
        # 渲染线索
        self._render_clues()
        
        # 渲染输入框
        self._render_input_boxes()
        
        # 渲染数字按键
        self._render_number_buttons()
        
        # 渲染功能按钮
        self._render_buttons()
        
        # 渲染结果消息
        if self.show_result:
            self._render_result_message()
        
        # 更新显示
        pygame.display.flip()
    
    def _render_title(self):
        """
        渲染标题
        """
        title_text = "密码锁解谜"
        title_surface = self.title_font.render(title_text, True, Config.COLORS['BLACK'])
        title_rect = title_surface.get_rect(center=(400, 80))
        self.screen.blit(title_surface, title_rect)
        
        # 渲染描述
        desc_text = self.lock_data['puzzle']['description']
        desc_surface = self.font.render(desc_text, True, Config.COLORS['GRAY'])
        desc_rect = desc_surface.get_rect(center=(400, 120))
        self.screen.blit(desc_surface, desc_rect)
    
    def _render_clues(self):
        """
        渲染线索
        """
        clues_title = "线索："
        title_surface = self.font.render(clues_title, True, Config.COLORS['BLACK'])
        self.screen.blit(title_surface, (50, 160))
        
        clues = self.lock_data['puzzle']['clues']
        for i, clue in enumerate(clues):
            clue_surface = self.small_font.render(f"• {clue}", True, Config.COLORS['DARK_GREEN'])
            self.screen.blit(clue_surface, (70, 190 + i * 25))
    
    def _render_input_boxes(self):
        """
        渲染输入框
        """
        for i, box in enumerate(self.input_boxes):
            # 绘制输入框边框
            pygame.draw.rect(self.screen, Config.COLORS['BLACK'], box, 2)
            pygame.draw.rect(self.screen, Config.COLORS['WHITE'], box)
            pygame.draw.rect(self.screen, Config.COLORS['BLACK'], box, 2)
            
            # 绘制输入的数字
            if i < len(self.current_input):
                digit_text = str(self.current_input[i])
                digit_surface = self.title_font.render(digit_text, True, Config.COLORS['BLACK'])
                digit_rect = digit_surface.get_rect(center=box.center)
                self.screen.blit(digit_surface, digit_rect)
    
    def _render_number_buttons(self):
        """
        渲染数字按键
        """
        for i, button in enumerate(self.number_buttons):
            # 按钮背景
            pygame.draw.rect(self.screen, Config.COLORS['LIGHT_BLUE'], button)
            pygame.draw.rect(self.screen, Config.COLORS['BLACK'], button, 2)
            
            # 数字文本
            number_text = self.font.render(str(i), True, Config.COLORS['BLACK'])
            number_rect = number_text.get_rect(center=button.center)
            self.screen.blit(number_text, number_rect)
    
    def _render_buttons(self):
        """
        渲染功能按钮
        """
        # 清除按钮
        pygame.draw.rect(self.screen, Config.COLORS['ORANGE'], self.clear_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.clear_button, 2)
        clear_text = self.small_font.render("清除", True, Config.COLORS['WHITE'])
        clear_rect = clear_text.get_rect(center=self.clear_button.center)
        self.screen.blit(clear_text, clear_rect)
        
        # 提交按钮
        pygame.draw.rect(self.screen, Config.COLORS['GREEN'], self.submit_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.submit_button, 2)
        submit_text = self.small_font.render("提交", True, Config.COLORS['WHITE'])
        submit_rect = submit_text.get_rect(center=self.submit_button.center)
        self.screen.blit(submit_text, submit_rect)
        
        # AI解谜按钮
        pygame.draw.rect(self.screen, Config.COLORS['BLUE'], self.auto_solve_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.auto_solve_button, 2)
        auto_text = self.small_font.render("AI解谜", True, Config.COLORS['WHITE'])
        auto_rect = auto_text.get_rect(center=self.auto_solve_button.center)
        self.screen.blit(auto_text, auto_rect)
    
    def _render_result_message(self):
        """
        渲染结果消息
        """
        # 半透明背景
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(128)
        overlay.fill(Config.COLORS['BLACK'])
        self.screen.blit(overlay, (0, 0))
        
        # 消息框
        message_box = pygame.Rect(200, 250, 400, 100)
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], message_box)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], message_box, 3)
        
        # 消息文本
        color = Config.COLORS['GREEN'] if self.puzzle_solved else Config.COLORS['RED']
        message_surface = self.font.render(self.result_message, True, color)
        message_rect = message_surface.get_rect(center=message_box.center)
        self.screen.blit(message_surface, message_rect)
        
