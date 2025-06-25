#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏UI界面模块
提供可视化的游戏界面和交互
"""

import pygame
import sys
from typing import Dict, List, Tuple, Optional
from src.config import Config
from src.game_engine import GameEngine
from src.ui.battle_ui import BattleUI
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
        self.auto_play = False
        self.auto_play_speed = 500  # 毫秒
        self.last_auto_step = 0
        self.game_completed = False  # 游戏是否已结束

        # 显示面板
        self.show_statistics = True
        self.show_controls = True
        self.show_algorithm_info = False
        
        # 路径显示
        self.optimal_path = []
        self.greedy_path = []
        
        # 消息系统
        self.messages = []
        self.max_messages = 5
        
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
        
        # 初始化字体
        try:
            self.font = pygame.font.Font('font/msyh.ttc', 18)
            self.small_font = pygame.font.Font('font/msyh.ttc', 12)
        except:
            self.font = pygame.font.SysFont('Arial', 18)
            self.small_font = pygame.font.SysFont('Arial', 12)
    
    def run(self):
        """
        运行游戏主循环
        """
        # 初始化游戏
        init_result = self.game_engine.initialize_game()
        if init_result['success']:
            self.add_message("游戏初始化成功！")
            self.add_message(f"迷宫大小: {init_result['maze_size']}x{init_result['maze_size']}")
        else:
            self.add_message("游戏初始化失败！")
            return
        
        # 主游戏循环
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # 处理事件
            self._handle_events()
            
            # 自动游戏逻辑
            if self.auto_play and not self.paused:
                if current_time - self.last_auto_step > self.auto_play_speed:
                    self._auto_play_step()
                    self.last_auto_step = current_time
            
            # 渲染游戏
            self._render()
            
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
    
    def _handle_keydown(self, key):
        """
        处理键盘按下事件
        
        Args:
            key: 按下的键
        """
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            self.add_message("游戏暂停" if self.paused else "游戏继续")
        
        elif key == pygame.K_r:
            # 重新开始游戏
            init_result = self.game_engine.initialize_game()
            if init_result['success']:
                self.add_message("游戏重新开始！")
                self.optimal_path = []
                self.greedy_path = []
                self.game_completed = False  # 重置游戏结束标志

            
        elif key == pygame.K_a:
            # 切换自动游戏
            self.auto_play = not self.auto_play
            self.add_message("自动游戏开启" if self.auto_play else "自动游戏关闭")
        
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
        
        elif key == pygame.K_c:
            # 比较路径策略
            self._compare_path_strategies()
        
        elif not self.auto_play and not self.paused and not self.game_completed:

            # 手动移动控制
            direction = None
            if key == pygame.K_UP or key == pygame.K_w:
                direction = 'up'
            elif key == pygame.K_DOWN or key == pygame.K_s:
                direction = 'down'
            elif key == pygame.K_LEFT or key == pygame.K_a:
                direction = 'left'
            elif key == pygame.K_RIGHT or key == pygame.K_d:
                direction = 'right'
            
            if direction:
                prev_pos = self.game_engine.player_pos
                result = self.game_engine.move_player(direction)
                if result['success']:
                    interaction = result.get('interaction', {})
                    if interaction.get('message'):
                        self.add_message(interaction['message'])
                    # 删除已拾取金币格子
                    pos = self.game_engine.player_pos
                    i, j = pos
                    if self.game_engine.maze[i][j] == 'L':
                        self.add_message("触发解谜挑战...")
                        puzzle_result = self.game_engine.solve_puzzle()  # 调用解谜逻辑
                        if puzzle_result:
                            self.add_message("解谜成功！")
                            self.game_engine.maze[i][j] = Config.PATH  # 转为空地
                        else:
                            self.add_message("解谜失败，返回原位置。")
                            self.game_engine.player_pos = prev_pos  # 回退
                            return  # 中断处理
                    # 检查是否触发陷阱
                    if self.game_engine.maze[i][j] == 'T':
                        self.add_message("⚠️ 你触发了一个陷阱！")
                        self._play_trap_animation()  # 显示动画提示
                        self.game_engine.player_hp -= 10  # 扣除生命值（可自定义）
                        self.add_message("生命值 -10")
                        self.game_engine.maze[i][j] = Config.PATH  # 陷阱只触发一次，设为空地

                    if self.game_engine.maze[i][j] == 'E':
                        self.add_message("🎉 恭喜！你已到达出口，游戏结束！")
                        self.game_completed = True  # ✅ 标记游戏结束
                        return  # 停止后续处理
                    if self.game_engine.maze[i][j] == Config.GOLD:
                        self.game_engine.maze[i][j] = Config.PATH  # 将金币格子改为空白路径

                    # 检查是否遇到Boss
                    if interaction.get('type') == 'boss':
                        self._handle_boss_encounter(interaction)
                    
                    # 检查是否遇到密码锁
                    elif interaction.get('type') == 'puzzle':
                        self._handle_lock_encounter(interaction)
                else:
                    self.add_message(result['message'])
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """
        处理鼠标点击事件
        
        Args:
            pos: 鼠标点击位置
        """
        # 可以添加鼠标交互逻辑，比如点击迷宫格子
        pass
    
    def _auto_play_step(self):
        """
        执行自动游戏一步
        """
        # AI遇到Boss时，直接在引擎层面解决战斗，不打开UI
        game_state = self.game_engine.get_game_state()
        if game_state.get('active_battle'):
            self.add_message("AI遇到Boss，自动战斗...")
            battle_result = self.game_engine.fight_boss('optimal') # 使用旧的快速战斗方法
            if battle_result['success']:
                self.add_message(f"AI战斗胜利: {battle_result['message']}")
            else:
                self.add_message(f"AI战斗失败: {battle_result['message']}")
            return # 当前步骤只处理战斗

        result = self.game_engine.auto_play_step()
        
        if result['success']:
            if result.get('message'):
                self.add_message(result['message'])
            
            if result.get('game_completed'):
                self.auto_play = False
                self.add_message("游戏完成！自动游戏停止")
        else:
            self.add_message(f"自动游戏错误: {result['message']}")
            self.auto_play = False
    def _play_trap_animation(self):
    
    #显示陷阱触发动画（例如红色闪烁）
    
        for _ in range(3):
            self.screen.fill((255, 0, 0))  # 红色闪屏
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
            self.add_message(f"贪心路径计算完成，价值: {result['total_value']}")
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
            self.add_message(f"DP价值: {comparison['dp_path']['value']}, 贪心价值: {comparison['greedy_path']['details']['total_value']}")
            self.add_message(f"价值提升: {improvement['value_diff']}")
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
        lock_ui = LockUI(self.game_engine, lock_data, self.screen)
        puzzle_result = lock_ui.run()
        
        # 处理解谜结果
        if puzzle_result['success']:
            self.add_message("密码锁解开成功！")
            # 在游戏引擎中标记谜题已解决
            if hasattr(self.game_engine, 'active_puzzle') and self.game_engine.active_puzzle:
                self.game_engine.solved_puzzles.add(self.game_engine.active_puzzle['position'])
                reward = 20
                self.game_engine.player_resources += reward
                self.game_engine.total_value_collected += reward
                self.add_message(f"获得{reward}资源奖励！")
                self.game_engine.active_puzzle = None
        else:
            self.add_message("解谜失败或取消")
        
        # 恢复主游戏窗口
        pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        pygame.display.set_caption(Config.WINDOW_TITLE)

    def _handle_boss_encounter(self, interaction: Dict):
        """
        处理Boss遭遇事件
        
        Args:
            interaction: 交互信息
        """
        self.add_message("进入Boss战斗界面...")
        
        # 创建Boss数据
        boss_data = {
            'boss_hp': interaction.get('boss_hp', Config.BOSS_HP),
            'position': self.game_engine.player_pos
        }
        
        # 创建并运行战斗UI
        battle_ui = BattleUI(self.game_engine, boss_data)
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
            self.add_message(f"Boss战斗失败: {message}")
        else:
            self.add_message(f"Boss战斗结束: {message}")
        
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
                color = Config.ELEMENT_COLORS.get(cell, Config.COLORS['WHITE'])
                
                # 绘制格子
                pygame.draw.rect(self.screen, color, (x, y, cell_size, cell_size))
                
                # 绘制边框
                pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, cell_size, cell_size), 1)
                
                # 绘制元素符号
                if cell != Config.WALL and cell != Config.PATH:
                    text_surface = self.small_font.render(cell, True, Config.COLORS['WHITE'])
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
        
        # 绘制玩家（圆形）
        pygame.draw.circle(self.screen, Config.COLORS['ORANGE'], (x, y), cell_size // 3)
        pygame.draw.circle(self.screen, Config.COLORS['BLACK'], (x, y), cell_size // 3, 2)
    
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
        
        # 面板背景
        panel_height = 180
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("游戏统计", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 统计信息
        stats_text = [
            f"位置: {game_state['player_pos']}",
            f"移动次数: {game_state['moves_count']}",
            f"资源: {game_state['player_resources']}",
            f"生命值: {game_state['player_hp']}",
            f"收集价值: {game_state['total_value_collected']}",
            f"收集物品: {game_state['collected_items']}",
            f"解谜数: {game_state['solved_puzzles']}",
            f"击败BOSS: {game_state['defeated_bosses']}"
        ]
        
        for i, text in enumerate(stats_text):
            text_surface = self.small_font.render(text, True, Config.COLORS['WHITE'])
            self.screen.blit(text_surface, (x + 10, y + 35 + i * 18))
        
        return y + panel_height + 10
    
    def _render_controls_panel(self, x: int, y: int) -> int:
        """
        渲染控制帮助面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景
        panel_height = 200
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("控制帮助", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 控制说明
        controls_text = [
            "WASD/方向键: 移动",
            "A: 自动游戏开/关",
            "O: 显示最优路径",
            "G: 显示贪心路径",
            "C: 比较路径策略",
            "R: 重新开始",
            "SPACE: 暂停/继续",
            "S: 统计信息开/关",
            "H: 帮助开/关",
            "I: 算法信息开/关",
            "ESC: 退出游戏"
        ]
        
        for i, text in enumerate(controls_text):
            text_surface = self.small_font.render(text, True, Config.COLORS['WHITE'])
            self.screen.blit(text_surface, (x + 10, y + 35 + i * 15))
        
        return y + panel_height + 10
    
    def _render_algorithm_panel(self, x: int, y: int) -> int:
        """
        渲染算法信息面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景
        panel_height = 150
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("算法信息", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 算法说明
        algorithm_text = [
            "分治法: 迷宫生成",
            "动态规划: 最优路径",
            "贪心算法: 实时策略",
            "回溯法: 解谜破解",
            "分支限界: BOSS战斗",
            "",
            "蓝线: 动态规划路径",
            "绿线: 贪心策略路径"
        ]
        
        for i, text in enumerate(algorithm_text):
            if text:  # 跳过空行
                text_surface = self.small_font.render(text, True, Config.COLORS['WHITE'])
                self.screen.blit(text_surface, (x + 10, y + 35 + i * 15))
        
        return y + panel_height + 10
    
    def _render_messages_panel(self, x: int, y: int):
        """
        渲染消息面板
        
        Args:
            x, y: 面板位置
        """
        # 面板背景
        panel_height = 120
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("消息", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 显示最近的消息
        for i, message in enumerate(self.messages[-self.max_messages:]):
            text_surface = self.small_font.render(message, True, Config.COLORS['WHITE'])
            self.screen.blit(text_surface, (x + 10, y + 35 + i * 15))
    
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