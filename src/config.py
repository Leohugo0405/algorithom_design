#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏配置文件
定义游戏的基本参数和常量
"""

class Config:
    """
    游戏配置类
    """
    
    # 窗口设置
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    WINDOW_TITLE = "算法驱动的迷宫探险游戏"
    FPS = 60
    
    # 迷宫设置
    MIN_MAZE_SIZE = 7
    DEFAULT_MAZE_SIZE = 15
    MAX_MAZE_SIZE = 25
    CELL_SIZE = 40
    
    # 游戏元素符号
    WALL = '#'
    PATH = ' '
    START = 'S'
    EXIT = 'E'
    GOLD = 'G'
    TRAP = 'T'
    LOCKER = 'L'
    BOSS = 'B'
    PLAYER = 'P'
    
    # 颜色定义 (RGB)
    COLORS = {
        'BLACK': (0, 0, 0),
        'WHITE': (255, 255, 255),
        'GRAY': (128, 128, 128),
        'RED': (255, 0, 0),
        'GREEN': (0, 255, 0),
        'BLUE': (0, 0, 255),
        'LIGHT_BLUE': (173, 216, 230),
        'YELLOW': (255, 255, 0),
        'ORANGE': (255, 165, 0),
        'PURPLE': (128, 0, 128),
        'BROWN': (139, 69, 19),
        'GOLD': (255, 215, 0),
        'DARK_GREEN': (0, 100, 0),
        'DARK_RED': (139, 0, 0)
    }
    
    # 游戏元素颜色映射
    ELEMENT_COLORS = {
        WALL: COLORS['BLACK'],
        PATH: COLORS['WHITE'],
        START: COLORS['GREEN'],
        EXIT: COLORS['BLUE'],
        GOLD: COLORS['GOLD'],
        TRAP: COLORS['RED'],
        LOCKER: COLORS['PURPLE'],
        BOSS: COLORS['DARK_RED'],
        PLAYER: COLORS['ORANGE']
    }
    
    # 游戏参数
    PLAYER_VISION_RANGE = 3  # 玩家视野范围 (3x3)
    GOLD_VALUE = 5  # 金币价值
    TRAP_DAMAGE = -3  # 陷阱伤害
    
    # BOSS战斗参数
    BOSS_HP = 50  # BOSS血量
    BOSS_ATTACK_DAMAGE = 8  # BOSS攻击伤害

    # 玩家技能参数
    SKILLS = {
        'normal_attack': {
            'name': '普通攻击',
            'damage': 5,
            'cost': 0,
            'cooldown': 0
        },
        'special_attack': {
            'name': '强力一击',
            'damage': 12,
            'cost': 10,
            'cooldown': 2  # 冷却2个回合
        },
        'heal': {
            'name': '治疗',
            'heal_amount': 25,
            'cost': 15,
            'cooldown': 3
        }
    }
    
    # 密码锁参数
    LOCK_DIGITS = 3  # 密码位数
    
    # 多怪物战斗配置
    MONSTER_TYPES = {
        'goblin': {
            'name': '哥布林',
            'hp': 25,
            'attack': 6,
            'defense': 1
        },
        'orc': {
            'name': '兽人',
            'hp': 40,
            'attack': 10,
            'defense': 2
        },
        'skeleton': {
            'name': '骷髅战士',
            'hp': 30,
            'attack': 8,
            'defense': 0
        },
        'troll': {
            'name': '巨魔',
            'hp': 60,
            'attack': 12,
            'defense': 3
        }
    }
    
    # 多怪物战斗场景配置
    MULTI_BATTLE_SCENARIOS = {
        'easy': {
            'name': '简单战斗',
            'monsters': ['goblin', 'goblin']
        },
        'medium': {
            'name': '中等战斗', 
            'monsters': ['goblin', 'orc', 'skeleton']
        },
        'hard': {
            'name': '困难战斗',
            'monsters': ['orc', 'orc', 'troll']
        },
        'nightmare': {
            'name': '噩梦战斗',
            'monsters': ['skeleton', 'orc', 'troll', 'goblin']
        }
    }
    
    # 算法参数
    RESOURCE_DENSITY = 0.1  # 资源密度 (10%的通路包含资源)
    TRAP_DENSITY = 0.05  # 陷阱密度 (5%的通路包含陷阱)
    LOCKER_COUNT = 2  # 机关数量
    BOSS_COUNT = 1  # BOSS数量