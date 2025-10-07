#告警模块

from datetime import datetime, timedelta
from config.setting import DEFAULT_THRESHOLDS, ALERT_TEMPLATES, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_SENDER
from model.models import Server, User


# 基于IP地址的持续告警检查，如果80%以上的数据都超过阈值，认为持续告警
def check_sustained_alert_by_ip(ip_address, metric_type, value, minutes=2):
    from model.models import MonitorData

    # 获取最近N分钟的数据
    start_time = datetime.utcnow() - timedelta(minutes=minutes)

    # 根据IP地址查询最近N分钟的数据
    recent_data = MonitorData.get_by_ip(ip_address, start_time)

    if len(recent_data) < 3:  # 至少需要3个数据点
        return False

    # 获取阈值
    thresholds = DEFAULT_THRESHOLDS[metric_type]
    alert_level = determine_alert_level(value, thresholds)

    if not alert_level:
        return False

    # 检查是否所有数据都超过对应阈值
    threshold_value = thresholds[alert_level]
    sustained_count = 0

    for data in recent_data:
        if metric_type == 'cpu' and data.cpu_value >= threshold_value:
            sustained_count += 1
        elif metric_type == 'memory' and data.memory_value >= threshold_value:
            sustained_count += 1
        elif metric_type == 'disk' and data.disk_value >= threshold_value:
            sustained_count += 1

    # 如果80%以上的数据都超过阈值，认为持续告警
    return sustained_count >= len(recent_data) * 0.8


# 根据IP地址找到服务器告警检查，获取服务器的所有关联用户
# 调用 check_sustained_alert_by_ip()检查是否持续超过阈值（2分钟）
# 向所有关联用户的邮箱发送告警
def check_and_send_alert_by_ip(ip_address, metric_type, value):
    try:
        # 1. 获取服务器信息
        server = Server.get_by_ip(ip_address)
        if not server:
            pass  # 服务器不存在
            return False

        # 2. 获取告警用户列表
        alert_users = server.get_alert_users()
        if not alert_users:
            pass  # 服务器没有关联用户
            return False

        # 3. 获取告警阈值
        thresholds = DEFAULT_THRESHOLDS[metric_type]

        # 4. 检查告警级别
        alert_level = determine_alert_level(value, thresholds)

        if alert_level:
            # 5. 检查是否持续超过阈值（2分钟）
            if not check_sustained_alert_by_ip(ip_address, metric_type, value, minutes=2):
                return True

            # 6. 向所有关联用户发送告警邮件
            success_count = 0
            total_count = len(alert_users)

            for user in alert_users:
                success = send_alert_email(
                    user.email,
                    server.server_name,
                    metric_type,
                    value,
                    alert_level
                )

                if success:
                    success_count += 1
                else:
                    pass  # 告警发送失败

            if success_count > 0:
                pass  # 告警发送完成
            return success_count > 0
        else:
            return True

    except Exception as e:
        pass  # 告警检查失败
        return False


# 确定告警级别
def determine_alert_level(value, thresholds):
    if value >= thresholds['emergency']:
        return 'emergency'
    elif value >= thresholds['critical']:
        return 'critical'
    elif value >= thresholds['warning']:
        return 'warning'
    return None


# 发送告警邮件
def send_alert_email(email, server_name, metric_type, value, level):
    try:
        import smtplib
        from email.mime.text import MIMEText

        # 生成告警消息
        template = ALERT_TEMPLATES[level]
        message = template.format(
            server_name=server_name,
            metric_type=metric_type,
            value=value,
            threshold=get_threshold_by_level(level, metric_type)
        )

        # 创建邮件
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = SMTP_SENDER
        msg['To'] = email
        msg['Subject'] = f"【{level.upper()}】服务器 {server_name} 监控告警"

        # 发送邮件
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_SENDER, email, msg.as_string())
        return True
    except Exception as e:
        pass  # 发送告警邮件失败
        return False


# 根据级别获取阈值
def get_threshold_by_level(level, metric_type):
    thresholds = DEFAULT_THRESHOLDS[metric_type]
    if level == 'emergency':
        return thresholds['emergency']
    elif level == 'critical':
        return thresholds['critical']
    elif level == 'warning':
        return thresholds['warning']
    return 0
