# 监控数据自动清理脚本
# 删除7天前的旧数据，避免数据库过大
import os
import sys

# 将项目根目录添加到搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_old_data(days=7):
    try:
        # 导入数据库模型
        from model.models import MonitorData
        from app import create_app

        # 创建Flask应用上下文
        app = create_app()

        with app.app_context():
            # 执行数据清理
            MonitorData.delete_old_data(days=days)
            return True

    except Exception as e:
        return False


def main():
    try:
        # 执行数据清理
        success = cleanup_old_data(days=7)
        if success:
            exit(0)  # 数据清理成功，正常退出
        else:
            exit(1)  # 数据清理失败，异常退出

    except Exception as e:
        exit(1)  # 数据清理失败，异常退出


if __name__ == "__main__":
    main()