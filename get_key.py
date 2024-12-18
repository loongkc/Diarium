import hashlib
import base64

def generate_fernet_key_from_string(input_string):
    # 使用 SHA256 哈希算法生成 32 字节的哈希值
    sha256_hash = hashlib.sha256(input_string.encode('utf-8')).digest()

    # 将哈希值转换为 URL-safe base64 编码
    fernet_key = base64.urlsafe_b64encode(sha256_hash)

    return fernet_key.decode('utf-8')  # 返回 URL-safe base64 编码的密钥

# 从终端获取用户输入
input_string = input("请输入要生成密钥的字符串: ")

# 生成并打印 Fernet 密钥
fernet_key = generate_fernet_key_from_string(input_string)
print(f"生成的 Fernet 密钥是: {fernet_key}")
