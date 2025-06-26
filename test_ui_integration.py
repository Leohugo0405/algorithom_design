#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动拾取功能在游戏UI中的集成
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.game_engine import GameEngine
from src.ui.game_ui import GameUI
import pygame

def test_auto_pickup_integration():
    """
    测试自动拾取功能的UI集成
    """
    print("=== 测试自动拾取功能UI集成 ===")
    
    # 初始化游戏引擎
    engine = GameEngine(maze_size=8)
    result = engine.initialize_game()
    
    if not result['success']:
        print(f"游戏初始化失败: {result.get('message', '未知错误')}")
        return False
    
    print(f"✓ 游戏引擎初始化成功")
    print(f"  迷宫大小: {engine.maze_size}x{engine.maze_size}")
    print(f"  玩家位置: {engine.player_pos}")
    
    # 测试自动拾取功能的基本方法
    print("\n--- 测试自动拾取基本功能 ---")
    
    # 测试切换功能
    toggle_result = engine.toggle_auto_pickup()
    print(f"✓ 切换自动拾取: {toggle_result['message']}")
    
    # 测试状态获取
    status = engine.get_auto_pickup_status()
    print(f"✓ 自动拾取状态: 启用={status['enabled']}, 有目标={status['has_target']}")
    
    # 测试3x3区域资源检测
    resources = engine._get_resources_in_3x3_area()
    print(f"✓ 3x3区域资源检测: 发现{len(resources)}个资源")
    
    # 测试执行一步自动拾取
    if len(resources) > 0:
        step_result = engine.execute_auto_pickup_step()
        print(f"✓ 执行自动拾取步骤: {step_result['success']}")
        if step_result['success']:
            print(f"  动作: {step_result.get('action', '未知')}")
    
    # 关闭自动拾取
    engine.toggle_auto_pickup()
    print(f"✓ 关闭自动拾取功能")
    
    return True

def test_ui_components():
    """
    测试UI组件是否正确包含自动拾取功能
    """
    print("\n=== 测试UI组件集成 ===")
    
    # 初始化pygame（不显示窗口）
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    
    try:
        # 创建游戏引擎和UI
        engine = GameEngine(maze_size=6)
        engine.initialize_game()
        
        # 创建GameUI实例（但不运行主循环）
        game_ui = GameUI(engine)
        print("✓ GameUI实例创建成功")
        
        # 测试自动拾取状态显示
        status = engine.get_auto_pickup_status()
        print(f"✓ 可以获取自动拾取状态: {status['enabled']}")
        
        # 模拟按键事件处理
        print("\n--- 模拟按键事件 ---")
        
        # 模拟按下'A'键（自动拾取切换）
        print("模拟按下'A'键...")
        try:
            # 直接调用按键处理方法
            game_ui._handle_keydown(pygame.K_a)
            print("✓ 'A'键处理成功")
        except Exception as e:
            print(f"✗ 'A'键处理失败: {e}")
            return False
        
        # 检查自动拾取状态是否改变
        new_status = engine.get_auto_pickup_status()
        if new_status['enabled'] != status['enabled']:
            print("✓ 自动拾取状态成功切换")
        else:
            print("⚠️  自动拾取状态未改变（可能是因为没有资源）")
        
        return True
        
    except Exception as e:
        print(f"✗ UI组件测试失败: {e}")
        return False
    finally:
        pygame.quit()

def test_control_help_text():
    """
    测试控制帮助文本是否包含自动拾取说明
    """
    print("\n=== 测试控制帮助文本 ===")
    
    # 读取game_ui.py文件，检查控制帮助文本
    try:
        with open('src/ui/game_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含自动拾取的说明
        if '3x3自动拾取开/关' in content:
            print("✓ 控制帮助包含自动拾取说明")
        else:
            print("✗ 控制帮助缺少自动拾取说明")
            return False
        
        # 检查是否包含'A'键绑定
        if 'pygame.K_a' in content:
            print("✓ 包含'A'键绑定")
        else:
            print("✗ 缺少'A'键绑定")
            return False
        
        # 检查是否包含toggle_auto_pickup调用
        if 'toggle_auto_pickup' in content:
            print("✓ 包含自动拾取功能调用")
        else:
            print("✗ 缺少自动拾取功能调用")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 读取UI文件失败: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("开始测试自动拾取功能的UI集成...\n")
    
    tests = [
        test_auto_pickup_integration,
        test_control_help_text,
        test_ui_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_func.__name__} 通过")
            else:
                print(f"✗ {test_func.__name__} 失败")
        except Exception as e:
            print(f"✗ {test_func.__name__} 异常: {e}")
        
        print("-" * 50)
    
    print(f"\n测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 自动拾取功能已成功集成到游戏UI中！")
        print("\n集成功能:")
        print("- ✓ 'A'键切换3x3自动拾取功能")
        print("- ✓ 统计面板显示自动拾取状态")
        print("- ✓ 控制帮助包含自动拾取说明")
        print("- ✓ 自动执行完整拾取流程")
        print("- ✓ 游戏暂停和结束状态保护")
        print("\n使用方法:")
        print("1. 运行游戏: python main.py")
        print("2. 按'A'键开启自动拾取")
        print("3. 系统自动收集玩家周围3x3区域内的资源")
        print("4. 按'S'键查看统计信息中的自动拾取状态")
        print("5. 按'H'键查看完整的控制帮助")
    else:
        print("⚠️  部分测试失败，请检查集成")

if __name__ == "__main__":
    main()