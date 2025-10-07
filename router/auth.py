from flask import request
from flask_restful import Resource
from lib.response import response
from model.models import User


#用户登录验证api资源类，根据用户id生产token，并限制只有admin可以登录
class Auth(Resource):
    #处理用户登录post请求
    def post(self):
        try:
            data=request.json
            username = data.get('username')
            password = data.get('password')

            # 验证必需参数
            if not username or not password:
                return response(message="用户名和密码不能为空", code=400)

            #查找用户
            user=User.get_by_username(username)
            if not user:
                return response(message="用户不存在", code=401)

            # 验证密码（使用数据模型的方法）
            if not user.check_password(password):
                return response(message="密码错误", code=401)

            # 只允许admin用户登录
            if user.role != 'admin':
                return response(message="只有管理员可以登录系统", code=403)

            # 生成JWT Token
            from lib.jwt_utils import create_token
            token = create_token(identity=user.id)


            # 构建返回用户数据
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "token": token
            }

            return response(data=user_data,message="登录成功")

        except Exception as e:
            return response(message="登录失败", code=500)
