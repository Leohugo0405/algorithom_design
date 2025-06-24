#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss战斗功能测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.game_engine import GameEngine
from src.config import Config

def test_boss_battle():
    """
    测试Boss战斗功能
    """
    print("=== Boss战斗功能测试 ===")
    
    # 创建游戏引擎
    game_engine = GameEngine(maze_size=10)
    
    # 初始化游戏
    init_result = game_engine.initialize_game()
    if not init_result['success']:
        print("游戏初始化失败！")
        return
    
    print(f"游戏初始化成功，迷宫大小: {init_result['maze_size']}x{init_result['maze_size']}")
    
    # 模拟遇到Boss
    print("\n--- 模拟遇到Boss ---")
    game_engine.active_battle = {
        'position': (5, 5),
        'boss_hp': Config.BOSS_HP,
        'type': 'boss'
    }
    
    # 测试最优策略战斗
    print("\n--- 测试最优策略战斗 ---")
    result = game_engine.fight_boss('optimal')
    
    if result['success']:
        print(f"战斗胜利！")
        print(f"策略: {result['strategy']}")
        print(f"回合数: {result['rounds_used']}")
        print(f"奖励: {result['reward']}")
        print(f"统计信息: {result['stats']}")
        
        if 'battle_log' in result:
            print("\n战斗日志:")
            for log in result['battle_log'][:5]:  # 只显示前5条
                print(f"  {log}")
    else:
        print(f"战斗失败: {result['message']}")
    
    # 测试随机策略战斗
    print("\n--- 测试随机策略战斗 ---")
    game_engine.active_battle = {
        'position': (6, 6),
        'boss_hp': Config.BOSS_HP,
        'type': 'boss'
    }
    
    result = game_engine.fight_boss('random')
    
    if result['success']:
        print(f"战斗胜利！")
        print(f"策略: {result['strategy']}")
        print(f"回合数: {result['rounds_used']}")
        print(f"奖励: {result['reward']}")
    else:
        print(f"战斗失败: {result['message']}")
    
    # 显示游戏统计
    print("\n--- 游戏统计 ---")
    stats = game_engine.get_game_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_boss_battle() 