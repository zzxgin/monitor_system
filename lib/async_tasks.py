from concurrent.futures import ThreadPoolExecutor
from flask import current_app
from model.models import db, MonitorData, Server
from mail.alert import check_and_send_alert_by_ip

# 创建全局线程池
# max_workers=10 表示最多同时有10个线程在后台处理任务
executor = ThreadPoolExecutor(max_workers=10)

def async_process_monitor_data(app, server_ip, metrics):
    """
    异步处理监控数据：入库 + 告警
    注意：由于是异步线程，需要手动创建应用上下文
    """
    with app.app_context():
        try:
            # 1. 数据入库
            # 支持两种字段名格式
            cpu_value = metrics.get('cpu_value', metrics.get('cpu', 0.0))
            memory_value = metrics.get('memory_value', metrics.get('memory', 0.0))
            disk_value = metrics.get('disk_value', metrics.get('disk', 0.0))

            MonitorData.create_by_ip(
                server_ip,
                cpu_value,
                memory_value,
                disk_value
            )
            
            # 2. 告警检查
            alert_metrics = {
                'cpu': cpu_value,
                'memory': memory_value,
                'disk': disk_value
            }
            for metric_type, value in alert_metrics.items():
                check_and_send_alert_by_ip(server_ip, metric_type, float(value))
                
        except Exception as e:
            # 实际项目中应记录日志
            print(f"异步处理监控数据失败: {str(e)}")
