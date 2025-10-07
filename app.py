from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from config.setting import DEBUG, HOST, PORT, JWT_SECRET_KEY
from lib.response import response


#应用工厂模式
def create_app():
    # 创建 Flask 应用实例（核心对象）
    app = Flask(__name__)
    # 从配置文件加载应用配置
    app.config.from_object('config.setting')
    print("当前数据库连接URI：", app.config.get('SQLALCHEMY_DATABASE_URI'))
    
    # 配置CORS跨域支持
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"], 
         allow_headers=["Content-Type", "Authorization"], 
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # 导入数据库连接对象
    from model.models import db
    # 将数据库对象绑定到Flask应用
    db.init_app(app)

    # 初始化数据库迁移功能flask -A main:app db init
    migrate = Migrate(app, db)

    # ==================== JWT认证配置 ====================
    # 设置JWT密钥
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    # 设置JWT Token过期时间
    # 开发环境：24小时，生产环境：1小时
    from config.setting import EXPIRES
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = EXPIRES
    
    # 初始化JWT管理器
    jwt = JWTManager(app)
    
    # 配置JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return response(message="Token已过期", code=401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return response(message="Token无效", code=401)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return response(message="缺少Token", code=401)

    # 导入并注册所有API路由蓝图
    # 包括认证、用户管理、服务器管理、监控数据等模块
    import router
    router.init_app(app)

    return app


# 创建Flask应用实例
app = create_app()
if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST, port=PORT)
