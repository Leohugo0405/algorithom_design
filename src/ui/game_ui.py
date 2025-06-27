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
                            self.add_message(f"总价值获得: {pickup_result['total_value_gained']}")
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
                    # 删除已拾取金币格子
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
                        self.game_engine.maze[i][j] = Config.PATH  # 将金币格子改为空白路径

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
                self.game_engine.total_value_collected += reward
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
        
        # 绘制图例背景
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], 
                        (legend_x, legend_y, legend_width, legend_height))
        pygame.draw.rect(self.screen, Config.COLORS['WHITE'], 
                        (legend_x, legend_y, legend_width, legend_height), 2)
        
        # 绘制标题
        title = self.font.render("路径方案图例", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (legend_x + 10, legend_y + 5))
        
        # 绘制每个路径的图例
        path_colors = [
            (Config.COLORS['BLUE'], "蓝色"),
            (Config.COLORS['GREEN'], "绿色"),
            (Config.COLORS['RED'], "红色"),
            (Config.COLORS['PURPLE'], "紫色"),
            (Config.COLORS['ORANGE'], "橙色"),
        ]
        
        for i, alt in enumerate(self.alternative_paths[:5]):  # 最多显示5个
            if not alt.get('success'):
                continue
            
            y_offset = legend_y + 30 + i * 25
            
            # 绘制颜色线条
            if i < len(path_colors):
                color, color_name = path_colors[i]
                pygame.draw.line(self.screen, color, 
                               (legend_x + 10, y_offset + 8), 
                               (legend_x + 30, y_offset + 8), 3)
            
            # 绘制路径信息
            name = alt.get('name', f'方案{i+1}')
            value = alt.get('total_value', 0)
            text = f"{name} (价值:{value})"
            text_surface = self.small_font.render(text, True, Config.COLORS['WHITE'])
            self.screen.blit(text_surface, (legend_x + 40, y_offset))
    
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
        
        # 面板背景
        panel_height = 180
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("游戏统计", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 获取自动拾取状态
        auto_pickup_status = self.game_engine.get_auto_pickup_status()
        
        # 统计信息（移除生命值显示）
        stats_text = [
            f"位置: {game_state['player_pos']}",
            f"移动次数: {game_state['moves_count']}",
            f"资源: {game_state['player_resources']}",
            f"收集价值: {game_state['total_value_collected']}",
            f"收集物品: {game_state['collected_items']}",
            f"解谜数: {game_state['solved_puzzles']}",
            f"击败BOSS: {game_state['defeated_bosses']}",
            f"自动拾取: {'开启' if auto_pickup_status['enabled'] else '关闭'}"
        ]
        
        for i, text in enumerate(stats_text):
            text_surface = self.small_font.render(text, True, Config.COLORS['WHITE'])
            self.screen.blit(text_surface, (x + 10, y + 35 + i * 18))
        
        return y + panel_height + 10
    
    def _render_interaction_panel(self, x: int, y: int) -> int:
        """
        渲染交互提示面板
        
        Args:
            x, y: 面板位置
        
        Returns:
            int: 下一个面板的y坐标
        """
        # 面板背景
        panel_height = 80
        pygame.draw.rect(self.screen, Config.COLORS['YELLOW'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("可交互内容", True, Config.COLORS['BLACK'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 交互提示
        interaction = self.game_engine.pending_interaction
        if interaction['type'] == 'puzzle':
            hint_text = "密码锁 - 按Enter键解谜"
        elif interaction['type'] == 'multi_monster_battle':
            hint_text = "怪物群 - 按Enter键战斗"
        else:
            hint_text = "未知内容 - 按Enter键交互"
        
        hint_surface = self.small_font.render(hint_text, True, Config.COLORS['BLACK'])
        self.screen.blit(hint_surface, (x + 10, y + 40))
        
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
        panel_height = 180
        pygame.draw.rect(self.screen, Config.COLORS['GRAY'], (x, y, 300, panel_height))
        pygame.draw.rect(self.screen, Config.COLORS['BLACK'], (x, y, 300, panel_height), 2)
        
        # 标题
        title = self.font.render("控制帮助", True, Config.COLORS['WHITE'])
        self.screen.blit(title, (x + 10, y + 10))
        
        # 控制说明
        controls_text = [
            "WASD/方向键: 移动",
            "ENTER: 交互",
            "A: 自动拾取",
            "M: 多路径方案",
            "V: 切换路径显示",
            "P: 资源路径规划",
            "C: 比较路径策略",
            "R: 重新开始",
            "SPACE: 暂停/继续",
            "H: 帮助开/关",
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
    
    def _draw_settings_screen(self):
        """
        绘制设置界面
        """
        # 清空屏幕
        self.screen.fill(Config.COLORS['BLACK'])
        
        # 标题
        title = self.font.render("迷宫探险游戏 - 设置", True, Config.COLORS['WHITE'])
        title_rect = title.get_rect(center=(Config.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # 迷宫大小设置
        size_text = self.font.render(f"迷宫大小: {self.selected_maze_size} x {self.selected_maze_size}", True, Config.COLORS['WHITE'])
        size_rect = size_text.get_rect(center=(Config.WINDOW_WIDTH // 2, 200))
        self.screen.blit(size_text, size_rect)
        
        # 大小范围提示
        range_text = self.small_font.render(f"范围: {Config.MIN_MAZE_SIZE} - {Config.MAX_MAZE_SIZE}", True, Config.COLORS['GRAY'])
        range_rect = range_text.get_rect(center=(Config.WINDOW_WIDTH // 2, 230))
        self.screen.blit(range_text, range_rect)
        
        # 控制说明
        controls = [
            "↑/↓ 键: 调整迷宫大小",
            "回车键: 开始游戏",
            "ESC键: 退出游戏"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, Config.COLORS['WHITE'])
            control_rect = control_text.get_rect(center=(Config.WINDOW_WIDTH // 2, 300 + i * 30))
            self.screen.blit(control_text, control_rect)
        
        # 游戏说明
        description = [
            "游戏目标: 从起点(S)到达终点(E)",
            "收集金币(G), 避开陷阱(T)",
            "解开机关(L), 击败BOSS(B)"
        ]
        
        for i, desc in enumerate(description):
            desc_text = self.small_font.render(desc, True, Config.COLORS['YELLOW'])
            desc_rect = desc_text.get_rect(center=(Config.WINDOW_WIDTH // 2, 450 + i * 25))
            self.screen.blit(desc_text, desc_rect)
    
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
            self.add_message(f"最优资源路径: 总价值{result['total_value']}")
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