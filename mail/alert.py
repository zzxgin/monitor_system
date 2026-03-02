#告警模块

from datetime import datetime, timedelta
from config.setting import DEFAULT_THRESHOLDS, ALERT_TEMPLATES, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_SENDER
from model import Server, User, AlertRule, AlertHistory


# 获取服务器的告警阈值（优先使用自定义规则）
def get_server_thresholds(server, metric_type):
    # 尝试查询该服务器的自定义告警规则
    rule = AlertRule.query.filter_by(server_id=server.id, metric_type=metric_type, is_enabled=True).first()
    
    if rule:
        # 如果有自定义规则，统一使用该阈值
        val = float(rule.threshold)
        return {
            'warning': val,
            'critical': val,
            'emergency': val
        }
    else:
        return DEFAULT_THRESHOLDS.get(metric_type)

# 基于IP地址的持续告警检查，如果80%以上的数据都超过阈值，认为持续告警
def check_sustained_alert_by_ip(ip_address, metric_type, value, minutes=2, thresholds=None):
    from model import MonitorData

    # 获取最近N分钟的数据
    start_time = datetime.utcnow() - timedelta(minutes=minutes)

    # 根据IP地址查询最近N分钟的数据
    recent_data = MonitorData.get_by_ip(ip_address, start_time)

    if len(recent_data) < 3:  # 至少需要3个数据点
        return False

    # 获取阈值
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS[metric_type]
        
    alert_level = determine_alert_level(value, thresholds)

    if not alert_level:
        return False

    # 检查是否所有数据都超过对应阈值
    threshold_value = thresholds[alert_level]
    sustained_count = 0

    for data in recent_data:
        if metric_type == 'cpu' and float(data.cpu_value) >= threshold_value:
            sustained_count += 1
        elif metric_type == 'memory' and float(data.memory_value) >= threshold_value:
            sustained_count += 1
        elif metric_type == 'disk' and float(data.disk_value) >= threshold_value:
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
        alert_users = server.users # 之前的 get_alert_users() 似乎是 Server 类的方法，但 Server 模型并没有这个方法。
        # 检查 Server 模型是否有 get_alert_users, 之前的代码是 server.get_alert_users()
        # 但是在 server.py 中没有看到 get_alert_users 的定义，server.py 中只有 relationship users
        # 也许在 server.py 中有定义，但我没读全。
        # 如果没有，应该直接用 server.users
        users_to_alert = server.users if server.users else []
        
        if not users_to_alert:
            pass  # 服务器没有关联用户
            return False

        # 3. 获取告警阈值 (支持动态阈值)
        thresholds = get_server_thresholds(server, metric_type)

        # 4. 检查告警级别
        alert_level = determine_alert_level(value, thresholds)

        if alert_level:
            # 5. 检查是否持续超过阈值（2分钟）
            if not check_sustained_alert_by_ip(ip_address, metric_type, value, minutes=2, thresholds=thresholds):
                 # 如果没有达到持续告警条件，直接返回 True (视为已处理但忽略)
                 # 或者返回 False 表示未触发
                return True

            # 6. 向所有关联用户发送告警邮件
            success_count = 0
            
            # 使用 float 转换阈值，确保 AlertHistory 存储正确
            threshold_val = float(thresholds[alert_level])

            for user in users_to_alert:
                success = send_alert_email(
                    user.email,
                    server.server_name,
                    metric_type,
                    value,
                    alert_level,
                    threshold_val # 传递阈值给邮件模板
                )

                if success:
                    success_count += 1
                else:
                    pass  # 告警发送失败

            if success_count > 0:
                # [新增] 记录告警历史
                msg_content = f"服务器 {server.server_name} {metric_type} 告警: 当前值 {value}%, 阈值 {threshold_val}%"
                AlertHistory.create(
                    server_id=server.id,
                    metric_type=metric_type,
                    current_value=value,
                    threshold=threshold_val,
                    content=msg_content
                )
                pass  # 告警发送完成
            return success_count > 0
        else:
            return True

    except Exception as e:
        print(f"告警检查失败: {e}")
        pass  # 告警检查失败
        return False


# 确定告警级别
def determine_alert_level(value, thresholds):
    if value >= thresholds.get('emergency', 100):
        return 'emergency'
    elif value >= thresholds.get('critical', 100):
        return 'critical'
    elif value >= thresholds.get('warning', 100):
        return 'warning'
    return None


# 发送告警邮件
def send_alert_email(email, server_name, metric_type, value, level, threshold=None):
    try:
        import smtplib
        from email.mime.text import MIMEText

        if threshold is None:
             threshold = get_threshold_by_level(level, metric_type)

        # 生成告警消息
        # 简单处理，不再依赖复杂的 ALERT_TEMPLATES，或者确保 ALERT_TEMPLATES 兼容
        # 假设 ALERT_TEMPLATES 存在于 setting.py
        
        message = f"""
        【{level.upper()}】服务器监控告警
        
        服务器: {server_name}
        告警指标: {metric_type}
        当前数值: {value}%
        触发阈值: {threshold}%
        
        请及时处理。
        """

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
        print(f"发送邮件失败: {e}")
        pass  # 发送告警邮件失败
        return False


# 根据级别获取阈值 (保留辅助函数)
def get_threshold_by_level(level, metric_type):
    thresholds = DEFAULT_THRESHOLDS.get(metric_type, {})
    return thresholds.get(level, 0)

