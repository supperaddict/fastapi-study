from security import hash_password, verify_password

hashed = hash_password("example123")

print("生成的哈希：", hashed)
print("正确密码：", verify_password("example123", hashed))
print("错误密码：", verify_password("wrong123", hashed))
