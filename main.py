#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算法驱动的迷宫探险游戏 - 主程序
"""

import pygame
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.game_engine import GameEngine
from src.ui.game_ui import GameUI
from src.config import Config

def main():
    """
    游戏主函数
    """
    # 初始化pygame
    pygame.init()
    
    try:
        # 创建游戏引擎
        game_engine = GameEngine()
        
        # 创建游戏UI
        game_ui = GameUI(game_engine)
        
        # 运行游戏
        game_ui.run()
        
    except Exception as e:
        print(f"游戏运行出错: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()