from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .base import db
from .associations import server_users

#创建用户模型，映射数据库中的users表
class User(db.Model):
    # 指定当前模型对应的数据库表名，必须与数据库中表名一致
    __tablename__='users'
    #定义表字段
    #主键
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(50),unique=True,nullable=False,comment='用户名')
    password=db.Column(db.String(255),nullable=False,comment='密码')
    email=db.Column(db.String(100),nullable=False,comment='告警邮箱')
    role=db.Column(db.Enum('admin','user'), default='user',nullable=False,comment='用户角色：管理员/普通用户')
    created_at=db.Column(db.DateTime,default=datetime.now, comment='创建时间')

    # 关联关系：一个用户可以有多个服务器（多对多关系）
    # 使用字符串引用 'Server' 避免循环导入
    servers = db.relationship('Server', secondary=server_users, backref='users', lazy=True)

    # 定义获取哪些字段
    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(user) 操作
        """
        return ('id', 'username', 'email', 'role', 'created_at')

    # 获取字段的值
    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换
        """
        if key == 'created_at':
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
