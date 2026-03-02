from .base import db
from .associations import server_users
from .user import User
from .server import Server, ServerGroup
from .monitor import MonitorData, AlertRule, AlertHistory
from .audit import AuditLog

# 定义函数：将 ORM 实例与app核心对象绑定
def init_app_db(app):
    db.init_app(app)