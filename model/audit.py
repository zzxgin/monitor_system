from datetime import datetime
from .base import db

class AuditLog(db.Model):
    """
    【新增】审计日志表
    解决痛点：记录敏感操作，满足安全合规需求
    表关系：
    Users (1) <-> (N) AuditLogs
    这是一个“逻辑上的一对多弱关联”。即一个用户可以产生多条日志。
    为了保证审计证据的不可篡改与留存，这里有意不设置外键级联删除。
    即使删除了用户，日志中的 user_id 与 username_snapshot 依然保留，确保操作可追溯。
    """
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    user_id = db.Column(db.Integer, comment='操作人ID(可为空,如系统自动任务)')
    username_snapshot = db.Column(db.String(50), comment='用户名快照')
    
    action = db.Column(db.String(50), nullable=False, comment='动作(如:DELETE_SERVER)')
    target = db.Column(db.String(100), comment='操作对象(如:server_id=5)')
    details = db.Column(db.Text, comment='详细信息/JSON')
    client_ip = db.Column(db.String(45), comment='操作来源IP')
    
    created_at = db.Column(db.DateTime, default=datetime.now, comment='记录时间')

    @classmethod
    def log(cls, user, action, target, details=None, client_ip=None):
        """记录日志的快捷方法"""
        log_entry = cls(
            user_id=user.id if user else None,
            username_snapshot=user.username if user else 'SYSTEM',
            action=action,
            target=target,
            details=details,
            client_ip=client_ip
        )
        db.session.add(log_entry)
        db.session.commit()
