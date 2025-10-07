
# JWT认证工具模块

#Flask的JWT扩展库，提供JWT功能
# create_access_token: 在用户登录时，创建并返回一个加密的 JWT 令牌。
# jwt_required: 一个装饰器，用于保护路由，确保只有携带有效 JWT 令牌的请求才能访问。
# get_jwt_identity: 在受保护的路由中，获取当前登录用户的身份（如用户 ID）
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps     #保持装饰器函数的元数据
from lib.response import response

#创建JWT访问令牌
def create_token(identity):
    #将输入的用户ID转换为JWT令牌返回
    return create_access_token(identity=str(identity))

#创建管理员权限装饰器，先验证token是否有效
def admin_required(func):
    @wraps(func)  # 保持原函数的元数据
    @jwt_required()  # 验证JWT令牌是否有效，一个装饰器
    # 权限验证逻辑
    def decorated_function(*args, **kwargs):
        try:
            # 导入用户模型
            from model.models import User

            # 从token中提取获取当前用户ID
            current_user_id = get_jwt_identity()

            # 查询用户信息
            user = User.get_by_id(int(current_user_id))

            # 检查用户是否存在且具有管理员权限
            if not user or user.role != 'admin':
                return response(message="需要管理员权限", code=403)

            # 执行原函数
            return func(*args, **kwargs)
        except Exception as e:
            return response(message="权限验证失败", code=500)
    return decorated_function