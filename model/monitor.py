from datetime import datetime
from .base import db

#创建监控数据模型，映射数据库中的monitor_data表
class MonitorData(db.Model):
    __tablename__ = 'monitor_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 外键关联，阻止插入不存在的服务器监控数据
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, comment='关联的服务器ID')
    ip_address = db.Column(db.String(45), nullable=False, comment='服务器IP地址') # 这里的 IP 其实是冗余字段，但为了方便查询保留
    # 监控数据
    cpu_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment='CPU使用率，保留2位小数')
    memory_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment='内存使用率，保留2位小数')
    disk_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment='磁盘使用率，保留2位小数')
    recorded_at = db.Column(db.DateTime, default=datetime.now, comment='数据记录时间', index=True)

    def keys(self):
        """
        返回字典序列化时的键列表
        用于支持 dict(monitor_data) 操作
        """
        return ('id', 'server_id', 'ip_address', 'cpu_value', 'memory_value', 'disk_value', 'recorded_at')

    def __getitem__(self, key):
        """
        支持字典式访问对象属性
        自动处理时间字段的字符串转换和Decimal类型转换
        """
        value = getattr(self, key)

        # 处理时间字段
        if key == 'recorded_at':
            return str(value)

        # 处理Decimal类型字段
        decimal_fields = ('cpu_value', 'memory_value', 'disk_value')

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
        # 需要在方法内部import避免循环依赖，因为Server也在model.server中
        from .server import Server
        
        # 先根据IP查找服务器
        server = Server.get_by_ip(ip_address)
        if not server:
            raise ValueError(f'服务器 {ip_address} 不存在')

        # 创建监控数据，负责业务逻辑（查找服务器），然后委托给 create()，在数据库创建一条记录
        return cls.create(server.id, ip_address, cpu_value, memory_value, disk_value)

    #根据IP地址查询指定时间范围的数据
    @classmethod
    def get_by_ip(cls, ip_address, start_time):
        from .server import Server
        
        server = Server.get_by_ip(ip_address)
        if not server:
            return []

        return cls.query.filter(
            cls.server_id == server.id,
            cls.recorded_at >= start_time
        ).order_by(cls.recorded_at.desc()).all()

    #根据ID查询指定时间范围的数据（用于历史趋势图）
    @classmethod
    def get_history_by_server_id(cls, server_id, hours=1):
        from datetime import timedelta
        start_time = datetime.now() - timedelta(hours=hours)
        return cls.query.filter(
            cls.server_id == server_id,
            cls.recorded_at >= start_time
        ).order_by(cls.recorded_at.asc()).all()

    #清理7天前的旧数据，避免数据库过大
    @classmethod
    def delete_old_data(cls, days=7):
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        cls.query.filter(cls.recorded_at < cutoff_date).delete()
        db.session.commit()

class AlertRule(db.Model):
    """
    【新增】告警规则表
    解决痛点：不再是一刀切的硬编码阈值，实现精细化告警
    """
    __tablename__ = 'alert_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, comment='关联服务器')
    
    metric_type = db.Column(db.Enum('cpu', 'memory', 'disk'), nullable=False, comment='指标类型')
    threshold = db.Column(db.DECIMAL(5, 2), nullable=False, comment='触发阈值(%)')
    silence_minutes = db.Column(db.Integer, default=60, comment='静默时间(分钟)避免频繁轰炸')
    is_enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

class AlertHistory(db.Model):
    """
    【新增】告警历史表
    解决痛点：告警数据沉淀，支持SLA统计和故障复盘
    """
    __tablename__ = 'alert_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, comment='关联服务器')
    
    metric_type = db.Column(db.String(20), nullable=False, comment='告警指标')
    current_value = db.Column(db.DECIMAL(5, 2), nullable=False, comment='当时数值')
    threshold_snapshot = db.Column(db.DECIMAL(5, 2), comment='当时阈值快照')
    
    alert_content = db.Column(db.Text, comment='告警邮件内容')
    status = db.Column(db.Enum('firing', 'resolved', 'ignored'), default='firing', comment='状态')
    
    triggered_at = db.Column(db.DateTime, default=datetime.now, comment='触发时间')
    resolved_at = db.Column(db.DateTime, nullable=True, comment='恢复时间')
    
    @classmethod
    def create(cls, server_id, metric_type, current_value, threshold, content):
        history = cls(
            server_id=server_id,
            metric_type=metric_type,
            current_value=current_value,
            threshold_snapshot=threshold,
            alert_content=content
        )
        db.session.add(history)
        db.session.commit()
        return history
