#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏UI界面模块
提供可视化的游戏界面和交互
"""

import pygame
import sys
from typing import Dict, List, Tuple, Optional
from src import config
from src.config import Config
from src.game_engine import GameEngine
from src.ui.lock_ui import LockUI

class GameUI:
    """
    游戏用户界面类
    """
    
    def __init__(self, game_engine: GameEngine):
        """
        初始化游戏UI
        
        Args:
            game_engine: 游戏引擎实例
        """
        self.game_engine = game_engine
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        
        # UI状态
        self.running = True
        self.paused = False
        self.show_optimal_path = False
        self.show_greedy_path = False

        self.game_completed = False  # 游戏是否已结束
        self.show_settings = True  # 显示设置界面
        self.game_started = False  # 游戏是否已开始

        # 显示面板
        self.show_statistics = True
        self.show_controls = True
        self.show_algorithm_info = False

        
        # 路径显示
        self.optimal_path = []
        self.greedy_path = []
        self.alternative_paths = []  # 多路径方案
        self.show_alternative_paths = False  # 是否显示多路径方案
        
        # 消息系统
        self.messages = []
        self.max_messages = 5
        
        # 迷宫大小设置
        self.selected_maze_size = Config.DEFAULT_MAZE_SIZE
        
        # 初始化pygame
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """
        初始化pygame组件
        """
        pygame.init()
        
        # 创建窗口
        self.screen = pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        pygame.display.set_caption(Config.WINDOW_TITLE)
        
        # 创建时钟
        self.clock = pygame.time.Clock()
        
        # 初始化字体 - 分别为文字和emoji使用不同字体
        try:
            # 文字字体
            self.font = pygame.font.Font('d:/pycharm代码/algorithom/font/msyh.ttc', 18)
            self.small_font = pygame.font.Font('d:/pycharm代码/algorithom/font/msyh.ttc', 12)
            
            # emoji字体
            self.emoji_font = pygame.font.Font('d:/pycharm代码/algorithom/font/seguiemj.ttf', 18)
            self.emoji_small_font = pygame.font.Font('d:/pycharm代码/algorithom/font/seguiemj.ttf', 12)
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 备用字体
            self.font = pygame.font.SysFont('Arial', 18)
            self.small_font = pygame.font.SysFont('Arial', 12)
            self.emoji_font = pygame.font.SysFont('Arial', 18)
            self.emoji_small_font = pygame.font.SysFont('Arial', 12)
    
    def _render_mixed_text(self, text, font_size='normal', color=(255, 255, 255)):
        """
        渲染包含文字和emoji的混合文本
        
        Args:
            text: 要渲染的文本
            font_size: 字体大小 ('normal', 'small')
            color: 文字颜色
        
        Returns:
            pygame.Surface: 渲染后的文本表面
        """
        # 处理空文本或None
        if not text or text.strip() == "":
            # 返回一个最小尺寸的透明表面
            if font_size == 'small':
                font_height = self.small_font.get_height()
            else:
                font_height = self.font.get_height()
            return pygame.Surface((1, font_height), pygame.SRCALPHA)
        
        # 选择字体
        if font_size == 'small':
            text_font = self.small_font
            emoji_font = self.emoji_small_font
        else:
            text_font = self.font
            emoji_font = self.emoji_font
        
        # 分析文本，分离emoji和普通文字
        segments = []
        current_segment = ""
        is_emoji = False
        
        for char in text:
            # 判断是否为emoji (简化版本，检查Unicode范围)
            char_is_emoji = (
                0x1F600 <= ord(char) <= 0x1F64F or  # 表情符号
                0x1F300 <= ord(char) <= 0x1F5FF or  # 杂项符号
                0x1F680 <= ord(char) <= 0x1F6FF or  # 交通和地图符号
                0x1F1E0 <= ord(char) <= 0x1F1FF or  # 区域指示符号
                0x2600 <= ord(char) <= 0x26FF or   # 杂项符号
                0x2700 <= ord(char) <= 0x27BF or   # 装饰符号
                0xFE00 <= ord(char) <= 0xFE0F or   # 变体选择器
                0x1F900 <= ord(char) <= 0x1F9FF     # 补充符号
            )
            
            if char_is_emoji != is_emoji:
                # 类型改变，保存当前段落
                if current_segment:
                    segments.append((current_segment, is_emoji))
                current_segment = char
                is_emoji = char_is_emoji
            else:
                current_segment += char
        
        # 添加最后一个段落
        if current_segment:
            segments.append((current_segment, is_emoji))
        
        # 如果只有一种类型的文本，直接渲染
        if len(segments) == 1:
            segment_text, is_emoji_segment = segments[0]
            # 检查是否为空文本或不可见字符（如变体选择器）
            if not segment_text or segment_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in segment_text):
                return pygame.Surface((1, text_font.get_height()), pygame.SRCALPHA)
            font = emoji_font if is_emoji_segment else text_font
            return font.render(segment_text, True, color)
        
        # 渲染各个段落
        rendered_segments = []
        total_width = 0
        max_height = 0
        
        for segment_text, is_emoji_segment in segments:
            # 跳过空的段落或不可见字符（如变体选择器）
            if not segment_text or segment_text.strip() == "" or all(0xFE00 <= ord(c) <= 0xFE0F for c in segment_text):
                continue
            font = emoji_font if is_emoji_segment else text_font
            rendered = font.render(segment_text, True, color)
            rendered_segments.append(rendered)
            total_width += rendered.get_width()
            max_height = max(max_height, rendered.get_height())
        
        # 创建组合表面
        if total_width == 0 or max_height == 0:
            # 创建一个最小尺寸的透明表面，避免"Text has zero width"错误
            min_surface = pygame.Surface((1, text_font.get_height()), pygame.SRCALPHA)
            return min_surface
        
        combined_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        
        # 将各段落绘制到组合表面
        x_offset = 0
        for rendered in rendered_segments:
            y_offset = (max_height - rendered.get_height()) // 2
            combined_surface.blit(rendered, (x_offset, y_offset))
            x_offset += rendered.get_width()
        
        return combined_surface
    
    def run(self):
        """
        运行游戏主循环
        """
        # 主游戏循环
        while self.running:
            # 处理事件
            self._handle_events()
            
            # 如果显示设置界面
            if self.show_settings:
                self._draw_settings_screen()
            # 游戏已开始，渲染游戏界面
            elif self.game_started:
                self._render()
            # 如果游戏还未开始且不显示设置界面，显示空白屏幕等待初始化
            else:
                self.screen.fill(Config.COLORS['BLACK'])
            
            # 更新显示
            pygame.display.flip()
            
            # 控制帧率
            self.clock.tick(Config.FPS)
        
        pygame.quit()
    
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
            else:
                pass
    
    def _handle_keydown(self, key):
        """
        处理键盘按下事件
        
        Args:
            key: 按下的键
        """
        if self.show_settings and not self.game_started:
            # 设置界面的按键处理
            if key == pygame.K_ESCAPE:
                self.running = False
            elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
                # 开始游戏
                self.show_settings = False
                # 立即初始化游戏
                init_result = self.game_engine.initialize_game(self.selected_maze_size)
                if init_result['success']:
                    self.add_message("游戏初始化成功！")
                    self.add_message(f"迷宫大小: {init_result['maze_size']}x{init_result['maze_size']}")
                    self.game_started = True
                else:
                    self.add_message("游戏初始化失败！")
                    self.show_settings = True  # 如果初始化失败，返回设置界面
            elif key == pygame.K_UP:
                # 增加迷宫大小
                if self.selected_maze_size < Config.MAX_MAZE_SIZE:
                    self.selected_maze_size += 2  # 保持奇数
            elif key == pygame.K_DOWN:
                # 减少迷宫大小
                if self.selected_maze_size > Config.MIN_MAZE_SIZE:
                    self.selected_maze_size -= 2  # 保持奇数
            return
        
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            self.add_message("游戏暂停" if self.paused else "游戏继续")
        
        elif key == pygame.K_r:
            # 重新开始游戏
            self.show_settings = True
            self.game_started = False
            self.game_engine.maze = None
            self.optimal_path = []
            self.greedy_path = []
            self.game_completed = False  # 重置游戏结束标志
            self.messages = []
        elif key == pygame.K_o:
            # 显示/隐藏最优路径
            self.show_optimal_path = not self.show_optimal_path
            if self.show_optimal_path:
                self._calculate_optimal_path()
            self.add_message("最优路径显示" + ("开启" if self.show_optimal_path else "关闭"))
        
        elif key == pygame.K_g:
            # 显示/隐藏贪心路径
            self.show_greedy_path = not self.show_greedy_path
            if self.show_greedy_path:
                self._calculate_greedy_path()
            self.add_message("贪心路径显示" + ("开启" if self.show_greedy_path else "关闭"))
        
        elif key == pygame.K_s:
            # 切换统计信息显示
            self.show_statistics = not self.show_statistics
        
        elif key == pygame.K_h:
            # 切换控制帮助显示
            self.show_controls = not self.show_controls
        
        elif key == pygame.K_i:
            # 切换算法信息显示
            self.show_algorithm_info = not self.show_algorithm_info
        
        elif key == pygame.K_a:
            # 切换自动拾取功能
            if not self.paused and not self.game_completed:
                toggle_result = self.game_engine.toggle_auto_pickup()
                self.add_message(toggle_result['message'])
                
                # 如果开启了自动拾取，执行一次完整的自动拾取
                if toggle_result['auto_pickup_enabled']:
                    pickup_result = self.game_engine.auto_pickup_until_complete(max_steps=50)
                    if pickup_result['success']:
                        if pickup_result['resources_collected'] > 0:
                            self.add_message(f"自动拾取完成: 收集了{pickup_result['resources_collected']}个资源")

                        else:
                            self.add_message("3x3区域内没有可收集的资源")
                    else:
                        self.add_message(f"自动拾取失败: {pickup_result.get('message', '未知错误')}")
            else:
                self.add_message("游戏暂停或已结束时无法使用自动拾取")
        
        elif key == pygame.K_c:
            # 比较路径策略
            self._compare_path_strategies()
        
        elif key == pygame.K_p:
            # 显示资源路径规划
            self._show_resource_path_planning()
        
        elif key == pygame.K_n:
            # 自动导航到最近资源
            self._auto_navigate_to_nearest_resource()
        
        elif key == pygame.K_e:
            # 自动导航到出口
            self._auto_navigate_to_exit()
        
        elif key == pygame.K_m:
            # 显示多个路径方案
            self._show_path_alternatives()
        
        elif key == pygame.K_v:
            # 切换多路径方案显示
            if self.alternative_paths:
                self.show_alternative_paths = not self.show_alternative_paths
                status = "开启" if self.show_alternative_paths else "关闭"
                self.add_message(f"多路径方案显示已{status}")
            else:
                self.add_message("请先按M键生成路径方案")
        
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            # Enter键交互
            if self.game_engine.pending_interaction:
                interaction_result = self.game_engine.interact_with_special_cell()
                if interaction_result['success']:
                    self.add_message(interaction_result['message'])
                    # 处理不同类型的交互
                    if interaction_result['type'] == 'puzzle':
                        self._handle_lock_encounter(interaction_result)
                    elif interaction_result['type'] == 'multi_monster_battle':
                        self._handle_multi_monster_battle(interaction_result)
                else:
                    self.add_message(interaction_result['message'])
        
        elif not self.paused and not self.game_completed:
            # 手动移动控制
            direction = None
            if key == pygame.K_UP :
                direction = 'up'
            elif key == pygame.K_DOWN:
                direction = 'down'
            elif key == pygame.K_LEFT:
                direction = 'left'
            elif key == pygame.K_RIGHT:
                direction = 'right'
            
            if direction:
                prev_pos = self.game_engine.player_pos
                result = self.game_engine.move_player(direction)
                if result['success']:
                    interaction = result.get('interaction', {})
                    if interaction.get('message'):
                        self.add_message(interaction['message'])
                    # 删除已拾取资源格子
                    pos = self.game_engine.player_pos
                    i, j = pos
                    # 旧的L格处理逻辑已移除，现在使用interaction系统处理
                    # 检查是否触发陷阱
                    if self.game_engine.maze[i][j] == 'T':
                        self.add_message("⚠️ 你触发了一个陷阱！")
                        self._play_trap_animation()  # 显示动画提示
                        # 陷阱现在只消耗资源，不再影响生命值
                        self.add_message(f"资源 -{Config.TRAP_RESOURCE_COST}")
                        self.game_engine.maze[i][j] = Config.PATH  # 陷阱只触发一次，设为空地

                    if self.game_engine.maze[i][j] == 'E':
                        self.add_message("🎉 恭喜！你已到达出口，游戏结束！")
                        self.game_completed = True  # ✅ 标记游戏结束
                        return  # 停止后续处理
                    if self.game_engine.maze[i][j] == Config.GOLD:
                        self.game_engine.maze[i][j] = Config.PATH  # 将资源格子改为空白路径

                    # 检查是否遇到需要交互的特殊方格
                    if interaction.get('type') == 'pending_multi_monster_battle':
                        # 不立即处理，等待Enter键交互
                        pass
                    elif interaction.get('type') == 'pending_puzzle':
                        # 不立即处理，等待Enter键交互
                        pass
                    # 保留旧的立即处理逻辑（如果有的话）
                    elif interaction.get('type') == 'multi_monster_battle':
                        self._handle_multi_monster_battle(interaction)
                    elif interaction.get('type') == 'boss':
                        self._handle_boss_encounter(interaction)
                    elif interaction.get('type') == 'puzzle':
                        self._handle_lock_encounter(interaction)
                else:
                    self.add_message(result['message'])
        else:
            # 处理未定义的按键，防止程序无响应
            pass
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """
        处理鼠标点击事件
        
        Args:
            pos: 鼠标点击位置
        """
        # 可以添加鼠标交互逻辑，比如点击迷宫格子
        pass
    

    def _play_trap_animation(self):
    
    #显示陷阱触发动画（例如红色闪烁）
    
        for _ in range(3):
            self.screen.fill(Config.COLORS['RED'])  # 红色闪屏
            pygame.display.flip()
            pygame.time.delay(100)
            
            self._render()  # 恢复正常画面
            pygame.display.flip()
            pygame.time.delay(100)

    def _calculate_optimal_path(self):
        """
        计算并缓存最优路径
        """
        result = self.game_engine.get_optimal_path()
        if result['success']:
            self.optimal_path = result['optimal_path']
            self.add_message(f"最优路径计算完成，价值: {result['max_value']}")
        else:
            self.add_message("最优路径计算失败")
    
    def _calculate_greedy_path(self):
        """
        计算并缓存贪心路径
        """
        result = self.game_engine.get_greedy_path()
        if result['success']:
            self.greedy_path = result['greedy_path']
            self.add_message(f"贪心路径计算完成")
        else:
            self.add_message("贪心路径计算失败")
    
    def _compare_path_strategies(self):
        """
        比较路径策略
        """
        result = self.game_engine.compare_path_strategies()
        if result['success']:
            comparison = result['comparison']
            improvement = comparison['improvement']
            
            self.add_message(f"路径比较完成:")
            self.add_message(f"DP路径长度: {len(comparison['dp_path']['path'])}, 贪心路径长度: {len(comparison['greedy_path']['path'])}")

        else:
            self.add_message("路径比较失败")
    
    def _handle_lock_encounter(self, interaction: Dict):
        """
        处理Lock遭遇事件
        
        Args:
            interaction: 交互信息
        """
        self.add_message("发现密码锁，进入解谜界面...")
        
        # 创建谜题数据
        lock_data = {
            'puzzle': interaction.get('puzzle'),
            'position': self.game_engine.player_pos
        }
        
        # 创建并运行解谜界面
        lock_ui = LockUI(self.game_engine, lock_data)
        puzzle_result = lock_ui.run()
        
        # 处理解谜结果
        if puzzle_result['success']:
            self.add_message("密码锁解开成功！")
            # 在游戏引擎中标记谜题已解决
            if hasattr(self.game_engine, 'active_puzzle') and self.game_engine.active_puzzle:
                self.game_engine.solved_puzzles.add(self.game_engine.active_puzzle['position'])
                reward = 20
                self.game_engine.player_resources += reward

                self.add_message(f"获得{reward}资源奖励！")
                self.game_engine.active_puzzle = None
        else:
            self.add_message("解谜失败或取消")
        
        # 恢复主游戏窗口
        pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        pygame.display.set_caption(Config.WINDOW_TITLE)

    def _handle_multi_monster_battle(self, interaction: Dict):
        """
        处理多怪物战斗遭遇事件
        
        Args:
            interaction: 交互信息
        """
        from .multi_battle_ui import MultiMonsterBattleUI
        
        scenario = interaction.get('scenario', 'medium')
        self.add_message(f"进入多怪物战斗界面... {interaction.get('message', '')}")
        
        # 创建并运行多怪物战斗UI
        battle_ui = MultiMonsterBattleUI(scenario)
        battle_result = battle_ui.run()
        
        # 处理战斗结果
        if not battle_result:
            return

        status = battle_result.get('status')
        message = battle_result.get('message', '战斗已结束。')

        if status == 'victory':
            self.add_message(f"Boss战斗胜利！ {message}")
            # ✅ 删除 Boss 格子
            i, j = self.game_engine.player_pos
            if self.game_engine.maze[i][j] == 'B':
                self.game_engine.maze[i][j] = Config.PATH  # 将 Boss 格子变为空地
        elif status == 'defeat':
            self.add_message(f"多怪物战斗失败: {message}")
        else:
            self.add_message(f"多怪物战斗结束: {message}")
        
        # 恢复主游戏窗口
        pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        pygame.display.set_caption(Config.WINDOW_TITLE)
    
    def _render(self):
        """
        渲染游戏画面
        """
        # 清空屏幕
        self.screen.fill(Config.COLORS['WHITE'])
        
        # 渲染迷宫
        self._render_maze()
        
        # 渲染路径
        if self.show_alternative_paths and self.alternative_paths:
            # 绘制多路径方案
            self._render_alternative_paths()
        else:
            # 绘制传统路径
            if self.show_optimal_path and self.optimal_path:
                self._render_path(self.optimal_path, Config.COLORS['BLUE'], 2)
            
            if self.show_greedy_path and self.greedy_path:
                self._render_path(self.greedy_path, Config.COLORS['GREEN'], 2)
        
        # 渲染玩家
        self._render_player()
        
        # 渲染UI面板
        self._render_ui_panels()
        
        # 更新显示
        pygame.display.flip()
    
    def _render_maze(self):
        """
        渲染迷宫
        """
        if not self.game_engine.maze:
            return
        
        maze = self.game_engine.maze
        maze_size = self.game_engine.maze_size
        
        # 计算迷宫渲染区域
        maze_area_width = min(600, Config.WINDOW_WIDTH - 400)
        maze_area_height = min(600, Config.WINDOW_HEIGHT - 100)
        cell_size = min(maze_area_width // maze_size, maze_area_height // maze_size)
        
        start_x = 50
        start_y = 50
        
        for i in range(maze_size):
            for j in range(maze_size):
                x = start_x + j * cell_size
                y = start_y + i * cell_size
                
                cell = maze[i][j]
                
                # 如果是已解决的谜题，显示为普通路径
                if cell == Config.LOCKER and (i, j) in self.game_engine.solved_puzzles:
                    cell = Config.PATH
                
                color = Config.ELEMENT_COLORS.get(cell, Config.COLORS['WHITE'])
                
                # 绘制阴影效果（对于墙壁和特殊元素）
                if cell == Config.WALL or cell in [Config.GOLD, Config.BOSS, Config.LOCKER]:
                    shadow_color = Config.COLORS['SHADOW']
                    pygame.draw.rect(self.screen, shadow_color, (x + 2, y + 2, cell_size, cell_size))
                
                # 绘制格子主体
                pygame.draw.rect(self.screen, color, (x, y, cell_size, cell_size))
                
                # 绘制特殊效果
                if cell == Config.START:
                    # 起点：绿色渐变边框
                    pygame.draw.rect(self.screen, Config.COLORS['SUCCESS'], (x, y, cell_size, cell_size), 3)
                    pygame.draw.rect(self.screen, Config.COLORS['LIGHT_GREEN'], (x + 2, y + 2, cell_size - 4, cell_size - 4), 1)
                elif cell == Config.EXIT:
                    # 终点：蓝色渐变边框
                    pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], (x, y, cell_size, cell_size), 3)
                    pygame.draw.rect(self.screen, Config.COLORS['CYAN'], (x + 2, y + 2, cell_size - 4, cell_size - 4), 1)
                elif cell == Config.GOLD:
                    # 金币：金色光晕效果
                    pygame.draw.rect(self.screen, Config.COLORS['GOLD'], (x, y, cell_size, cell_size), 2)
                    center_x, center_y = x + cell_size // 2, y + cell_size // 2
                    pygame.draw.circle(self.screen, Config.COLORS['YELLOW'], (center_x, center_y), cell_size // 4, 1)
                elif cell == Config.TRAP:
                    # 陷阱：红色警告边框
                    pygame.draw.rect(self.screen, Config.COLORS['DANGER'], (x, y, cell_size, cell_size), 2)
                elif cell == Config.BOSS:
                    # Boss：紫色强化边框
                    pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], (x, y, cell_size, cell_size), 3)
                    pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], (x + 1, y + 1, cell_size - 2, cell_size - 2), 1)
                elif cell == Config.LOCKER:
                    # 机关：橙色边框
                    pygame.draw.rect(self.screen, Config.COLORS['WARNING'], (x, y, cell_size, cell_size), 2)
                else:
                    # 普通格子：细边框
                    pygame.draw.rect(self.screen, Config.COLORS['BORDER'], (x, y, cell_size, cell_size), 1)
                
                # 绘制元素符号（使用更好的字体和颜色）
                if cell != Config.WALL and cell != Config.PATH:
                    # 根据元素类型选择合适的文字颜色
                    if cell == Config.START:
                        text_color = Config.COLORS['WHITE']
                        symbol = "🏁"
                    elif cell == Config.EXIT:
                        text_color = Config.COLORS['WHITE']
                        symbol = "🎯"
                    elif cell == Config.GOLD:
                        text_color = Config.COLORS['WHITE']
                        symbol = "💎"
                    elif cell == Config.TRAP:
                        text_color = Config.COLORS['WHITE']
                        symbol = "⚠️"
                    elif cell == Config.BOSS:
                        text_color = Config.COLORS['WHITE']
                        symbol = "👹"
                    elif cell == Config.LOCKER:
                        text_color = Config.COLORS['WHITE']
                        symbol = "🔐"
                    else:
                        text_color = Config.COLORS['WHITE']
                        symbol = cell
                    
                    text_surface = self._render_mixed_text(symbol, 'small', text_color)
                    text_rect = text_surface.get_rect(center=(x + cell_size // 2, y + cell_size // 2))
                    self.screen.blit(text_surface, text_rect)
    
    def _render_path(self, path: List[Tuple[int, int]], color: Tuple[int, int, int], width: int):
        """
        渲染路径
        
        Args:
            path: 路径坐标列表
            color: 路径颜色
            width: 线条宽度
        """
        if len(path) < 2:
            return
        
        maze_size = self.game_engine.maze_size
        maze_area_width = min(600, Config.WINDOW_WIDTH - 400)
        maze_area_height = min(600, Config.WINDOW_HEIGHT - 100)
        cell_size = min(maze_area_width // maze_size, maze_area_height // maze_size)
        
        start_x = 50
        start_y = 50
        
        points = []
        for i, j in path:
            x = start_x + j * cell_size + cell_size // 2
            y = start_y + i * cell_size + cell_size // 2
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, width)
    
    def _render_alternative_paths(self):
        """
        渲染多个备选路径方案
        """
        if not self.alternative_paths:
            return
        
        # 定义不同路径的颜色和样式
        path_colors = [
            (Config.COLORS['BLUE'], 3),      # 方案1：蓝色，粗线
            (Config.COLORS['GREEN'], 3),     # 方案2：绿色，粗线
            (Config.COLORS['RED'], 3),       # 方案3：红色，粗线
            (Config.COLORS['PURPLE'], 2),    # 方案4：紫色，中线
            (Config.COLORS['ORANGE'], 2),    # 方案5：橙色，中线
        ]
        
        maze_size = self.game_engine.maze_size
        maze_area_width = min(600, Config.WINDOW_WIDTH - 400)
        maze_area_height = min(600, Config.WINDOW_HEIGHT - 100)
        cell_size = min(maze_area_width // maze_size, maze_area_height // maze_size)
        start_x = 50
        start_y = 50
        
        # 绘制每个路径方案
        for i, alt in enumerate(self.alternative_paths):
            if not alt.get('success') or not alt.get('path'):
                continue
            
            path = alt['path']
            if i < len(path_colors):
                color, width = path_colors[i]
            else:
                color, width = Config.COLORS['GRAY'], 2
            
            # 绘制路径线条
            self._render_path(path, color, width)
            
            # 绘制路径起点和终点标记
            if len(path) >= 2:
                # 起点标记
                start_i, start_j = path[0]
                start_x_pos = start_x + start_j * cell_size + cell_size // 2
                start_y_pos = start_y + start_i * cell_size + cell_size // 2
                pygame.draw.circle(self.screen, color, (start_x_pos, start_y_pos), cell_size // 4, 2)
                
                # 终点标记
                end_i, end_j = path[-1]
                end_x_pos = start_x + end_j * cell_size + cell_size // 2
                end_y_pos = start_y + end_i * cell_size + cell_size // 2
                pygame.draw.rect(self.screen, color, 
                               (end_x_pos - cell_size//4, end_y_pos - cell_size//4, 
                                cell_size//2, cell_size//2), 2)
            
            # 绘制资源收集点
            resources_collected = alt.get('resources_collected', [])
            for resource in resources_collected:
                if 'position' in resource:
                    res_i, res_j = resource['position']
                    res_x = start_x + res_j * cell_size + cell_size // 2
                    res_y = start_y + res_i * cell_size + cell_size // 2
                    # 绘制资源收集标记（小圆圈）
                    pygame.draw.circle(self.screen, color, (res_x, res_y), cell_size // 6, 2)
        
        # 绘制路径图例
        self._render_path_legend()
    
    def _render_path_legend(self):
        """
        绘制路径图例
        """
        legend_x = Config.WINDOW_WIDTH - 340
        legend_y = 400
        legend_width = 320
        legend_height = min(150, 30 + len(self.alternative_paths) * 25)
        
        # 绘制阴影
        shadow_offset = 3
        pygame.draw.rect(self.screen, Config.COLORS['SHADOW'], 
                        (legend_x + shadow_offset, legend_y + shadow_offset, legend_width, legend_height))
        
        # 绘制图例背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], 
                        (legend_x, legend_y, legend_width, legend_height))
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], 
                        (legend_x, legend_y, legend_width, legend_height), 2)
        
        # 绘制标题栏
        title_height = 25
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], 
                        (legend_x, legend_y, legend_width, title_height))
        
        # 绘制标题
        title = self._render_mixed_text("🗺️ 路径方案图例", 'normal', Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(legend_x + legend_width // 2, legend_y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 绘制每个路径的图例
        path_colors = [
            (Config.COLORS['BLUE'], "🔵", "蓝色路径"),
            (Config.COLORS['GREEN'], "🟢", "绿色路径"),
            (Config.COLORS['RED'], "🔴", "红色路径"),
            (Config.COLORS['PURPLE'], "🟣", "紫色路径"),
            (Config.COLORS['ORANGE'], "🟠", "橙色路径"),
        ]
        
        for i, alt in enumerate(self.alternative_paths[:5]):  # 最多显示5个
            if not alt.get('success'):
                continue
            
            y_offset = legend_y + title_height + 5 + i * 22
            
            # 绘制颜色指示器
            if i < len(path_colors):
                color, icon, color_name = path_colors[i]
                # 绘制图标
                icon_surface = self._render_mixed_text(icon, 'small', color)
                self.screen.blit(icon_surface, (legend_x + 8, y_offset))
                
                # 绘制线条
                pygame.draw.line(self.screen, color, 
                               (legend_x + 25, y_offset + 8), 
                               (legend_x + 45, y_offset + 8), 3)
            
            # 绘制路径信息
            name = alt.get('name', f'方案{i+1}')
            value = alt.get('total_value', 0)
            text = f"{name} (价值:{value})"
            text_surface = self._render_mixed_text(text, 'small', Config.COLORS['TEXT_PRIMARY'])
            self.screen.blit(text_surface, (legend_x + 55, y_offset))
    
    def _render_player(self):
        """
        渲染玩家
        """
        if not self.game_engine.player_pos:
            return
        
        i, j = self.game_engine.player_pos
        maze_size = self.game_engine.maze_size
        
        maze_area_width = min(600, Config.WINDOW_WIDTH - 400)
        maze_area_height = min(600, Config.WINDOW_HEIGHT - 100)
        cell_size = min(maze_area_width // maze_size, maze_area_height // maze_size)
        
        start_x = 50
        start_y = 50
        
        x = start_x + j * cell_size + cell_size // 2
        y = start_y + i * cell_size + cell_size // 2
        
        # 绘制玩家阴影
        shadow_radius = cell_size // 3
        pygame.draw.circle(self.screen, Config.COLORS['SHADOW'], (x + 2, y + 2), shadow_radius)
        
        # 绘制玩家主体（渐变效果）
        player_radius = cell_size // 3
        pygame.draw.circle(self.screen, Config.COLORS['ACCENT'], (x, y), player_radius)
        pygame.draw.circle(self.screen, Config.COLORS['ORANGE'], (x, y), player_radius - 2)
        
        # 绘制玩家边框
        pygame.draw.circle(self.screen, Config.COLORS['WHITE'], (x, y), player_radius, 2)
        
        # 绘制玩家图标
        player_symbol = "🚶"
        symbol_surface = self._render_mixed_text(player_symbol, 'small', Config.COLORS['WHITE'])
        symbol_rect = symbol_surface.get_rect(center=(x, y))
        self.screen.blit(symbol_surface, symbol_rect)
    
    def _render_ui_panels(self):
        """
        渲染UI面板
        """
        panel_x = Config.WINDOW_WIDTH - 350
        panel_y = 50
        
        # 游戏状态面板
        if self.show_statistics:
            panel_y = self._render_statistics_panel(panel_x, panel_y)
        
        # 控制帮助面板
        if self.show_controls:
            panel_y = self._render_controls_panel(panel_x, panel_y)
        
        # 算法信息面板
        if self.show_algorithm_info:
            panel_y = self._render_algorithm_panel(panel_x, panel_y)
        

        
        # 交互提示面板
        if self.game_engine.pending_interaction:
            panel_y = self._render_interaction_panel(panel_x, panel_y)
        
        # 消息面板
        self._render_messages_panel(panel_x, Config.WINDOW_HEIGHT - 200)
    
    def _render_statistics_panel(self, x: int, y: int) -> int:
        """
        渲染统计信息面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        game_state = self.game_engine.get_game_state()
        
        # 面板背景 - 现代化设计
        panel_height = 200
        panel_width = 320
        
        # 绘制阴影效果
        shadow_offset = 4
        pygame.draw.rect(self.screen, (0, 0, 0, 50), 
                        (x + shadow_offset, y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (x, y, panel_width, panel_height))
        
        # 绘制渐变边框
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], (x, y, panel_width, panel_height), 2)
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BORDER'], (x + 1, y + 1, panel_width - 2, panel_height - 2), 1)
        
        # 标题栏背景
        title_height = 35
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], (x, y, panel_width, title_height))
        
        # 标题
        title = self._render_mixed_text("📊 游戏统计", 'normal', Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(x + panel_width // 2, y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 获取自动拾取状态
        auto_pickup_status = self.game_engine.get_auto_pickup_status()
        
        # 统计信息 - 使用图标和颜色编码
        stats_data = [
            ("📍", "位置", f"{game_state['player_pos']}", Config.COLORS['INFO']),
            ("👣", "移动", f"{game_state['moves_count']}步", Config.COLORS['CYAN']),
            ("💎", "资源", f"{game_state['player_resources']}", Config.COLORS['GOLD']),
            ("📦", "物品", f"{game_state['collected_items']}", Config.COLORS['SUCCESS']),
            ("🧩", "解谜", f"{game_state['solved_puzzles']}", Config.COLORS['PURPLE']),
            ("👹", "BOSS", f"{game_state['defeated_bosses']}", Config.COLORS['DANGER']),
            ("🤖", "自动拾取", '开启' if auto_pickup_status['enabled'] else '关闭', 
             Config.COLORS['SUCCESS'] if auto_pickup_status['enabled'] else Config.COLORS['TEXT_DISABLED'])
        ]
        
        # 绘制统计信息
        start_y = y + title_height + 10
        for i, (icon, label, value, color) in enumerate(stats_data):
            item_y = start_y + i * 22
            
            # 绘制图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            self.screen.blit(icon_surface, (x + 15, item_y))
            
            # 绘制标签
            label_surface = self._render_mixed_text(f"{label}:", 'small', Config.COLORS['TEXT_SECONDARY'])
            self.screen.blit(label_surface, (x + 40, item_y))
            
            # 绘制数值
            value_surface = self._render_mixed_text(value, 'small', color)
            value_rect = value_surface.get_rect()
            self.screen.blit(value_surface, (x + panel_width - value_rect.width - 15, item_y))
        
        return y + panel_height + 15
    
    def _render_interaction_panel(self, x: int, y: int) -> int:
        """
        渲染交互提示面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景 - 现代化设计
        panel_height = 90
        panel_width = 320
        
        # 绘制阴影效果
        shadow_offset = 4
        pygame.draw.rect(self.screen, (0, 0, 0, 50), 
                        (x + shadow_offset, y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板背景 - 使用警告色
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (x, y, panel_width, panel_height))
        
        # 绘制动态边框 - 闪烁效果
        border_color = Config.COLORS['WARNING']
        pygame.draw.rect(self.screen, border_color, (x, y, panel_width, panel_height), 3)
        pygame.draw.rect(self.screen, Config.COLORS['ACCENT'], (x + 2, y + 2, panel_width - 4, panel_height - 4), 1)
        
        # 标题栏背景
        title_height = 30
        pygame.draw.rect(self.screen, Config.COLORS['WARNING'], (x, y, panel_width, title_height))
        
        # 标题
        title = self._render_mixed_text("⚡ 可交互内容", 'normal', Config.COLORS['BLACK'])
        title_rect = title.get_rect(center=(x + panel_width // 2, y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 交互提示
        interaction = self.game_engine.pending_interaction
        if interaction['type'] == 'puzzle':
            icon = "🔐"
            hint_text = "密码锁 - 按Enter键解谜"
            hint_color = Config.COLORS['PURPLE']
        elif interaction['type'] == 'multi_monster_battle':
            icon = "⚔️"
            hint_text = "怪物群 - 按Enter键战斗"
            hint_color = Config.COLORS['DANGER']
        else:
            icon = "❓"
            hint_text = "未知内容 - 按Enter键交互"
            hint_color = Config.COLORS['INFO']
        
        # 绘制交互内容
        content_y = y + title_height + 15
        
        # 绘制图标
        icon_surface = self._render_mixed_text(icon, 'normal', hint_color)
        self.screen.blit(icon_surface, (x + 15, content_y))
        
        # 绘制提示文字
        hint_surface = self._render_mixed_text(hint_text, 'small', Config.COLORS['TEXT_PRIMARY'])
        self.screen.blit(hint_surface, (x + 50, content_y + 5))
        
        # 绘制按键提示
        key_hint = "[Enter] 交互"
        key_surface = self._render_mixed_text(key_hint, 'small', Config.COLORS['HIGHLIGHT'])
        key_rect = key_surface.get_rect()
        self.screen.blit(key_surface, (x + panel_width - key_rect.width - 15, content_y + 5))
        
        return y + panel_height + 15
    
    def _render_controls_panel(self, x: int, y: int) -> int:
        """
        渲染控制帮助面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景 - 现代化设计
        panel_height = 220
        panel_width = 320
        
        # 绘制阴影效果
        shadow_offset = 4
        pygame.draw.rect(self.screen, (0, 0, 0, 50), 
                        (x + shadow_offset, y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (x, y, panel_width, panel_height))
        
        # 绘制边框
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], (x, y, panel_width, panel_height), 2)
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BORDER'], (x + 1, y + 1, panel_width - 2, panel_height - 2), 1)
        
        # 标题栏背景
        title_height = 35
        pygame.draw.rect(self.screen, Config.COLORS['INFO'], (x, y, panel_width, title_height))
        
        # 标题
        title = self._render_mixed_text("🎮 控制帮助", 'normal', Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(x + panel_width // 2, y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 控制说明 - 分类显示
        controls_data = [
            ("🎯", "移动", "方向键/WASD", Config.COLORS['CYAN']),
            ("⚡", "交互", "Enter", Config.COLORS['WARNING']),
            ("🤖", "自动拾取", "A", Config.COLORS['SUCCESS']),
            ("🗺️", "路径方案", "M", Config.COLORS['PURPLE']),
            ("👁️", "切换显示", "V", Config.COLORS['BLUE']),
            ("📊", "路径规划", "P", Config.COLORS['GOLD']),
            ("⚖️", "策略比较", "C", Config.COLORS['ORANGE']),
            ("🔄", "重新开始", "R", Config.COLORS['DANGER']),
            ("⏸️", "暂停/继续", "Space", Config.COLORS['LIME']),
            ("❓", "帮助开关", "H", Config.COLORS['TEAL']),
            ("🚪", "退出游戏", "ESC", Config.COLORS['TEXT_DISABLED'])
        ]
        
        # 绘制控制说明
        start_y = y + title_height + 8
        for i, (icon, action, key, color) in enumerate(controls_data):
            item_y = start_y + i * 16
            
            # 绘制图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            self.screen.blit(icon_surface, (x + 10, item_y))
            
            # 绘制动作
            action_surface = self._render_mixed_text(action, 'small', Config.COLORS['TEXT_SECONDARY'])
            self.screen.blit(action_surface, (x + 35, item_y))
            
            # 绘制按键 - 右对齐
            key_surface = self._render_mixed_text(key, 'small', color)
            key_rect = key_surface.get_rect()
            self.screen.blit(key_surface, (x + panel_width - key_rect.width - 15, item_y))
        
        return y + panel_height + 15
    
    def _render_algorithm_panel(self, x: int, y: int) -> int:
        """
        渲染算法信息面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景 - 现代化设计
        panel_height = 180
        panel_width = 320
        
        # 绘制阴影效果
        shadow_offset = 4
        pygame.draw.rect(self.screen, (0, 0, 0, 50), 
                        (x + shadow_offset, y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (x, y, panel_width, panel_height))
        
        # 绘制边框
        pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], (x, y, panel_width, panel_height), 2)
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BORDER'], (x + 1, y + 1, panel_width - 2, panel_height - 2), 1)
        
        # 标题栏背景
        title_height = 35
        pygame.draw.rect(self.screen, Config.COLORS['PURPLE'], (x, y, panel_width, title_height))
        
        # 标题
        title = self._render_mixed_text("🧠 算法信息", 'normal', Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(x + panel_width // 2, y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 算法说明 - 分类显示
        algorithm_data = [
            ("🔧", "分治法", "迷宫生成", Config.COLORS['CYAN']),
            ("📈", "动态规划", "最优路径", Config.COLORS['SUCCESS']),
            ("⚡", "贪心算法", "实时策略", Config.COLORS['WARNING']),
            ("🔄", "回溯法", "解谜破解", Config.COLORS['ORANGE']),
            ("⚔️", "分支限界", "BOSS战斗", Config.COLORS['DANGER']),
        ]
        
        # 绘制算法说明
        start_y = y + title_height + 10
        for i, (icon, algorithm, usage, color) in enumerate(algorithm_data):
            item_y = start_y + i * 18
            
            # 绘制图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            self.screen.blit(icon_surface, (x + 10, item_y))
            
            # 绘制算法名称
            algo_surface = self._render_mixed_text(algorithm, 'small', color)
            self.screen.blit(algo_surface, (x + 35, item_y))
            
            # 绘制用途
            usage_surface = self._render_mixed_text(usage, 'small', Config.COLORS['TEXT_SECONDARY'])
            usage_rect = usage_surface.get_rect()
            self.screen.blit(usage_surface, (x + panel_width - usage_rect.width - 15, item_y))
        
        # 分隔线
        separator_y = start_y + len(algorithm_data) * 18 + 5
        pygame.draw.line(self.screen, Config.COLORS['PANEL_BORDER'], 
                        (x + 10, separator_y), (x + panel_width - 10, separator_y), 1)
        
        # 路径颜色说明
        path_info = [
            ("🔵", "蓝线: 动态规划路径", Config.COLORS['BLUE']),
            ("🟢", "绿线: 贪心策略路径", Config.COLORS['SUCCESS'])
        ]
        
        for i, (icon, desc, color) in enumerate(path_info):
            item_y = separator_y + 10 + i * 16
            
            # 绘制颜色图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            self.screen.blit(icon_surface, (x + 10, item_y))
            
            # 绘制说明
            desc_surface = self._render_mixed_text(desc, 'small', Config.COLORS['TEXT_SECONDARY'])
            self.screen.blit(desc_surface, (x + 35, item_y))
        
        return y + panel_height + 15
    
    def _render_messages_panel(self, x: int, y: int):
        """
        渲染消息面板
        
        Args:
            x, y: 面板位置
        """
        # 面板背景 - 现代化设计
        panel_height = 140
        panel_width = 320
        
        # 绘制阴影效果
        shadow_offset = 4
        pygame.draw.rect(self.screen, (0, 0, 0, 50), 
                        (x + shadow_offset, y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板背景
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (x, y, panel_width, panel_height))
        
        # 绘制边框
        pygame.draw.rect(self.screen, Config.COLORS['SUCCESS'], (x, y, panel_width, panel_height), 2)
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BORDER'], (x + 1, y + 1, panel_width - 2, panel_height - 2), 1)
        
        # 标题栏背景
        title_height = 35
        pygame.draw.rect(self.screen, Config.COLORS['SUCCESS'], (x, y, panel_width, title_height))
        
        # 标题
        title = self._render_mixed_text("💬 消息", 'normal', Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(x + panel_width // 2, y + title_height // 2))
        self.screen.blit(title, title_rect)
        
        # 显示最近的消息
        start_y = y + title_height + 8
        recent_messages = self.messages[-self.max_messages:]
        
        for i, message in enumerate(recent_messages):
            item_y = start_y + i * 16
            
            # 根据消息内容选择颜色
            if "成功" in message or "完成" in message or "恭喜" in message:
                msg_color = Config.COLORS['SUCCESS']
            elif "失败" in message or "错误" in message or "陷阱" in message:
                msg_color = Config.COLORS['DANGER']
            elif "警告" in message or "注意" in message:
                msg_color = Config.COLORS['WARNING']
            else:
                msg_color = Config.COLORS['TEXT_PRIMARY']
            
            # 绘制消息前缀点
            pygame.draw.circle(self.screen, msg_color, (x + 15, item_y + 6), 2)
            
            # 绘制消息文本
            text_surface = self._render_mixed_text(message, 'small', msg_color)
            # 限制文本长度以适应面板宽度
            if text_surface.get_width() > panel_width - 40:
                # 截断过长的消息
                truncated_msg = message[:40] + "..."
                text_surface = self._render_mixed_text(truncated_msg, 'small', msg_color)
            
            self.screen.blit(text_surface, (x + 25, item_y))
    
    def _draw_settings_screen(self):
        """
        绘制设置界面
        """
        # 创建渐变背景
        self.screen.fill(Config.COLORS['BLACK'])
        
        # 绘制背景装饰
        center_x = Config.WINDOW_WIDTH // 2
        center_y = Config.WINDOW_HEIGHT // 2
        
        # 绘制背景圆圈装饰
        for i in range(5):
            radius = 100 + i * 50
            alpha = 20 - i * 3
            color = (*Config.COLORS['PRIMARY'], alpha)
            # 由于pygame不直接支持alpha，我们使用较暗的颜色模拟
            dark_color = tuple(c // (i + 2) for c in Config.COLORS['PRIMARY'])
            pygame.draw.circle(self.screen, dark_color, (center_x, center_y), radius, 2)
        
        # 主标题
        try:
            title_font = pygame.font.Font('d:/pycharm代码/algorithom/font/msyh.ttc', 32)
            emoji_title_font = pygame.font.Font('d:/pycharm代码/algorithom/font/seguiemj.ttf', 32)
        except:
            title_font = pygame.font.SysFont('Arial', 32)
            emoji_title_font = pygame.font.SysFont('Arial', 32)
        
        # 渲染主标题（包含emoji）
        title_text = "🎮 迷宫探险游戏"
        title_surface = self._render_mixed_text(title_text, 'normal', Config.COLORS['PRIMARY'])
        title_rect = title_surface.get_rect(center=(center_x, 120))
        self.screen.blit(title_surface, title_rect)
        
        # 副标题
        subtitle = self._render_mixed_text("算法驱动的智能探险", 'normal', Config.COLORS['TEXT_SECONDARY'])
        subtitle_rect = subtitle.get_rect(center=(center_x, 160))
        self.screen.blit(subtitle, subtitle_rect)
        
        # 设置面板背景
        panel_width = 400
        panel_height = 300
        panel_x = center_x - panel_width // 2
        panel_y = 220
        
        # 绘制面板阴影
        shadow_offset = 6
        pygame.draw.rect(self.screen, (0, 0, 0, 100), 
                        (panel_x + shadow_offset, panel_y + shadow_offset, panel_width, panel_height))
        
        # 绘制主面板
        pygame.draw.rect(self.screen, Config.COLORS['PANEL_BG'], (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['PRIMARY'], (panel_x, panel_y, panel_width, panel_height), 3)
        
        # 迷宫大小设置区域
        size_y = panel_y + 40
        
        # 迷宫大小标题
        size_title = self._render_mixed_text("🏗️ 迷宫大小设置", 'normal', Config.COLORS['PRIMARY'])
        size_title_rect = size_title.get_rect(center=(center_x, size_y))
        self.screen.blit(size_title, size_title_rect)
        
        # 当前大小显示
        size_display_y = size_y + 50
        size_text = self._render_mixed_text(f"{self.selected_maze_size} × {self.selected_maze_size}", 'normal', Config.COLORS['HIGHLIGHT'])
        size_rect = size_text.get_rect(center=(center_x, size_display_y))
        self.screen.blit(size_text, size_rect)
        
        # 大小范围提示
        range_text = self._render_mixed_text(f"范围: {Config.MIN_MAZE_SIZE} - {Config.MAX_MAZE_SIZE}", 'small', Config.COLORS['TEXT_SECONDARY'])
        range_rect = range_text.get_rect(center=(center_x, size_display_y + 35))
        self.screen.blit(range_text, range_rect)
        
        # 控制说明区域
        controls_y = size_display_y + 70
        
        # 控制说明标题
        controls_title = self._render_mixed_text("🎯 控制说明", 'normal', Config.COLORS['INFO'])
        controls_title_rect = controls_title.get_rect(center=(center_x, controls_y))
        self.screen.blit(controls_title, controls_title_rect)
        
        # 控制说明内容
        controls = [
            ("⬆️⬇️", "调整迷宫大小", Config.COLORS['CYAN']),
            ("⏎", "开始游戏", Config.COLORS['SUCCESS']),
            ("⎋", "退出游戏", Config.COLORS['DANGER'])
        ]
        
        for i, (icon, desc, color) in enumerate(controls):
            item_y = controls_y + 30 + i * 25
            
            # 绘制图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            icon_rect = icon_surface.get_rect(center=(center_x - 80, item_y))
            self.screen.blit(icon_surface, icon_rect)
            
            # 绘制说明
            desc_surface = self._render_mixed_text(desc, 'small', Config.COLORS['TEXT_PRIMARY'])
            desc_rect = desc_surface.get_rect(center=(center_x + 20, item_y))
            self.screen.blit(desc_surface, desc_rect)
        
        # 游戏说明区域 - 在面板外部
        game_desc_y = panel_y + panel_height + 40
        
        # 游戏说明标题
        game_title = self._render_mixed_text("🎯 游戏目标", 'normal', Config.COLORS['WARNING'])
        game_title_rect = game_title.get_rect(center=(center_x, game_desc_y))
        self.screen.blit(game_title, game_title_rect)
        
        # 游戏说明内容
        descriptions = [
            ("🏁", "从起点(S)到达终点(E)", Config.COLORS['SUCCESS']),
            ("💎", "收集资源(G), 避开陷阱(T)", Config.COLORS['GOLD']),
            ("🔐", "解开机关(L), 击败BOSS(B)", Config.COLORS['PURPLE'])
        ]
        
        for i, (icon, desc, color) in enumerate(descriptions):
            item_y = game_desc_y + 30 + i * 25
            
            # 绘制图标
            icon_surface = self._render_mixed_text(icon, 'small', color)
            icon_rect = icon_surface.get_rect(center=(center_x - 120, item_y))
            self.screen.blit(icon_surface, icon_rect)
            
            # 绘制说明
            desc_surface = self._render_mixed_text(desc, 'small', Config.COLORS['TEXT_PRIMARY'])
            desc_rect = desc_surface.get_rect(center=(center_x + 20, item_y))
            self.screen.blit(desc_surface, desc_rect)
    
    # ==================== 资源路径规划UI功能 ====================
    
    def _show_resource_path_planning(self):
        """
        显示资源路径规划信息
        """
        if not self.game_started or self.game_completed:
            self.add_message("游戏未开始或已结束")
            return
        
        result = self.game_engine.find_optimal_resource_path()
        
        if result['success']:
            self.add_message(f"最优资源路径计算完成")
            self.add_message(f"路径长度: {len(result['path'])}步")
            self.add_message(f"收集资源: {len(result['resources_collected'])}个")
            
            # 保存路径用于显示
            self.optimal_path = result['path']
            self.show_optimal_path = True
        else:
            self.add_message(f"路径规划失败: {result['message']}")
    
    def _auto_navigate_to_nearest_resource(self):
        """
        自动导航到最近的资源
        """
        if not self.game_started or self.game_completed or self.paused:
            self.add_message("游戏未开始、已结束或已暂停")
            return
        
        result = self.game_engine.get_auto_navigation_to_nearest_resource()
        
        if result['success']:
            self.add_message(f"找到最近资源，距离{result['total_steps']}步")
            resource_type = result['target_resource']['type']
            resource_value = result['target_resource']['value']
            self.add_message(f"目标: {resource_type} (价值{resource_value})")
            
            # 执行自动导航
            nav_result = self.game_engine.execute_auto_navigation(result['steps'])
            if nav_result['success']:
                self.add_message(f"自动导航完成: {nav_result['executed_steps']}/{nav_result['total_steps']}步")
            else:
                self.add_message(f"导航失败: {nav_result['message']}")
        else:
            self.add_message(f"导航失败: {result['message']}")
    
    def _auto_navigate_to_exit(self):
        """
        自动导航到出口
        """
        if not self.game_started or self.game_completed or self.paused:
            self.add_message("游戏未开始、已结束或已暂停")
            return
        
        result = self.game_engine.get_auto_navigation_to_exit()
        
        if result['success']:
            self.add_message(f"找到出口路径，距离{result['total_steps']}步")
            
            # 执行自动导航
            nav_result = self.game_engine.execute_auto_navigation(result['steps'])
            if nav_result['success']:
                self.add_message(f"自动导航完成: {nav_result['executed_steps']}/{nav_result['total_steps']}步")
                # 检查是否到达出口
                if self.game_engine.player_pos == self.game_engine.exit_pos:
                    self.add_message("🎉 恭喜！你已到达出口，游戏结束！")
                    self.game_completed = True
            else:
                self.add_message(f"导航失败: {nav_result['message']}")
        else:
            self.add_message(f"导航失败: {result['message']}")
    
    def _show_path_alternatives(self):
        """
        显示多个路径方案
        """
        if not self.game_started or self.game_completed:
            self.add_message("游戏未开始或已结束")
            return
        
        alternatives = self.game_engine.get_resource_path_alternatives(3)
        
        if alternatives:
            # 存储路径方案用于可视化
            self.alternative_paths = alternatives
            self.show_alternative_paths = True
            
            self.add_message("=== 路径方案对比 ===")
            self.add_message("路径已在迷宫中显示，按V键切换显示")
            for i, alt in enumerate(alternatives, 1):
                if alt.get('success'):
                    name = alt.get('name', f'方案{i}')
                    value = alt.get('total_value', 0)
                    steps = alt.get('total_steps', len(alt.get('path', [])))
                    resources = len(alt.get('resources_collected', []))
                    
                    self.add_message(f"{i}. {name}")
                    self.add_message(f"   价值:{value} 步数:{steps} 资源:{resources}")
        else:
            self.add_message("无可用路径方案")
        
        # 注意：显示更新在主循环中统一处理
    
    def add_message(self, message: str):
        """
        添加消息
        
        Args:
            message: 消息内容
        """
        self.messages.append(message)
        if len(self.messages) > 20:  # 保留最近20条消息
            self.messages = self.messages[-20:]
        
        print(f"[游戏消息] {message}")  # 同时输出到控制台