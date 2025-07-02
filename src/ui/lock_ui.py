#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码锁解谜UI界面模块
提供可视化的解谜界面和交互
"""

import pygame
import sys
import json
import tkinter as tk
from tkinter import filedialog
from typing import Dict, List, Tuple, Optional
from src.config import Config
from src.game_engine import GameEngine
from src.algorithms.Lock import PasswordLock

class LockUI:
    def __init__(self, game_engine: GameEngine, lock_data: Dict, remembered_json_file: str = None):
        self.game_engine = game_engine
        self.lock_data = lock_data
        self.remembered_json_file = remembered_json_file
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # 初始化密码锁
        self.password_lock = PasswordLock()
        
        # 生成答案的哈希值
        if 'puzzle' in lock_data and 'password' in lock_data['puzzle']:
            password = lock_data['puzzle']['password']
            password_str = ''.join(map(str, password))
            self.password_hash = self.password_lock.hash_password(password_str)
            print(f"[调试信息] 密码锁答案: {password_str}")
            print(f"[调试信息] 密码哈希值: {self.password_hash}")
        
        # 清除可能存在的定时器，防止影响新的解谜界面
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
        
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
        self.back_button = None
        self.number_buttons = []  # 数字按键
        self.clear_button = None  # 清除按钮
        
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
            # emoji字体
            self.emoji_title_font = pygame.font.Font('font/seguiemj.ttf', 32)
            self.emoji_font = pygame.font.Font('font/seguiemj.ttf', 20)
            self.emoji_small_font = pygame.font.Font('font/seguiemj.ttf', 32)
        except:
            self.title_font = pygame.font.SysFont('Arial', 32)
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
            # emoji字体fallback
            self.emoji_title_font = pygame.font.SysFont('Arial', 32)
            self.emoji_font = pygame.font.SysFont('Arial', 20)
            self.emoji_small_font = pygame.font.SysFont('Arial', 16)
        
        # 初始化UI元素
        self._initialize_ui_elements()
    
    def _render_mixed_text(self, text: str, size: str, color: Tuple[int, int, int]) -> pygame.Surface:
        """
        渲染包含文字和emoji的混合文本
        
        Args:
            text: 要渲染的文本
            size: 字体大小 ('normal', 'small', 'title')
            color: 文字颜色
            
        Returns:
            渲染后的Surface
        """
        # 选择字体
        if size == 'title':
            text_font = self.title_font
            emoji_font = self.emoji_title_font
        elif size == 'small':
            text_font = self.small_font
            emoji_font = self.emoji_small_font
        else:  # normal
            text_font = self.font
            emoji_font = self.emoji_font
        
        # 如果文本为空或只包含不可见字符，返回最小尺寸的透明surface
        if not text or text.strip() == "":
            return pygame.Surface((1, text_font.get_height()), pygame.SRCALPHA)
        
        # 分析文本，分离emoji和普通文字
        segments = []
        current_segment = ""
        is_emoji = False
        
        for char in text:
            char_code = ord(char)
            # 判断是否为emoji字符
            char_is_emoji = (
                0x1F600 <= char_code <= 0x1F64F or  # 表情符号
                0x1F300 <= char_code <= 0x1F5FF or  # 杂项符号
                0x1F680 <= char_code <= 0x1F6FF or  # 交通和地图符号
                0x1F1E0 <= char_code <= 0x1F1FF or  # 区域指示符号
                0x2600 <= char_code <= 0x26FF or   # 杂项符号
                0x2700 <= char_code <= 0x27BF or   # 装饰符号
                0xFE00 <= char_code <= 0xFE0F or   # 变体选择器
                0x1F900 <= char_code <= 0x1F9FF     # 补充符号
            )
            
            if char_is_emoji != is_emoji:
                if current_segment:
                    segments.append((current_segment, is_emoji))
                current_segment = char
                is_emoji = char_is_emoji
            else:
                current_segment += char
        
        if current_segment:
            segments.append((current_segment, is_emoji))
        
        # 如果只有一个段落，直接渲染
        if len(segments) == 1:
            segment_text, is_emoji = segments[0]
            # 检查是否为不可见字符（如变体选择器）
            if not segment_text or segment_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in segment_text):
                return pygame.Surface((1, text_font.get_height()), pygame.SRCALPHA)
            font = emoji_font if is_emoji else text_font
            return font.render(segment_text, True, color)
        
        # 渲染各个段落并组合
        surfaces = []
        total_width = 0
        max_height = 0
        
        for segment_text, is_emoji in segments:
            # 跳过空的段落或不可见字符（如变体选择器）
            if not segment_text or segment_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in segment_text):
                continue
            font = emoji_font if is_emoji else text_font
            surface = font.render(segment_text, True, color)
            surfaces.append(surface)
            total_width += surface.get_width()
            max_height = max(max_height, surface.get_height())
        
        # 创建组合surface
        combined_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        x_offset = 0
        
        for surface in surfaces:
            y_offset = (max_height - surface.get_height()) // 2
            combined_surface.blit(surface, (x_offset, y_offset))
            x_offset += surface.get_width()
        
        return combined_surface
    
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
        
        self.clear_button = pygame.Rect(220, 540, button_width, button_height)
        self.submit_button = pygame.Rect(330, 540, button_width, button_height)
        self.auto_solve_button = pygame.Rect(440, 540, button_width, button_height)
        self.load_json_button = pygame.Rect(550, 540, button_width, button_height)
        self.back_button = pygame.Rect(50, 50, 80, 30)
    
    def run(self) -> Dict:
        """
        运行解谜界面主循环
        
        Returns:
            Dict: 解谜结果
        """
        # 检查是否有记住的JSON文件，如果有就自动加载
        if self.remembered_json_file:
            self._load_json_file_auto(self.remembered_json_file)
        
        while self.running:
            # 处理事件
            self._handle_events()
            
            # 渲染界面
            self._render()
            
            # 控制帧率
            self.clock.tick(Config.FPS)
        
        # 清除定时器，防止影响后续界面
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
        
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
            self.result_message = "解谜取消"
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
        
        elif self.load_json_button.collidepoint(pos):
            self._load_json_file()
        
        elif self.back_button.collidepoint(pos):
            self.result_message = "解谜取消"
            self.running = False
    
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
        test_password = ''.join(map(str, self.current_input))
        if self.password_lock.verify_password(test_password, self.password_hash):
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
        correct_password = puzzle_data['password']
        solution, attempts = self.game_engine.puzzle_solver.solve_password_puzzle(puzzle_data['clues'], correct_password)
        
        if solution:
            self.current_input = solution
            self.puzzle_solved = True
            self.result_message = f"AI解谜成功！密码是{''.join(map(str, solution))}，尝试了{attempts}次"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
            # 延迟1秒后退出
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
        else:
            self.result_message = f"AI解谜失败，尝试了{attempts}次"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
        
    def _load_json_file(self):
        """
        打开JSON文件并解析密码
        """
        try:
            # 隐藏pygame窗口，显示文件选择对话框
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            file_path = filedialog.askopenfilename(
                title="选择JSON文件",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            root.destroy()
            
            if not file_path:
                return
            
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取C和L
            C = data.get('C', [])
            L = data.get('L', '')
            
            if not C:
                self.result_message = "JSON文件中未找到'C'字段！"
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                return
            
            # 调用密码破解算法
            ans, times = self._puzzle_solver(C, L)
            
            if ans != -1:
                # 解密成功
                self.puzzle_solved = True
                cost = times - 1
                self.result_message = f"JSON解密成功！密码是{ans}，尝试了{times}次，消耗资源{cost}"
                
                # 减少资源
                if hasattr(self.game_engine, 'player_resources'):
                    self.game_engine.player_resources = self.game_engine.player_resources - cost - 20
                
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                # 延迟3秒后退出
                pygame.time.set_timer(pygame.USEREVENT + 1, 3000)
            else:
                self.result_message = f"JSON解密失败，尝试了{times}次"
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                
        except Exception as e:
            self.result_message = f"读取JSON文件失败：{str(e)}"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
    
    def _load_json_file_auto(self, file_path: str):
        """
        自动加载指定的JSON文件并解析密码
        
        Args:
            file_path: JSON文件路径
        """
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取C和L
            C = data.get('C', [])
            L = data.get('L', '')
            
            if not C:
                self.result_message = "记住的JSON文件中未找到'C'字段！"
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                return
            
            # 调用密码破解算法
            ans, times = self._puzzle_solver(C, L)
            
            if ans != -1:
                # 解密成功
                self.puzzle_solved = True
                cost = times - 1
                self.result_message = f"自动JSON解密成功！密码是{ans}，尝试了{times}次，消耗资源{cost}"
                
                # 减少资源
                if hasattr(self.game_engine, 'player_resources'):
                    self.game_engine.player_resources = self.game_engine.player_resources - cost - 20
                
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                # 延迟3秒后退出
                pygame.time.set_timer(pygame.USEREVENT + 1, 3000)
            else:
                self.result_message = f"自动JSON解密失败，尝试了{times}次"
                self.show_result = True
                self.result_start_time = pygame.time.get_ticks()
                
        except Exception as e:
            self.result_message = f"自动读取JSON文件失败：{str(e)}"
            self.show_result = True
            self.result_start_time = pygame.time.get_ticks()
    
    def _puzzle_solver(self, C: List[List[int]], L: str) -> Tuple[int, int]:
        """
        密码破解算法（Python版本的C++代码实现）
        
        Args:
            C: 二维数组，包含约束条件
            L: 目标哈希字符串
            
        Returns:
            Tuple[int, int]: (答案, 尝试次数)
        """
        times = 0
        flag = 0
        ANS = [-3, -3, -3]
        prime = [2, 3, 5, 7]
        
        # 解析约束条件
        for constraint in C:
            if len(constraint) == 3:
                for j in range(3):
                    if constraint[j] != -1:
                        ANS[j] = constraint[j]
                        break
            else:
                if constraint[0] == -1:
                    flag = 1
                else:
                    if ANS[constraint[0] - 1] == -3:
                        ANS[constraint[0] - 1] = constraint[1] - 2
        
        # 根据flag选择不同的搜索策略
        if flag:
            # 使用素数搜索
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        if self._judge1(i, j, k, ANS):
                            times += 1
                            ans_str = str(prime[i]) + str(prime[j]) + str(prime[k])
                            if self.password_lock.verify_password(ans_str, L):
                                return int(ans_str), times
        else:
            # 使用普通数字搜索
            for i in range(10):
                for j in range(10):
                    for k in range(10):
                        if self._judge(i, j, k, ANS):
                            times += 1
                            ans_str = str(i) + str(j) + str(k)
                            if self.password_lock.verify_password(ans_str, L):
                                return int(ans_str), times
        
        return -1, times
    
    def _judge1(self, a: int, b: int, c: int, ANS: List[int]) -> bool:
        """
        判断素数约束条件
        """
        prime = [2, 3, 5, 7]
        
        if a == b or b == c or a == c:
            return False
        
        if ANS[0] >= 0 and ANS[0] != prime[a]:
            return False
        if ANS[1] >= 0 and ANS[1] != prime[b]:
            return False
        if ANS[2] >= 0 and ANS[2] != prime[c]:
            return False
        
        if ANS[0] == -2 and a != 0:  # 第一位应该是偶数(2)
            return False
        if ANS[1] == -2 and b != 0:
            return False
        if ANS[2] == -2 and c != 0:
            return False
        
        if ANS[0] == -1 and a == 0:  # 第一位应该是奇数(不是2)
            return False
        if ANS[1] == -1 and b == 0:
            return False
        if ANS[2] == -1 and c == 0:
            return False
        
        return True
    
    def _judge(self, a: int, b: int, c: int, ANS: List[int]) -> bool:
        """
        判断普通数字约束条件
        """
        if ANS[0] >= 0 and ANS[0] != a:
            return False
        if ANS[1] >= 0 and ANS[1] != b:
            return False
        if ANS[2] >= 0 and ANS[2] != c:
            return False
        
        if ANS[0] == -2 and a % 2 != 0:  # 应该是偶数
            return False
        if ANS[1] == -2 and b % 2 != 0:
            return False
        if ANS[2] == -2 and c % 2 != 0:
            return False
        
        if ANS[0] == -1 and a % 2 == 0:  # 应该是奇数
            return False
        if ANS[1] == -1 and b % 2 == 0:
            return False
        if ANS[2] == -1 and c % 2 == 0:
            return False
        
        return True

    
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
        title_surface = self._render_mixed_text(title_text, 'title', Config.COLORS['BLACK'])
        title_rect = title_surface.get_rect(center=(400, 80))
        self.screen.blit(title_surface, title_rect)
        
        # 渲染描述
        desc_text = self.lock_data['puzzle']['description']
        desc_surface = self._render_mixed_text(desc_text, 'normal', Config.COLORS['GRAY'])
        desc_rect = desc_surface.get_rect(center=(400, 120))
        self.screen.blit(desc_surface, desc_rect)
    
    def _render_clues(self):
        """
        渲染线索
        """
        clues_title = "线索："
        title_surface = self._render_mixed_text(clues_title, 'normal', Config.COLORS['BLACK'])
        self.screen.blit(title_surface, (50, 160))
        
        clues = self.lock_data['puzzle']['clues']
        for i, clue in enumerate(clues):
            clue_surface = self._render_mixed_text(f"• {clue}", 'small', Config.COLORS['DARK_GREEN'])
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
                digit_surface = self._render_mixed_text(digit_text, 'title', Config.COLORS['BLACK'])
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
            number_text = self._render_mixed_text(str(i), 'normal', Config.COLORS['BLACK'])
            number_rect = number_text.get_rect(center=button.center)
            self.screen.blit(number_text, number_rect)
    
    def _render_buttons(self):
        """
        渲染功能按钮
        """
        # 清除按钮
        pygame.draw.rect(self.screen, Config.COLORS['ORANGE'], self.clear_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.clear_button, 2)
        clear_text = self._render_mixed_text("清除", 'small', Config.COLORS['WHITE'])
        clear_rect = clear_text.get_rect(center=self.clear_button.center)
        self.screen.blit(clear_text, clear_rect)
        
        # 提交按钮
        pygame.draw.rect(self.screen, Config.COLORS['GREEN'], self.submit_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.submit_button, 2)
        submit_text = self._render_mixed_text("提交", 'small', Config.COLORS['WHITE'])
        submit_rect = submit_text.get_rect(center=self.submit_button.center)
        self.screen.blit(submit_text, submit_rect)
        
        # AI解谜按钮
        pygame.draw.rect(self.screen, Config.COLORS['BLUE'], self.auto_solve_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.auto_solve_button, 2)
        auto_text = self._render_mixed_text("AI解谜", 'small', Config.COLORS['WHITE'])
        auto_rect = auto_text.get_rect(center=self.auto_solve_button.center)
        self.screen.blit(auto_text, auto_rect)
        
        # 打开JSON文件按钮
        pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], self.load_json_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.load_json_button, 2)
        json_text = self._render_mixed_text("打开JSON", 'small', Config.COLORS['WHITE'])
        json_rect = json_text.get_rect(center=self.load_json_button.center)
        self.screen.blit(json_text, json_rect)
        
        # 返回按钮
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], self.back_button)
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], self.back_button, 2)
        back_text = self._render_mixed_text("返回", 'small', Config.COLORS['WHITE'])
        back_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_rect)
    
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
        message_surface = self._render_mixed_text(self.result_message, 'normal', color)
        message_rect = message_surface.get_rect(center=message_box.center)
        self.screen.blit(message_surface, message_rect)
        
