# 算法驱动的迷宫探险游戏

一个集成多种经典算法的迷宫探险游戏，包含动态规划、回溯法、分支限界、贪心算法等核心算法实现。

## 🎮 游戏特色

### 核心算法实现
- **动态规划** - 最优路径规划与资源收集
- **回溯法** - 密码破解与谜题求解
- **分支限界** - BOSS战斗策略优化
- **贪心算法** - 资源收集策略
- **分治法** - 迷宫生成算法

### 游戏元素
- 🏰 **迷宫探索** - 自动生成的复杂迷宫
- 💰 **资源收集** - 金币收集与陷阱规避
- 🔐 **密码解谜** - SHA-256加密的密码锁
- ⚔️ **BOSS战斗** - 多技能战斗系统
- 🎯 **智能AI** - 自动游戏模式

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pygame
- numpy
- matplotlib
- pandas

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行游戏
```bash
python main.py
```

## 📁 项目结构

```
algorithom/
├── src/                          # 源代码目录
│   ├── algorithms/               # 算法实现
│   │   ├── maze_generator.py     # 迷宫生成算法
│   │   ├── path_planning.py      # 动态规划路径规划
│   │   ├── puzzle_solver.py      # 回溯法解谜
│   │   ├── boss_strategy.py      # 分支限界BOSS战略
│   │   ├── greedy_strategy.py    # 贪心资源收集
│   │   └── resource_path_planner.py # 资源路径规划
│   ├── ui/                       # 用户界面
│   │   ├── game_ui.py           # 主游戏界面
│   │   ├── lock_ui.py           # 密码锁界面
│   │   └── multi_battle_ui.py   # 战斗界面
│   ├── battle/                   # 战斗系统
│   │   └── multi_monster_battle.py
│   ├── game_engine.py           # 游戏引擎核心
│   └── config.py                # 游戏配置
├── example/                      # 示例文件
│   ├── 迷宫动态规划样例/         # DP算法示例
│   ├── 回溯法解密样例/           # 回溯法示例
│   └── BOSS战样例/              # 分支限界示例
├── dp测试集/                     # 动态规划测试用例
├── font/                         # 字体文件
└── main.py                      # 程序入口
```

## 🧮 算法详解

### 1. 动态规划 - 路径规划
**文件**: `src/algorithms/path_planning.py`

实现最优路径规划，在迷宫中寻找从起点到终点的最大资源收集路径。

**核心思想**:
- 状态定义：`dp[i][j] = (最大资源值, 最小步数)`
- 状态转移：考虑四个方向的移动
- 资源计算：金币(+50)，陷阱(-30)

### 2. 回溯法 - 密码破解
**文件**: `src/algorithms/puzzle_solver.py`

使用回溯算法破解SHA-256加密的三位数密码。

**特点**:
- 支持多种线索类型（素数、奇偶性等）
- 剪枝优化，提高搜索效率
- 三种回溯策略：顺序、随机、启发式

### 3. 分支限界 - BOSS战斗
**文件**: `src/algorithms/boss_strategy.py`

使用分支限界算法优化BOSS战斗策略，寻找最小回合数的获胜方案。

**核心机制**:
- 状态空间搜索
- 启发式函数：`f(n) = g(n) + h(n)`
- 技能冷却时间管理
- 资源消耗优化

### 4. 贪心算法 - 资源收集
**文件**: `src/algorithms/greedy_strategy.py`

实现贪心策略进行资源收集，优先选择价值最高的目标。

### 5. 分治法 - 迷宫生成
**文件**: `src/algorithms/maze_generator.py`

使用分治算法生成具有唯一解的迷宫。

## 🎯 游戏模式

### AI自动模式
- 自动路径规划
- 智能资源收集
- 自动战斗决策
- 实时可视化

### 手动模式
- 键盘控制移动
- 手动解谜
- 策略选择

## 📊 测试用例

### 动态规划测试集
位于 `dp测试集/` 目录，包含不同难度的迷宫：
- **Easy**: 7×7 迷宫
- **Medium**: 15×15 迷宫
- **Hard**: 15×15 复杂迷宫

每个测试用例包含：
- 迷宫JSON文件
- 路径可视化图片
- 结果动画GIF
- 最优解JSON

### 回溯法测试集
位于 `example/回溯法解密样例/`，包含30个密码破解案例。

### BOSS战测试集
位于 `example/BOSS战样例/`，包含9个不同难度的战斗场景。

## 🎨 界面特色

- **现代化UI设计** - Material Design风格
- **实时可视化** - 算法执行过程动画
- **多主题支持** - 深色/浅色主题切换
- **响应式布局** - 自适应不同屏幕尺寸

## 🔧 配置说明

游戏配置位于 `src/config.py`：

```python
class Config:
    # 窗口设置
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # 迷宫设置
    MIN_MAZE_SIZE = 7
    DEFAULT_MAZE_SIZE = 15
    MAX_MAZE_SIZE = 25
    
    # 游戏元素
    WALL = '#'
    PATH = ' '
    START = 'S'
    EXIT = 'E'
    GOLD = 'G'
    TRAP = 'T'
    LOCKER = 'L'
    BOSS = 'B'
```

## 📈 性能优化

- **算法优化**: 使用启发式函数和剪枝策略
- **内存管理**: 状态压缩和缓存机制
- **渲染优化**: 局部刷新和批量绘制
- **并发处理**: 算法计算与UI渲染分离

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 开发计划

- [ ] 添加更多算法实现（A*、Dijkstra等）
- [ ] 支持多人对战模式
- [ ] 增加关卡编辑器
- [ ] 添加成就系统
- [ ] 支持自定义皮肤

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和算法研究者。

---

**享受算法的魅力，在游戏中学习编程！** 🎮✨