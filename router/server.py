"""
服务器管理API接口
支持服务器管理，多用户关联和IP地址匹配
"""

from flask import request
from flask_restful import Resource
from lib.response import response
from model import Server, User, ServerGroup
from lib.jwt_utils import admin_required
from model import db

#服务器管理API资源类
class ServerManagement(Resource):
    #获取服务器列表或指定服务器信息
    @admin_required
    def get(self, server_id=None):
        try:
            if server_id:
                # 获取指定服务器信息
                server = Server.get_by_id(server_id)
                if not server:
                    return response(message="服务器不存在", code=404)

                server_data = dict(server)
                # 补充与处理关联数据
                try:
                    server_data['users'] = [dict(user) for user in server.users]
                    if server.group:
                        server_data['group_name'] = server.group.name
                except Exception:
                    pass
                return response(data=server_data, message="获取服务器信息成功")
            else:
                # 获取所有服务器列表
                servers = Server.get_all()
                server_list = []
                for server in servers:
                    server_data = dict(server)
                    try:
                        server_data['users'] = [dict(user) for user in server.users]
                        if server.group:
                            server_data['group_name'] = server.group.name
                    except Exception:
                        pass
                    server_list.append(server_data)

                return response(data=server_list, message="获取服务器列表成功")

        except Exception as e:
            return response(message=f"获取服务器信息失败: {str(e)}", code=500)

    #添加服务器
    @admin_required
    def post(self):
        try:
            data = request.json
            server_name = data.get('server_name')
            ip_address = data.get('ip_address')
            port = data.get('port', 22)
            user_ids = data.get('user_ids', [])  # 关联用户列表
            group_id = data.get('group_id')
            description = data.get('description')

            # 验证必需字段
            if not all([server_name, ip_address]):
                return response(message="服务器名称和IP地址不能为空", code=400)

            # 检查IP地址是否已存在
            if Server.get_by_ip(ip_address):
                return response(message="IP地址已存在", code=400)

            # 验证关联用户（支持用户名和用户ID）
            valid_user_ids = []
            for user_identifier in user_ids:
                if isinstance(user_identifier, int):
                    user = User.get_by_id(user_identifier)
                elif isinstance(user_identifier, str):
                    user = User.get_by_username(user_identifier)
                else:
                    continue

                if user:
                    valid_user_ids.append(user.id)

            # 创建服务器
            # 注意：Server.create现在支持group_id和description参数
            server = Server.create(
                server_name=server_name, 
                ip_address=ip_address, 
                port=port, 
                group_id=group_id,
                description=description,
                user_ids=valid_user_ids
            )

            # 构建返回数据
            server_data = dict(server)
            try:
                server_data['users'] = [dict(user) for user in server.users]
                if server.group:
                    server_data['group_name'] = server.group.name
            except Exception:
                pass

            return response(data=server_data, message="服务器创建成功")

        except Exception as e:
            return response(message=f"创建服务器失败: {str(e)}", code=500)

    #更新服务器信息
    @admin_required
    def put(self, server_id):
        try:
            data = request.json
            server = Server.get_by_id(server_id)
            if not server:
                return response(message="服务器不存在", code=404)

            # 更新服务器信息
            if 'server_name' in data:
                server.server_name = data['server_name']

            if 'ip_address' in data:
                # 检查新IP地址是否已存在
                existing_server = Server.get_by_ip(data['ip_address'])
                if existing_server and existing_server.id != server_id:
                    return response(message="IP地址已存在", code=400)
                server.ip_address = data['ip_address']

            if 'port' in data:
                server.port = data['port']
                
            if 'group_id' in data:
                server.group_id = data['group_id']
                
            if 'description' in data:
                server.description = data['description']

            if 'user_ids' in data:
                # 更新关联用户
                user_ids = data['user_ids']
                if isinstance(user_ids, list):
                    valid_user_ids = []
                    for user_identifier in user_ids:
                        if isinstance(user_identifier, int):
                            user = User.get_by_id(user_identifier)
                        elif isinstance(user_identifier, str):
                            user = User.get_by_username(user_identifier)
                        else:
                            continue

                        if user:
                            valid_user_ids.append(user.id)
                    
                    # 更新关联用户
                    Server.update_users(server_id, valid_user_ids)

            db.session.commit()

            server_data = dict(server)
            try:
                server_data['users'] = [dict(user) for user in server.users]
                if server.group:
                    server_data['group_name'] = server.group.name
            except Exception:
                pass
            return response(data=server_data, message="服务器更新成功")

        except Exception as e:
            db.session.rollback()
            return response(message=f"更新服务器失败: {str(e)}", code=500)

    #删除服务器
    @admin_required
    def delete(self, server_id):
        try:
            server = Server.get_by_id(server_id)
            if not server:
                return response(message="服务器不存在", code=404)

            Server.delete(server_id)

            return response(message="服务器删除成功")

        except Exception as e:
            return response(message="删除服务器失败", code=500)

#服务器添加删除用户管理API
class ServerUserAPI(Resource):

    #为服务器添加用户
    @admin_required
    def post(self, server_id):
        try:
            data = request.json
            user_identifier = data.get('user_id') or data.get('username')

            if not user_identifier:
                return response(message="用户ID或用户名不能为空", code=400)

            server = Server.get_by_id(server_id)
            if not server:
                return response(message="服务器不存在", code=404)

            # 检查用户是否存在（支持用户名和用户ID）
            user = None
            if isinstance(user_identifier, int):
                user = User.get_by_id(user_identifier)
            elif isinstance(user_identifier, str):
                user = User.get_by_username(user_identifier)

            if not user:
                return response(message="用户不存在", code=400)

            # 检查是否已关联
            if user in server.users:
                return response(message="用户已关联到此服务器", code=400)

            # 添加用户关联
            server.users.append(user)
            db.session.commit()

            return response(message="用户添加成功")

        except Exception as e:
            return response(message="添加服务器用户失败", code=500)

    #从服务器移除用户
    @admin_required
    def delete(self, server_id, user_id):
        try:
            server = Server.get_by_id(server_id)
            if not server:
                return response(message="服务器不存在", code=404)

            # 检查用户是否存在
            user = User.get_by_id(user_id)
            if not user:
                return response(message="用户不存在", code=400)

            # 检查是否已关联
            if user not in server.users:
                return response(message="用户未关联到此服务器", code=400)

            # 移除用户关联
            server.users.remove(user)
            db.session.commit()

            return response(message="用户移除成功")

        except Exception as e:
            return response(message="移除服务器用户失败", code=500)

#查看指定用户有哪些关联的服务器
class UserServers(Resource):
    @admin_required
    def get(self):
        try:
            user_id = request.args.get('user_id', type=int)
            if not user_id:
                return response(message="请指定用户ID", code=400)

            servers = Server.get_by_user(user_id)
            server_list = [dict(server) for server in servers]

            return response(data=server_list, message="获取用户服务器列表成功")

        except Exception as e:
            return response(message="获取用户服务器失败", code=500)

# 【新增】服务器分组管理API
class ServerGroupManagement(Resource):
    @admin_required
    def get(self):
        try:
            groups = ServerGroup.get_all()
            return response(data=[dict(g) for g in groups], message="获取分组列表成功")
        except Exception as e:
            return response(message="获取分组列表失败", code=500)

    @admin_required
    def post(self):
        try:
            data = request.json
            name = data.get('name')
            description = data.get('description')
            
            if not name:
                return response(message="分组名称不能为空", code=400)
                
            group = ServerGroup.create(name=name, description=description)
            return response(data=dict(group), message="分组创建成功")
        except Exception as e:
            return response(message=f"创建分组失败: {str(e)}", code=500)
