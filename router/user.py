"""
用户管理API接口
支持角色权限控制和密码管理
"""
from flask import request
from lib.response import response
from flask_restful import Resource
from model.models import db
from model.models import User
from lib.jwt_utils import admin_required

#定义某个资源类，继承自Resource基类
# 类里面每个方法对应一种HTTP请求方式，再为资源类注册路由
#在对应资源类调用写好的model方法
class UserManagement(Resource):
    #获取用户列表或单个用户信息，user_id默认为None
    @admin_required
    def get(self, user_id=None):
        """获取用户列表或指定用户信息"""
        try:
            if user_id:
                # 获取指定用户信息
                user = User.get_by_id(user_id)
                if not user:
                    return response(message="用户不存在", code=404)

                user_data = dict(user)
                return response(data=user_data, message="获取用户信息成功")
            else:
                # 获取所有用户列表
                users = User.get_all()
                user_list = [dict(user) for user in users]
                return response(data=user_list, message="获取用户列表成功")

        except Exception as e:
            return response(message="获取用户信息失败", code=500)

    #新增用户
    @admin_required
    def post(self):
        """添加用户（仅管理员）"""
        try:
            #以json格式接受数据
            data = request.json
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            # 强制设置角色为user，不允许创建admin
            role = 'user'

            # 验证必需字段
            if not all([username, password, email]):
                return response(message="用户名、密码和邮箱不能为空", code=400)

            # 检查用户名是否已存在
            if User.get_by_username(username):
                return response(message="用户名已存在", code=400)

            # 创建用户（密码加密在数据模型层处理）
            user = User.create(username, password, email, role)

            user_data = dict(user)
            return response(data=user_data, message="用户创建成功")

        except Exception as e:
            return response(message="创建用户失败", code=500)

    #更新用户信息
    @admin_required
    def put(self, user_id):
        try:
            data = request.json
            user = User.get_by_id(user_id)
            if not user:
                return response(message="用户不存在", code=404)
            # 准备更新数据
            update_data = {}

            if 'username' in data:
                # 检查新用户名是否已存在
                existing_user = User.get_by_username(data['username'])
                if existing_user and existing_user.id != user_id:
                    return response(message="用户名已存在", code=400)
                update_data['username'] = data['username']

            if 'email' in data:
                update_data['email'] = data['email']

            if 'password' in data and data['password']:
                update_data['password'] = data['password']

            # 使用实例方法更新用户信息
            if update_data:
                updated_user = user.update(**update_data)
                if not updated_user:
                    return response(message="更新用户失败", code=500)

            user_data = dict(user)
            return response(data=user_data, message="用户更新成功")

        except Exception as e:
            return response(message="更新用户失败", code=500)

    #删除用户
    @admin_required
    def delete(self, user_id):
        try:
            user = User.get_by_id(user_id)
            if not user:
                return response(message="用户不存在", code=404)

            # 检查是否为管理员
            if user.role == 'admin':
                return response(message="不能删除管理员用户", code=400)

            username = user.username
            if not user.delete():
                return response(message="删除用户失败", code=500)

            return response(message="用户删除成功")

        except Exception as e:
            return response(message="删除用户失败", code=500)

