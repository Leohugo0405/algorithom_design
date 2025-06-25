# -*- coding: utf-8 -*-
"""
BOSS战策略优化示例
使用分支限界算法寻找最小回合数的技能序列
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.algorithms.boss_strategy import BossStrategy
from src.config import Config

def demonstrate_boss_strategy():
    """
    演示BOSS战策略优化
    """
    print("=== BOSS战策略优化演示 ===")
    print("使用分支限界算法寻找最小回合数的技能序列")
    print()
    
    # 设置战斗参数
    boss_hp = 50
    player_resources = 100
    max_rounds = 15
    
    print(f"战斗设置:")
    print(f"- BOSS血量: {boss_hp}")
    print(f"- 玩家资源: {player_resources}")
    print(f"- 最大回合数: {max_rounds}")
    print()
    
    print("可用技能:")
    for skill_name, skill_info in Config.SKILLS.items():
        print(f"- {skill_info['name']}: 伤害{skill_info['damage']}, 冷却{skill_info['cooldown']}回合")
    print()
    
    # 创建策略优化器
    boss_strategy = BossStrategy(boss_hp=boss_hp, player_resources=player_resources)
    
    print("正在使用分支限界算法寻找最优策略...")
    
    # 寻找最优策略
    optimal_sequence, optimal_rounds, stats = boss_strategy.find_optimal_strategy(max_rounds=max_rounds)
    
    print("\n=== 算法执行统计 ===")
    print(f"探索节点数: {stats['nodes_explored']}")
    print(f"剪枝节点数: {stats['nodes_pruned']}")
    print(f"缓存状态数: {stats['states_cached']}")
    print(f"最优回合数: {stats['optimal_rounds']}")
    
    if optimal_sequence:
        print("\n=== 最优策略 ===")
        print(f"最少回合数: {optimal_rounds}")
        print("技能序列:")
        for i, skill in enumerate(optimal_sequence, 1):
            skill_info = Config.SKILLS[skill]
            print(f"  回合{i}: {skill_info['name']} (伤害: {skill_info['damage']})")
        
        # 模拟战斗过程
        print("\n=== 战斗模拟 ===")
        battle_result = boss_strategy.simulate_battle(optimal_sequence)
        
        if battle_result['success']:
            print("战斗成功！")
            print("\n详细战斗过程:")
            for log in battle_result['battle_log']:
                print(f"回合{log['round']}: 使用{log['skill']}, 造成{log['damage']}伤害, BOSS剩余血量{log['boss_hp']}")
        else:
            print(f"战斗失败: {battle_result['reason']}")
    else:
        print("\n未找到可行的获胜策略！")
        print("可能原因:")
        print("- BOSS血量过高")
        print("- 最大回合数限制过低")
    
    print("\n=== 算法特点 ===")
    print("1. 节点状态包括: BOSS血量、已用回合数、技能冷却状态")
    print("2. 代价函数: f(n) = 已用回合数 + 预估剩余回合数")
    print("3. 剪枝策略: 丢弃代价超过当前最优解的节点")
    print("4. 启发式函数: 基于平均伤害的乐观估计")

def compare_different_scenarios():
    """
    比较不同场景下的策略
    """
    print("\n\n=== 不同场景比较 ===")
    
    scenarios = [
        {"name": "简单BOSS", "boss_hp": 30, "max_rounds": 10},
        {"name": "中等BOSS", "boss_hp": 50, "max_rounds": 15},
        {"name": "困难BOSS", "boss_hp": 80, "max_rounds": 20}
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"BOSS血量: {scenario['boss_hp']}, 最大回合: {scenario['max_rounds']}")
        
        boss_strategy = BossStrategy(boss_hp=scenario['boss_hp'])
        optimal_sequence, optimal_rounds, stats = boss_strategy.find_optimal_strategy(
            max_rounds=scenario['max_rounds']
        )
        
        if optimal_sequence:
            print(f"最优回合数: {optimal_rounds}")
            print(f"探索节点: {stats['nodes_explored']}, 剪枝节点: {stats['nodes_pruned']}")
            
            # 分析策略效率
            efficiency = boss_strategy.analyze_strategy_efficiency(optimal_sequence)
            print(f"平均每回合伤害: {efficiency['damage_per_round']:.1f}")
        else:
            print("无法在限定回合内击败BOSS")

if __name__ == "__main__":
    demonstrate_boss_strategy()
    compare_different_scenarios()