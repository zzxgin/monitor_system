# 服务器监控系统（flask_monitor）

基于 Flask 开发的轻量级服务器监控平台，适用于中小型企业内部网络。系统能够集中管理多台服务器的资源使用情况，并对异常状态进行邮件告警。

## 🚀 功能概览

- **用户与认证**
  - 管理员登录（JWT）
  - 用户 CRUD（新增/查询/编辑/删除）
  - 当前用户信息查询与密码重置
- **服务器管理**
  - 服务器 CRUD 操作
  - 用户与服务器的多对多关联维护
  - 查询用户所关联的服务器列表
- **监控数据**
  - Agent 通过 API 上报 CPU/内存/磁盘等资源数据（带授权认证）
  - 查询所有服务器的最新监控数据
  - 统计展示每台服务器的资源使用率并与阈值对比
- **告警与通知**
  - 支持 CPU/内存/磁盘阈值告警
  - 超阈值时发送邮件给关联用户
  - 阈值通过配置文件调整
- **安全与跨域**
  - JWT 登录验证与 API 授权认证
  - Flask-CORS 实现跨域访问
- **维护脚本**
  - 定期清理历史监控数据（`scripts/cleanup_data.py`）

## 📁 项目结构

```
monitor_system/
├── app.py                    # Flask应用入口
├── config/                   # 配置文件
├── model/                    # SQLAlchemy 数据模型
├── router/                   # 各模块路由
├── lib/                      # 工具类（认证、响应封装等）
├── mail/                     # 告警邮件模块
├── migrations/               # 数据库迁移文件
├── frontend/                 # Vue 3 前端项目
├── scripts/                  # 维护脚本与客户端
│   ├── monitor_client.py     # 监控 Agent 示例
│   └── cleanup_data.py       # 清理脚本
├── requirements.txt          # Python 依赖
└── README.md                 # 项目说明（当前文件）
```

## 🛠️ 快速开始

1. 克隆仓库并进入目录：
   ```bash
   git clone <repo-url> monitor_system
   cd monitor_system
   ```
2. 创建并激活 Python 虚拟环境：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   source .venv/bin/activate    # macOS/Linux
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 配置环境变量：
   复制 `.env.example` 为 `.env`，并填写数据库、JWT、邮件等信息
   ```bash
   cp .env.example .env
   # Windows: copy .env.example .env
   ```
5. 初始化数据库并执行迁移：
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
6. 运行后端服务：
   ```bash
   python app.py
   ```
7. 启动前端（进入 `frontend` 目录）：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📬 运行监控 Agent

编辑 `scripts/monitor_client.py` 中的服务器地址和授权信息，执行：
```bash
python scripts/monitor_client.py
```

## 📦 部署建议

- 使用 Gunicorn 或 uWSGI 作为生产 WSGI 服务器
- Nginx 做反向代理与静态文件托管
- 前端构建后部署到同一域名下的子目录或 CDN
- 配置定时任务（Cron/Windows Task Scheduler）执行 `scripts/cleanup_data.py`



