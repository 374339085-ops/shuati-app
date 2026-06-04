import sys
sys.path.insert(0, 'D:\\刷题软件')

# 先清理旧的 accounts 文件
import os
acct_file = "D:\\刷题软件\\刷题数据\\accounts.json"
if os.path.exists(acct_file):
    os.remove(acct_file)

# 直接测试所有核心函数
from 刷题软件 import (load_accounts, save_accounts, hash_password, 
                      is_valid_phone, is_valid_password, DATA_DIR)

print(f"DATA_DIR = {DATA_DIR}")
print(f"accounts.json = {os.path.join(DATA_DIR, 'accounts.json')}")

# 测试注册流程
accounts = {}
phone = "13812345678"
pwd_hash = hash_password("123456")
accounts[phone] = {"password": pwd_hash, "created_at": 0}
save_accounts(accounts)
print(f"注册后 accounts: {accounts}")

# 测试登录流程
loaded = load_accounts()
assert loaded[phone]["password"] == hash_password("123456"), "密码验证失败"
print("登录验证 OK")

# 测试手机号校验
assert is_valid_phone("13812345678") == True
assert is_valid_phone("12345") == False
assert is_valid_phone("abc") == False
print("手机号校验 OK")

# 测试密码校验
assert is_valid_password("123456") == True
assert is_valid_password("12345") == False
print("密码校验 OK")

# 清理
os.remove(acct_file)
print("\n✅ 所有测试通过！")
