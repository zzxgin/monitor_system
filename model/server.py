from datetime import datetime
from .base import db
from .associations import server_users
from .user import User
from .monitor import MonitorData

class ServerGroup(db.Model):
    """
    【新增】服务器分组表/资产组表
    解决痛点：资产混乱，无法按业务线管理
    """
    __tablename__ = 'server_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, comment='分组名称(如:后端组,大数据组)')
    description = db.Column(db.String(200), comment='分组描述')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联关系：一个分组包含多个服务器
    # 使用字符串引用
    servers = db.relationship('Server', backref='group', lazy=True)
    
    def keys(self):
        return ('id', 'name', 'description', 'created_at')

    def __getitem__(self, key):
        if key == 'created_at':
            return str(getattr(self, key))
        return getattr(self, key)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def create(cls, name, description=None):
        group = cls(name=name, description=description)
        db.session.add(group)
        db.session.commit()
        return group


#创建服务器模型，映射数据库中的servers表
class Server(db.Model):
    __tablename__ = 'servers'

    id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    
    # 【新增】关联分组ID
    group_id = db.Column(db.Integer, db.ForeignKey('server_groups.id'), nullable=True, comment='所属分组ID')
    
    server_name = db.Column(db.String(100), nullable=False, comment='服务器名称')
    ip_address = db.Column(db.String(45), unique=True, nullable=False, comment='IP地址')
    port = db.Column(db.Integer, default=22, comment='SSH端口，默认22')
    description = db.Column(db.String(200), comment='服务器描述/用途备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系：一个服务器可以有多个监控数据记录
    monitor_data = db.relationship('MonitorData', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    alert_rules = db.relationship('AlertRule', backref='server', lazy=True, cascade='all, delete-orphan')
    alert_history = db.relationship('AlertHistory', backref='server', lazy='dynamic', cascade='all, delete-orphan')

    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(server) 操作
        """
        return ('id', 'server_name', 'ip_address', 'port', 'group_id', 'description', 'created_at')

    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换
        """
        if key == 'created_at':
            return str(getattr(self, key))
        return getattr(self, key)

    #创建服务器对象
    @classmethod
    def create(cls, server_name, ip_address, port=22, group_id=None, description=None, user_ids=None):
        server = cls(
            server_name=server_name,
            ip_address=ip_address,
            port=port,
            group_id=group_id,
            description=description
        )
        db.session.add(server)
        db.session.flush()  # 获取服务器ID

        # 被监控服务器关联多个用户
        if user_ids:
            for user_id in user_ids:
                user = User.get_by_id(user_id)
                if user:
                    server.users.append(user)

        db.session.commit()
        return server       #返回服务器对象

    #获取所有服务器列表
    @classmethod
    def get_all(cls):
        return cls.query.all()      #Returns:    List[Server]: 所有服务器对象列表

    #根据id获取服务器信息
    @classmethod
    def get_by_id(cls, server_id):
        return cls.query.get(server_id)#根据id返回一个服务器对象

    # 根据ip获取服务器信息
    @classmethod
    def get_by_ip(cls, ip_address):
        return cls.query.filter_by(ip_address=ip_address).first()#根据ip返回一个服务器对象，不存在返回None

    #获取指定用户的所有服务器,通过多对多关系查询
    @classmethod
    def get_by_user(cls, user_id):
        return cls.query.join(server_users).filter(server_users.c.user_id == user_id).all()#返回List[Server]: 该用户的服务器列表

    # 根据id删除服务器，先删除所有关联的监控数据
    @classmethod
    def delete(cls, server_id):
        #先查到id在删除
        server = cls.query.get(server_id)
        if server:
            # 这里的级联删除已经在 relationship 中配置了 cascade='all, delete-orphan'，
            # 理论上不需要手动删 MonitorData，但为了保险起见还是显式保留逻辑或简化它
            # 由于配置了 cascade，这里只需删 server 即可
            MonitorData.query.filter_by(server_id=server_id).delete()
            db.session.delete(server)
            db.session.commit()
            return True
        return False

    #获取告警用户列表
    def get_alert_users(self):
        return list(self.users)

    #更新服务器关联用户
    @classmethod
    def update_users(cls, server_id, user_ids):
        server = cls.query.get(server_id)
        if server:
            # 清空现有关联
            server.users.clear()
            # 添加新的关联用户
            if user_ids:
                for user_id in user_ids:
                    user = User.get_by_id(user_id)
                    if user:
                        server.users.append(user)

            db.session.commit()
            return server
        return None
