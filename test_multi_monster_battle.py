#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多怪物战斗系统测试
演示多怪物战斗功能，包括目标选择和战斗策略
"""

import pygame
import sys
from src.game_engine import GameEngine
from src.ui.multi_battle_ui import MultiMonsterBattleUI
from src.config import Config

def test_multi_monster_battle_console():
    """
    控制台测试多怪物战斗系统
    """
    print("=== 多怪物战斗系统控制台测试 ===")
    
    # 初始化游戏引擎
    engine = GameEngine()
    engine.initialize_game()
    
    # 显示可用的战斗场景
    print("\n可用的战斗场景:")
    for scenario_name, scenario_info in Config.MULTI_BATTLE_SCENARIOS.items():
        monsters = [Config.MONSTER_TYPES[m]['name'] for m in scenario_info['monsters']]
        print(f"  {scenario_name}: {scenario_info['name']} - {', '.join(monsters)}")
    
    # 选择战斗场景
    scenario = input("\n请选择战斗场景 (easy/medium/hard/nightmare): ").strip()
    if scenario not in Config.MULTI_BATTLE_SCENARIOS:
        scenario = 'medium'
        print(f"无效选择，使用默认场景: {scenario}")
    
    # 开始战斗
    result = engine.start_multi_monster_battle(scenario)
    if not result['success']:
        print(f"战斗开始失败: {result['message']}")
        return
    
    print(f"\n{result['message']}")
    print(f"怪物列表: {', '.join(result['monsters'])}")
    
    # 战斗循环
    turn = 1
    while engine.active_multi_battle and engine.active_multi_battle.battle_active:
        print(f"\n=== 第 {turn} 回合 ===")
        
        # 显示当前状态
        battle_state = engine.get_multi_battle_state()
        print(f"玩家状态: HP {battle_state['player_hp']}/{battle_state['player_max_hp']}, 资源 {battle_state['player_resources']}")
        
        print("\n怪物状态:")
        alive_monsters = []
        for monster in battle_state['monsters']:
            status = "存活" if monster['alive'] else "已死亡"
            print(f"  {monster['id']}: {monster['name']} - HP {monster['current_hp']}/{monster['max_hp']} ({status})")
            if monster['alive']:
                alive_monsters.append(monster)
        
        if not alive_monsters:
            print("所有怪物都被击败了！")
            break
        
        # 显示可用技能
        print("\n可用技能:")
        available_skills = battle_state['available_skills']
        skill_list = []
        for skill_name, skill_info in Config.SKILLS.items():
            status = "可用" if available_skills[skill_name] else "不可用"
            cost = skill_info.get('cost', 0)
            cooldown = battle_state['skill_cooldowns'].get(skill_name, 0)
            cooldown_text = f" (冷却: {cooldown})" if cooldown > 0 else ""
            print(f"  {skill_name}: {skill_info['name']} - 消耗 {cost} 资源 ({status}){cooldown_text}")
            if available_skills[skill_name]:
                skill_list.append(skill_name)
        
        if not skill_list:
            print("没有可用技能！")
            break
        
        # 选择技能
        skill_choice = input(f"\n请选择技能 ({'/'.join(skill_list)}): ").strip()
        if skill_choice not in skill_list:
            print("无效的技能选择！")
            continue
        
        target_id = None
        skill_info = Config.SKILLS[skill_choice]
        
        # 如果是攻击技能，需要选择目标
        if 'damage' in skill_info:
            print("\n选择攻击目标:")
            for monster in alive_monsters:
                print(f"  {monster['id']}: {monster['name']} (HP: {monster['current_hp']}/{monster['max_hp']})")
            
            # 显示AI建议
            suggestion = engine.get_multi_battle_target_suggestion()
            if suggestion is not None:
                suggested_monster = next(m for m in alive_monsters if m['id'] == suggestion)
                print(f"\nAI建议攻击: {suggestion} ({suggested_monster['name']})")
            
            try:
                target_input = input("请输入目标怪物ID: ").strip()
                target_id = int(target_input)
                if target_id not in [m['id'] for m in alive_monsters]:
                    print("无效的目标ID！")
                    continue
            except ValueError:
                print("请输入有效的数字ID！")
                continue
        
        # 执行回合
        turn_result = engine.execute_multi_battle_turn(skill_choice, target_id)
        
        if not turn_result['success']:
            print(f"回合执行失败: {turn_result['message']}")
            continue
        
        # 显示回合结果
        print(f"\n你使用了 {turn_result['skill_name']}")
        
        if turn_result['damage_dealt'] > 0:
            target_info = turn_result['target_monster']
            print(f"对 {target_info['name']} 造成了 {turn_result['damage_dealt']} 点伤害")
            print(f"{target_info['name']} 剩余HP: {target_info['remaining_hp']}")
            
            if turn_result['monster_defeated']:
                print(f"{target_info['name']} 被击败了！")
        
        if turn_result['heal_amount'] > 0:
            print(f"你恢复了 {turn_result['heal_amount']} 点生命值")
        
        # 显示怪物行动
        if 'monster_actions' in turn_result:
            print("\n怪物行动:")
            for action in turn_result['monster_actions']:
                print(f"  {action['monster_name']} 攻击了你，造成 {action['damage']} 点伤害")
        
        # 检查战斗结果
        if 'battle_result' in turn_result:
            battle_result = turn_result['battle_result']
            print(f"\n{battle_result['message']}")
            
            if battle_result['status'] == 'victory':
                print(f"战斗用时: {battle_result['turns_used']} 回合")
                print(f"获得奖励: {battle_result['reward']} 资源")
            
            break
        
        turn += 1
        
        # 防止无限循环
        if turn > 50:
            print("\n战斗时间过长，自动结束")
            break
    
    print("\n=== 战斗结束 ===")

def test_multi_monster_battle_ui():
    """
    图形界面测试多怪物战斗系统
    """
    print("=== 多怪物战斗系统图形界面测试 ===")
    
    # 初始化pygame
    pygame.init()
    
    try:
        # 显示场景选择
        print("\n可用的战斗场景:")
        scenarios = list(Config.MULTI_BATTLE_SCENARIOS.keys())
        for i, scenario_name in enumerate(scenarios):
            scenario_info = Config.MULTI_BATTLE_SCENARIOS[scenario_name]
            monsters = [Config.MONSTER_TYPES[m]['name'] for m in scenario_info['monsters']]
            print(f"  {i+1}. {scenario_info['name']} - {', '.join(monsters)}")
        
        choice = input(f"\n请选择场景 (1-{len(scenarios)}) 或直接按回车使用默认: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(scenarios):
            scenario = scenarios[int(choice) - 1]
        else:
            scenario = 'medium'
        
        print(f"选择的场景: {Config.MULTI_BATTLE_SCENARIOS[scenario]['name']}")
        
        # 创建并运行战斗UI
        battle_ui = MultiMonsterBattleUI(scenario)
        result = battle_ui.run()
        
        # 显示结果
        print(f"\n战斗结果: {result}")
        
    except Exception as e:
        print(f"图形界面测试失败: {e}")
        print("请确保pygame已正确安装并且系统支持图形界面")
    
    finally:
        pygame.quit()

def main():
    """
    主函数
    """
    print("多怪物战斗系统测试")
    print("1. 控制台测试")
    print("2. 图形界面测试")
    
    choice = input("\n请选择测试方式 (1/2): ").strip()
    
    if choice == '1':
        test_multi_monster_battle_console()
    elif choice == '2':
        test_multi_monster_battle_ui()
    else:
        print("无效选择，运行控制台测试")
        test_multi_monster_battle_console()

if __name__ == '__main__':
    main()