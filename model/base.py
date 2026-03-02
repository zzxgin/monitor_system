from flask_sqlalchemy import SQLAlchemy

# 创建 ORM 核心对象，后续所有数据库操作（定义表结构、增删改查）都通过这个对象实现。
db = SQLAlchemy()
