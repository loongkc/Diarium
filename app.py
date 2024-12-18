import subprocess
import os
import sys
from get_key import generate_fernet_key_from_string  # 导入 get_key.py 中的生成密钥函数

# 定义 key.key 文件路径
key_file_path = 'key.key'

def clear_key_file():
    """清空 key.key 文件中的内容"""
    try:
        with open(key_file_path, 'w') as key_file:
            key_file.write("")  # 清空文件内容
        print(f"{key_file_path} 文件内容已清空.")
    except Exception as e:
        print(f"无法清空 {key_file_path} 文件: {e}")

def run_diarium():
    """运行 Diarium Base.py 程序"""
    try:
        # 使用 subprocess 启动 Diarium Base.py（假设 Diarium Base.py 在同一目录下）
        process = subprocess.Popen([sys.executable, 'Diarium Base.py'])

        # 等待 Diarium 程序退出
        process.wait()
        
        # 在程序退出后清空 key.key 文件
        clear_key_file()

    except Exception as e:
        print(f"无法运行 Diarium Base.py: {e}")

if __name__ == "__main__":
    run_diarium()
