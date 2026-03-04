
#API密钥认证工具模块


from functools import wraps
from flask import request
from lib.response import response
from config.setting import DEFAULT_API_KEY, DEBUG
import hashlib
import time

# ==================== API认证配置 ====================
# AppID 和 SecretKey 配置
# AppID用于标识客户端身份，SecretKey用于签名加密（必须保密）
API_CREDENTIALS = {
    # AppID : SecretKey
    "default_client": "sk_default_123456",
    "server_1": "sk_abc123def456",
    "server_2": "sk_xyz789uvw012",
    "server_3": "sk_mno345pqr678"
}

# 签名有效时间窗口（秒）
# 防止重放攻击，请求的时间戳必须在当前时间的前后范围内
SIGN_EXPIRE_SECONDS = 60

# 生成签名函数
def generate_signature(app_id, secret_key, timestamp, nonce=None):
    """
    生成签名
    算法：sha256(app_id + secret_key + timestamp + nonce)
    """
    # 组合待签名字符串
    raw_str = f"{app_id}{secret_key}{timestamp}"
    if nonce:
        raw_str += nonce
        
    # 计算哈希值
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

# API签名认证装饰器
def api_key_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 1. 获取请求头参数
        app_id = request.headers.get('X-App-ID')
        timestamp = request.headers.get('X-Timestamp')
        sign = request.headers.get('X-Sign')
        nonce = request.headers.get('X-Nonce', '') # 随机字符串，可选

        # 2. 检查参数完整性
        if not all([app_id, timestamp, sign]):
            return response(message="缺少认证参数(X-App-ID, X-Timestamp, X-Sign)", code=401)

        # 3. 检查AppID是否存在
        secret_key = API_CREDENTIALS.get(app_id)
        if not secret_key:
            return response(message="无效的AppID", code=401)

        # 4. 检查时间戳有效期（防重放攻击）
        try:
            req_time = int(timestamp)
            now_time = int(time.time())
            # 如果请求时间与服务器时间相差超过设定阈值（例如60秒），则拒绝
            if abs(now_time - req_time) > SIGN_EXPIRE_SECONDS:
                return response(message="请求已过期", code=401)
        except ValueError:
            return response(message="时间戳格式错误", code=401)

        # 5. 服务端重新计算签名
        server_sign = generate_signature(app_id, secret_key, timestamp, nonce)

        # 6. 比对签名
        if server_sign != sign:
            return response(message="签名验证失败", code=401)

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
