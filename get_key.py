import hashlib
import base64

def generate_fernet_key_from_string(input_string):
    """根据输入字符串生成 Fernet 密钥"""
    # 使用 SHA256 哈希算法生成 32 字节的哈希值
    sha256_hash = hashlib.sha256(input_string.encode('utf-8')).digest()

    # 将哈希值转换为 URL-safe base64 编码
    fernet_key = base64.urlsafe_b64encode(sha256_hash)

    return fernet_key.decode('utf-8')  # 返回 URL-safe base64 编码的密钥

def write_key_to_file(fernet_key, key_file_path):
    """将生成的 Fernet 密钥写入 key.key 文件"""
    try:
        with open(key_file_path, 'w') as key_file:
            key_file.write(fernet_key)  # 将 Fernet 密钥写入文件
        print(f"生成的 Fernet 密钥已写入 {key_file_path}.")
    except Exception as e:
        print(f"无法写入 {key_file_path} 文件: {e}")

# 从终端获取用户输入
input_string = input("请输入要生成密钥的字符串: ")

# 生成 Fernet 密钥
fernet_key = generate_fernet_key_from_string(input_string)

# 将生成的密钥写入 key.key 文件
key_file_path = 'key.key'  # 设置 key.key 文件路径
write_key_to_file(fernet_key, key_file_path)

# 打印生成的密钥（可选）
# print(f"生成的 Fernet 密钥是: {fernet_key}")
