# 部署指南

本文档介绍如何将「5分钟快速复盘」项目部署到生产环境。

## 部署方式

### 方式一：传统服务器部署

#### 1. 环境准备

**服务器要求**
- OS: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- Python: 3.8+
- Node.js: 16+
- Web服务器: Nginx (推荐) / Apache

#### 2. 后端部署

```bash
# 1. 进入后端目录
cd /var/www/5min-review/backend

# 2. 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置生产环境配置

# 5. 数据库迁移（如使用PostgreSQL）
# flask db upgrade

# 6. 使用Gunicorn启动
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
```

**环境变量配置 (.env)**
```env
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-min-32-chars
JWT_SECRET_KEY=your-different-jwt-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/review_db
LOG_LEVEL=INFO
```

#### 3. 前端部署

```bash
# 1. 进入前端目录
cd /var/www/5min-review/frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量
echo "VITE_API_BASE_URL=/api" > .env.production

# 4. 构建
npm run build

# 5. 构建产物在 dist/ 目录
```

#### 4. Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/5min-review/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1M;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 5. 使用Systemd管理服务

创建 `/etc/systemd/system/5min-review.service`:

```ini
[Unit]
Description=5min Review Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/5min-review/backend
Environment="PATH=/var/www/5min-review/backend/venv/bin"
EnvironmentFile=/var/www/5min-review/backend/.env
ExecStart=/var/www/5min-review/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl enable 5min-review
sudo systemctl start 5min-review
sudo systemctl status 5min-review
```

### 方式二：Docker部署

#### 1. 创建Dockerfile

**后端 Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**前端 Dockerfile**
```dockerfile
FROM node:16-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 2. Docker Compose配置

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: review_user
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: review_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://review_user:your_password@db:5432/review_db
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - db
    ports:
      - "5000:5000"
    
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

#### 3. 启动服务

```bash
docker-compose up -d
```

### 方式三：云平台部署

### 方式三：云平台部署

#### Vercel (前端) + Railway/Render (后端)

1. **前端部署到Vercel**
   - 连接GitHub仓库
   - 设置构建命令: `npm run build`
   - 输出目录: `dist`
   - 环境变量: `VITE_API_BASE_URL=https://your-api-domain.com`

2. **后端部署到Railway/Render**
   - 选择Python环境
   - 设置启动命令: `gunicorn -w 4 app:app`
   - 配置环境变量
   - 添加PostgreSQL插件

#### Render部署指南（免费，推荐）

Render提供每月750小时免费运行时，适合小规模部署。

**1. 准备代码仓库**
```bash
# 确保代码已推送到GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main
```

**2. 创建后端服务（Web Service）**

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 "New +" → "Web Service"
3. 连接到你的GitHub仓库
4. 配置：
   - Name: `5min-review-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
   - Plan: `Free`

5. 添加环境变量（Advanced → Environment Variables）：
   ```
   FLASK_ENV=production
   SECRET_KEY=your-random-secret-key (32+字符)
   JWT_SECRET_KEY=your-jwt-secret-key
   DATABASE_URL=sqlite:///review_app.db
   ```

6. 点击 "Create Web Service"

**3. 创建前端服务（Static Site）**

1. 点击 "New +" → "Static Site"
2. 连接到GitHub仓库
3. 配置：
   - Name: `5min-review-frontend`
   - Build Command: `npm run build`
   - Publish Directory: `frontend/dist`
   - Plan: `Free`

4. 添加环境变量（Settings → Environment Variables）：
   ```
   VITE_API_BASE_URL=https://your-backend-service.onrender.com
   ```

5. 点击 "Create Static Site"

**4. 配置跨域（CORS）**

Render免费版的Web Service需要配置CORS：

编辑 `backend/app.py` 中的CORS配置：
```python
cors = CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173", 
            "https://your-frontend.onrender.com"  # 前端地址
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

**5. 访问应用**

- 前端地址: `https://your-frontend.onrender.com`
- 后端API: `https://your-backend-service.onrender.com`

**6. 注意事项**

1. **免费版限制**：
   - 15分钟无活动自动休眠
   - 每月750小时运行时
   - 睡眠后首次访问需等待30-60秒

2. **数据库**：
   - 免费版使用SQLite（开发没问题）
   - 生产建议用Render PostgreSQL（免费额度内）

3. **头像存储**：
   - 当前本地存储（static/avatars）
   - 建议迁移到云存储（阿里云OSS/腾讯云COS）

**7. 监控与日志**

- 查看日志：Render Dashboard → 你的服务 → Logs
- 性能监控：Render Dashboard → 你的服务 → Insights

---

#### Heroku部署

```bash
# 1. 安装Heroku CLI并登录
heroku login

# 2. 创建应用
heroku create 5min-review-app

# 3. 添加PostgreSQL
heroku addons:create heroku-postgresql:mini

# 4. 设置环境变量
heroku config:set SECRET_KEY=your-secret
heroku config:set JWT_SECRET_KEY=your-jwt-secret

# 5. 创建Procfile
echo "web: gunicorn -w 4 app:app" > backend/Procfile

# 6. 推送部署
git push heroku main
```

## 安全建议

### 1. HTTPS配置
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # ... 其他配置
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. 数据库安全
- 使用强密码
- 限制数据库访问IP
- 定期备份数据
- 启用SSL连接

### 3. 环境变量安全
- 不要将.env文件提交到Git
- 使用密钥管理服务（如AWS KMS）
- 定期轮换密钥

## 监控与日志

### 1. 日志配置
```python
# backend/config.py
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### 2. 监控建议
- 使用Sentry监控错误
- 配置Uptime监控
- 设置数据库连接池监控
- 记录API响应时间

## 备份策略

### 数据库备份
```bash
# 每日自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U user -d review_db > /backup/review_db_$DATE.sql
# 保留最近30天备份
find /backup -name "review_db_*.sql" -mtime +30 -delete
```

### 文件备份
- 使用rsync同步到备份服务器
- 或使用云存储（AWS S3, 阿里云OSS）

## 性能优化

### 1. 启用Gzip压缩
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml;
```

### 2. 数据库优化
- 添加索引：复盘表按用户ID+日期
- 定期清理过期数据
- 使用连接池

### 3. 缓存策略
- 首页数据Redis缓存5分钟
- 统计数据每日更新一次
- 静态资源CDN加速

## 故障排查

### 常见问题

1. **后端无法启动**
   - 检查端口占用: `netstat -tulpn | grep 5000`
   - 检查环境变量: `echo $SECRET_KEY`
   - 查看日志: `journalctl -u 5min-review`

2. **前端API请求失败**
   - 检查API地址配置
   - 检查CORS配置
   - 查看浏览器Network面板

3. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查防火墙设置

## AI维护注意点

1. **生产环境部署前必读**
   - 修改所有默认密钥
   - 关闭DEBUG模式
   - 配置正确的数据库URL
   - 设置正确的ALLOWED_HOSTS/CORS

2. **部署后检查清单**
   - [ ] HTTPS正常工作
   - [ ] API响应正常
   - [ ] 数据库连接稳定
   - [ ] 日志记录正常
   - [ ] 备份任务运行中

3. **升级注意事项**
   - 备份数据库后再升级
   - 阅读CHANGELOG了解变更
   - 先在测试环境验证
   - 制定回滚计划

---

**最后更新**: 2026-02-03
