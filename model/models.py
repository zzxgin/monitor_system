from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# 创建 ORM 核心对象，后续所有数据库操作（定义表结构、增删改查）都通过这个对象实现。
db = SQLAlchemy()

# 关联表：server_users(user_id, server_id, created_at)多对多
# 使用 SQLAlchemy 的db.Table直接定义表结构，而非通过模型类，这是多对多关系中间表的常见实现方式，
# 服务器-用户多对多关联表
server_users = db.Table('server_users',
    db.Column('server_id', db.Integer, db.ForeignKey('servers.id'), primary_key=True, comment="服务器ID"),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True, comment="用户ID"),
    db.Column('created_at', db.DateTime, default=datetime.now, comment="关联创建时间")
)

#创建用户模型，映射数据库中的users表
class User(db.Model):
    # 指定当前模型对应的数据库表名，必须与数据库中表名一致
    __tablename__="users"
    #定义表字段
    #主键
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(50),unique=True,nullable=False,comment="用户名")
    password=db.Column(db.String(255),nullable=False,comment="密码")
    email=db.Column(db.String(100),nullable=False,comment="告警邮箱")
    role=db.Column(db.Enum("admin","user"), default='user',nullable=False,comment="用户角色：管理员/普通用户")
    created_at=db.Column(db.DateTime,default=datetime.now, comment="创建时间")

    # 关联关系：一个用户可以有多个服务器（多对多关系）
    servers = db.relationship('Server', secondary=server_users, backref='users', lazy=True)

    # 定义获取哪些字段
    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(user) 操作
        """
        return ("id", "username", "email", "role", "created_at")

    # 获取字段的值
    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换
        """
        if key == "created_at":
            return str(getattr(self, key))
        return getattr(self, key)

    # 新增用户的类方法（@classmethod：
    # 用类名调用，如User.create(...)）
    #注意传入参数的顺序
    @classmethod
    def create(cls, username, password, email, role='user'):

        # 在数据模型层进行密码加密
        hashed_password = generate_password_hash(password)
        # 创建一个用户就是实例化当前类，创建一个对象
        user = cls(
            username=username,
            password=hashed_password,
            email=email,
            role=role
        )

        # 将对象添加到ORM会话（类似Git的暂存区，未提交到数据库）
        db.session.add(user)
        # 提交会话：将暂存区的操作同步到数据库（真正执行INSERT）
        db.session.commit()
        return user
    #修改密码时加密
    def set_password(self, password):
        self.password = generate_password_hash(password)

    #登录时加密验证密码是否正确
    def check_password(self, password):
        return check_password_hash(self.password, password)#Returns:bool: 密码是否正确
    #获取所有用户列表
    @classmethod
    def get_all(cls):
        #cls代表当前类本身，query 是 SQLAlchemy 为每个模型类自动生成的一个查询属性。
        return cls.query.all()      #Returns:List[User]: 所有用户对象列表

    #根据用户ID（主键）获取用户信息
    @classmethod
    def get_by_id(cls,user_id):
        return cls.query.get(user_id)       #Returns:User: 用户模型对象，如果不存在默认返回None

    # 根据用户名获取用户信息
    @classmethod
    def get_by_username(cls, username):
        #查询数据库中，username 字段的值等于传入参数 username 的第一条记录，并将其作为一个模型对象返回。如果找不到匹配的记录，则返回 None。
        return cls.query.filter_by(username=username).first()

    #更新用户信息
    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and key != 'id':  # 不允许修改ID
                    if key == 'password':
                        # 密码需要加密处理
                        self.set_password(value)
                    else:
                        setattr(self, key, value)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return None

    # 删除当前用户
    def delete(self):
        try:
            # 先解除所有服务器关联关系
            for server in self.servers:
                server.users.remove(self)
            # 删除用户
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False





#创建服务器模型，映射数据库中的servers表
class Server(db.Model):
    __tablename__ = "servers"

    id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    server_name = db.Column(db.String(100), nullable=False, comment="服务器名称")
    ip_address = db.Column(db.String(45), unique=True, nullable=False, comment="IP地址")
    port = db.Column(db.Integer, default=22, comment="SSH端口，默认22")
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    # 关联关系：一个服务器可以有多个监控数据记录
    monitor_data = db.relationship('MonitorData', backref='server', lazy=True)

    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(server) 操作
        """
        return ("id", "server_name", "ip_address", "port", "created_at")

    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换
        """
        if key == "created_at":
            return str(getattr(self, key))
        return getattr(self, key)

    #创建服务器对象
    @classmethod
    def create(cls, server_name, ip_address, port, user_ids=None):
        server = cls(
            server_name=server_name,
            ip_address=ip_address,
            port=port
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
            # 先删除所有关联的监控数据
            MonitorData.query.filter_by(server_id=server_id).delete()

            # 删除服务器（会自动解除用户关联关系）
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



#创建监控数据模型，映射数据库中的monitor_data表
class MonitorData(db.Model):
    __tablename__ = "monitor_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 外键关联，阻止插入不存在的服务器监控数据
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, comment="关联的服务器ID")
    ip_address = db.Column(db.String(45), nullable=False, comment="服务器IP地址")
    # 监控数据
    cpu_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment="CPU使用率，保留2位小数")
    memory_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment="内存使用率，保留2位小数")
    disk_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment="磁盘使用率，保留2位小数")
    recorded_at = db.Column(db.DateTime, default=datetime.now, comment="数据记录时间")

    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(monitor_data) 操作
        """
        return ("id", "server_id", "ip_address", "cpu_value", "memory_value", "disk_value", "recorded_at")

    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换和Decimal类型转换
        """
        value = getattr(self, key)

        # 处理时间字段
        if key == "recorded_at":
            return str(value)

        # 处理Decimal类型字段
        decimal_fields = ("cpu_value", "memory_value", "disk_value")

        if key in decimal_fields:
            if value is not None:
                return float(value)
        return value

    #创建一条监控记录，负责实际的对象创建和数据库操作
    @classmethod
    def create(cls, server_id, ip_address, cpu_value, memory_value, disk_value):
        data = cls(
            server_id=server_id,
            ip_address=ip_address,
            cpu_value=cpu_value,
            memory_value=memory_value,
            disk_value=disk_value
        )
        db.session.add(data)
        db.session.commit()
        return data #返回监控记录对象

    #根据服务器id获取服务器最新监控数据
    @classmethod
    def get_latest_by_server(cls, server_id):
        # 返回MonitorData: 最新的监控数据对象，如果不存在返回None
        return cls.query.filter_by(server_id=server_id).order_by(cls.recorded_at.desc()).first()

    #根据IP地址创建监控数据记录（包含所有指标），复用create()方法
    @classmethod
    def create_by_ip(cls, ip_address, cpu_value, memory_value, disk_value):
        # 先根据IP查找服务器
        server = Server.get_by_ip(ip_address)
        if not server:
            raise ValueError(f"服务器 {ip_address} 不存在")

        # 创建监控数据，负责业务逻辑（查找服务器），然后委托给 create()，在数据库创建一条记录
        return cls.create(server.id, ip_address, cpu_value, memory_value, disk_value)

    #根据IP地址查询指定时间范围的数据
    @classmethod
    def get_by_ip(cls, ip_address, start_time):
        server = Server.get_by_ip(ip_address)
        if not server:
            return []

        return cls.query.filter(
            cls.server_id == server.id,
            cls.recorded_at >= start_time
        ).order_by(cls.recorded_at.desc()).all()

    #清理7天前的旧数据，避免数据库过大
    @classmethod
    def delete_old_data(cls, days=7):
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        cls.query.filter(cls.recorded_at < cutoff_date).delete()
        db.session.commit()