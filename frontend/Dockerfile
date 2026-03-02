# 第一阶段：构建前端应用
FROM node:20-alpine AS build-stage

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci --registry=https://registry.npmmirror.com

# 复制源代码
COPY . .

# 构建项目
RUN npm run build

# 第二阶段：用 Nginx 托管构建产物
FROM nginx:alpine AS production-stage

# 移除默认的 Nginx 配置
# RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义 Nginx 配置（如果需要 ConfigMap 挂载，这里可以先用一个默认的，或者不复制也行，让 K8s 覆盖）
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建输出到 Nginx 的 HTML 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
