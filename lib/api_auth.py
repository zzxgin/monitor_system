
#API密钥认证工具模块


from functools import wraps
from flask import request
from lib.response import response
from config.setting import DEFAULT_API_KEY, DEBUG
import hashlib
import time

# ==================== API密钥配置 ====================
# API密钥配置（从配置文件读取）
# 支持多服务器使用不同的API密钥
API_KEYS = {
    "default": DEFAULT_API_KEY,  # 默认API密钥
    "server_1": "key_abc123def456",  # 服务器1专用密钥
    "server_2": "key_xyz789uvw012",  # 服务器2专用密钥
    "server_3": "key_mno345pqr678"  # 服务器3专用密钥
}

# API密钥过期时间配置（秒）
# 开发环境：7天，生产环境：30天
API_KEY_EXPIRES = 2592000 if not DEBUG else 604800  # 30天或7天

#API密钥认证装饰器,保护监控数据提交API
def api_key_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 从请求头获取API密钥
        api_key = request.headers.get('X-API-Key')

        # 检查是否提供了API密钥
        if not api_key:
            return response(message="缺少API密钥", code=401)

        # 验证API密钥是否有效
        if api_key not in API_KEYS.values():
            return response(message="无效的API密钥", code=401)

        # 验证通过，执行原函数
        return func(*args, **kwargs)
    return decorated_function

#生成API密钥
def generate_api_key(server_name):
    # 获取当前时间戳
    timestamp = str(int(time.time()))

    # 组合服务器名称和时间戳
    raw_key = f"{server_name}_{timestamp}"

    # 使用SHA256生成API密钥哈希值，取前16位
    return hashlib.sha256(raw_key.encode()).hexdigest()[:16]

#验证API密钥是否有效,检查API密钥是否在有效密钥列表中
def validate_api_key(api_key):
    return api_key in API_KEYS.values()
