import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.algorithms.maze_generator import MazeGenerator
def generate_and_save_maze(size=15, filename='maze2.json'):
    # 创建迷宫生成器
    generator = MazeGenerator(size)
    # 生成迷宫
    maze = generator.generate_maze()
    # 保存迷宫到JSON文件
    generator.save_maze_to_json(filename)
    return maze

def main():

    size = 15
    filename='maze2.json'
    maze = generate_and_save_maze(size, filename)
    for row in maze:
        print(''.join(row))
    print(f"\n生成的迷宫文件 {filename}")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)