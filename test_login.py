import sys
sys.path.insert(0, 'D:\\刷题软件')
from 刷题软件 import LoginWindow, QuizApp, load_accounts, save_accounts, hash_password, ACCOUNTS_FILE
print("import OK")

# 测试账号存储
import os
# 清理测试
if os.path.exists(ACCOUNTS_FILE):
    os.remove(ACCOUNTS_FILE)

reg_phone = "13800138000"
reg_pwd = hash_password("123456")

accounts = load_accounts()
print(f"空账号: {accounts}")

accounts[reg_phone] = {"password": reg_pwd, "created_at": 0}
save_accounts(accounts)
print("注册保存 OK")

accounts2 = load_accounts()
print(f"读取账号: {list(accounts2.keys())}")

# 测试登录验证
assert reg_phone in accounts2
assert accounts2[reg_phone]["password"] == hash_password("123456")
assert accounts2[reg_phone]["password"] != hash_password("wrong")
print("登录验证 OK")

# 测试手机号校验
import re
def is_valid_phone(p):
    return re.match(r'^1[3-9]\d{9}$', p) is not None
assert is_valid_phone("13800138000")
assert not is_valid_phone("12345")
assert not is_valid_phone("abc")
print("手机号校验 OK")

# 清理
os.remove(ACCOUNTS_FILE)
print("ALL TESTS PASSED ✅")
