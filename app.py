import subprocess
import os
import sys

# 定义 key.key 文件路径
key_file_path = 'key.key'

def get_key_and_write_to_file():
    """提示用户输入 key，并将其写入 key.key 文件"""
    key = input("请输入一个密钥（key）：")
    try:
        with open(key_file_path, 'w') as key_file:
            key_file.write(key)  # 将用户输入的 key 写入文件
        print(f"密钥已写入 {key_file_path}.")
    except Exception as e:
        print(f"无法写入 {key_file_path} 文件: {e}")

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
    # 第一步：输入密钥并写入 key.key 文件
    get_key_and_write_to_file()

    # 第二步：运行 Diarium Base.py 并在退出后清空 key.key 文件
    run_diarium()
