#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏配置文件
定义游戏的基本参数和常量
"""

import json
import os

class Config:
    """
    游戏配置类
    """
    
    @classmethod
    def load_from_json(cls, json_file_path):
        """
        从JSON文件加载配置并更新SKILLS和MONSTER_TYPES
        
        Args:
            json_file_path (str): JSON配置文件路径
            
        JSON格式示例:
        {
            "B": [11, 13, 8, 17],  # boss血量列表
            "PlayerSkills": [[6, 2], [2, 0], [4, 1]],  # 技能配置 [伤害, 冷却]
            "min_turns": 13,
            "actions": [0, 2, 1, 2, 0, 2, 1, 0, 1, 2, 0, 1, 2]
        }
        """
        if not os.path.exists(json_file_path):
            print(f"配置文件不存在: {json_file_path}")
            return False
            
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新BOSS血量
            if 'B' in config_data and config_data['B']:
                boss_hp_list = config_data['B']
                # 更新默认BOSS血量为第一个值
                cls.BOSS_HP = boss_hp_list[0]
                
                # 如果有多个BOSS血量，完全重新构建MONSTER_TYPES
                if len(boss_hp_list) > 1:
                    # 为不同难度的BOSS创建配置，完全替换原有配置
                    new_monster_types = {}
                    for i, hp in enumerate(boss_hp_list):
                        new_monster_types[f'boss_{i}'] = {
                            'name': f'第{i+1}个BOSS', 
                            'hp': hp,
                            'attack': 10,  # 默认攻击力
                            'defense': 2   # 默认防御力
                        }
                    # 完全替换MONSTER_TYPES
                    cls.MONSTER_TYPES = new_monster_types
                else:
                    # 只有一个BOSS时，创建单个BOSS配置
                    cls.MONSTER_TYPES = {
                        'boss_0': {
                            'name': 'BOSS',
                            'hp': boss_hp_list[0],
                            'attack': 10,
                            'defense': 2
                        }
                    }
            
            # 更新玩家技能
            if 'PlayerSkills' in config_data and config_data['PlayerSkills']:
                player_skills = config_data['PlayerSkills']
                
                # 重新构建SKILLS字典
                new_skills = {}
                
                for i, skill in enumerate(player_skills):
                    new_skills[f'skill_{i}'] = {
                        'name': str(i),
                        'damage': skill[0],
                        'cost': 0,
                        'cooldown': skill[1] if len(skill) > 1 else 0
                    }
                # 更新技能配置
                cls.SKILLS = new_skills
            
            # 存储额外的配置信息
            if 'min_turns' in config_data:
                cls.MIN_TURNS = config_data['min_turns']
            
            if 'actions' in config_data:
                cls.ACTIONS_SEQUENCE = config_data['actions']
            
            print(f"成功从 {json_file_path} 加载配置")
            print(f"BOSS血量: {cls.BOSS_HP}")
            print(f"技能配置: {cls.SKILLS}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"JSON文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            return False
    
    @classmethod
    def save_to_json(cls, json_file_path):
        """
        将当前配置保存到JSON文件
        
        Args:
            json_file_path (str): 保存路径
        """
        try:
            # 提取BOSS血量
            boss_hp_list = [cls.BOSS_HP]
            
            # 从MONSTER_TYPES中提取BOSS血量
            for monster_type, config in cls.MONSTER_TYPES.items():
                if 'boss' in monster_type.lower():
                    boss_hp_list.append(config['hp'])
            
            # 提取技能配置
            player_skills = []
            for skill_name, skill_config in cls.SKILLS.items():
                player_skills.append([skill_config['damage'], skill_config['cooldown']])
            
            config_data = {
                'B': boss_hp_list[:4],  # 最多保存4个BOSS血量
                'PlayerSkills': player_skills,
                'min_turns': getattr(cls, 'MIN_TURNS', 13),
                'actions': getattr(cls, 'ACTIONS_SEQUENCE', [])
            }
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到 {json_file_path}")
            return True
            
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
            return False
    
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
    
    # 现代化颜色定义 (RGB) - 采用Material Design配色
    COLORS = {
        # 基础色彩 - 深色主题
        'BLACK': (18, 18, 18),          # 纯黑背景
        'WHITE': (255, 255, 255),       # 纯白文字
        'GRAY': (158, 158, 158),        # 中性灰
        'LIGHT_GRAY': (245, 245, 245),  # 浅灰
        'DARK_GRAY': (33, 33, 33),      # 深灰面板
        'MEDIUM_GRAY': (66, 66, 66),    # 中等灰
        
        # 主题色彩 - 现代渐变
        'PRIMARY': (64, 196, 255),      # 科技蓝
        'PRIMARY_DARK': (33, 150, 243), # 深蓝
        'SECONDARY': (158, 158, 158),   # 次要灰色
        'SUCCESS': (76, 175, 80),       # 成功绿
        'DANGER': (244, 67, 54),        # 危险红
        'WARNING': (255, 152, 0),       # 警告橙
        'INFO': (0, 188, 212),          # 信息青
        
        # 游戏专用色彩 - 高对比度
        'RED': (244, 67, 54),           # 鲜艳红
        'GREEN': (76, 175, 80),         # 鲜艳绿
        'BLUE': (33, 150, 243),         # 鲜艳蓝
        'LIGHT_BLUE': (3, 169, 244),    # 亮蓝
        'YELLOW': (255, 235, 59),       # 鲜艳黄
        'ORANGE': (255, 152, 0),        # 鲜艳橙
        'PURPLE': (156, 39, 176),       # 鲜艳紫
        'BROWN': (121, 85, 72),         # 现代棕
        'GOLD': (255, 193, 7),          # 金色
        'DARK_GREEN': (27, 94, 32),     # 深绿
        'DARK_RED': (183, 28, 28),      # 深红
        'CYAN': (0, 188, 212),          # 青色
        'PINK': (233, 30, 99),          # 粉色
        'LIME': (139, 195, 74),         # 青柠色
        'INDIGO': (63, 81, 181),        # 靛蓝
        'TEAL': (0, 150, 136),          # 蓝绿色
        
        # 渐变色彩
        'GRADIENT_START': (64, 196, 255),   # 渐变起始 - 科技蓝
        'GRADIENT_MID': (100, 181, 246),    # 渐变中间
        'GRADIENT_END': (156, 39, 176),     # 渐变结束 - 紫色
        
        # UI专用色彩
        'PANEL_BG': (33, 33, 33),           # 面板背景
        'PANEL_BORDER': (66, 66, 66),       # 面板边框
        'BUTTON_BG': (66, 66, 66),          # 按钮背景
        'BUTTON_HOVER': (97, 97, 97),       # 按钮悬停
        'BUTTON_ACTIVE': (33, 150, 243),    # 按钮激活
        'TEXT_PRIMARY': (255, 255, 255),    # 主要文字
        'TEXT_SECONDARY': (158, 158, 158),  # 次要文字
        'TEXT_DISABLED': (97, 97, 97),      # 禁用文字
        'ACCENT': (255, 64, 129),           # 强调色
        'HIGHLIGHT': (255, 235, 59),        # 高亮色
        
        # 半透明色彩
        'OVERLAY': (0, 0, 0, 180),          # 半透明遮罩
        'PANEL_OVERLAY': (33, 33, 33, 240), # 面板半透明背景
        'GLOW': (64, 196, 255, 100),        # 发光效果
        'SHADOW': (20, 20, 20),             # 阴影效果
        'BORDER': (97, 97, 97),             # 边框颜色
        'LIGHT_GREEN': (129, 199, 132)      # 浅绿色
    }
    
    # 游戏元素颜色映射
    ELEMENT_COLORS = {
        WALL: COLORS['DARK_GRAY'],
        PATH: COLORS['WHITE'],
        START: COLORS['SUCCESS'],
        EXIT: COLORS['PRIMARY'],
        GOLD: COLORS['GOLD'],
        TRAP: COLORS['DANGER'],
        LOCKER: COLORS['PURPLE'],
        BOSS: COLORS['DARK_RED'],
        PLAYER: COLORS['ACCENT']
    }
    
    # 游戏参数
    PLAYER_VISION_RANGE = 1  # 玩家视野范围 (3x3)
    RESOURCE_VALUE = 50  # 金币资源价值（踩到金币+5）
    TRAP_RESOURCE_COST = 30  # 陷阱资源损失（踩到陷阱-3）
    
    # BOSS战斗参数
    BOSS_HP = 50  # BOSS血量

    # 玩家技能参数（移除血量相关技能）
    SKILLS = {
        'normal_attack': {
            'name': '0',
            'damage': 5,
            'cost': 0,
            'cooldown': 0
        },
        'special_attack': {
            'name': '1',
            'damage': 10,
            'cost': 0, 
            'cooldown': 2  # 冷却2个回合
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