import sys
import os

# 将项目根目录添加到搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from model import User, db

def create_admin_user(username, password, email):
    app = create_app()
    with app.app_context():
        # 检查用户是否存在
        existing_user = User.get_by_username(username)
        if existing_user:
            print(f"用户 {username} 已存在，跳过创建。")
            return

        try:
            # 创建管理员用户
            User.create(username=username, password=password, email=email, role='admin')
            print(f"管理员用户 {username} 创建成功！")
        except Exception as e:
            print(f"创建用户失败: {str(e)}")

if __name__ == "__main__":
    # 默认创建一个 admin / 123456 的管理员账号
    create_admin_user('admin', '123456', 'admin@example.com')
