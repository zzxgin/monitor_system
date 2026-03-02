from datetime import datetime
from .base import db

# 关联表：server_users(user_id, server_id, created_at)多对多
# 使用 SQLAlchemy 的db.Table直接定义表结构，而非通过模型类，这是多对多关系中间表的常见实现方式，
# 服务器-用户多对多关联表
server_users = db.Table('server_users',
    db.Column('server_id', db.Integer, db.ForeignKey('servers.id'), primary_key=True, comment='服务器ID'),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True, comment='用户ID'),
    db.Column('created_at', db.DateTime, default=datetime.now, comment='关联创建时间')
)
