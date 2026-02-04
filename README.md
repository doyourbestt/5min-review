# 5分钟快速复盘

一个帮助用户每天花5分钟进行复盘记录的Web应用，支持自定义模板、打卡统计、数据可视化等功能。

## 功能特性

- **快速复盘**：5分钟内完成每日复盘，养成好习惯
- **自定义模板**：支持创建多种复盘模板（每日/每周/项目/自定义）
- **打卡系统**：日历热力图展示打卡记录，激励持续复盘
- **数据统计**：复盘次数、连续打卡天数、累计字数等核心指标
- **数据安全**：JWT认证，复盘数据私密存储

## 技术栈

### 后端
- **框架**: Flask 2.3.3 + Python 3.8+
- **数据库**: SQLAlchemy ORM (SQLite/PostgreSQL)
- **认证**: Flask-JWT-Extended
- **API**: RESTful API设计

### 前端
- **框架**: Vue 3.3 + Composition API
- **构建**: Vite 4.4
- **状态**: Pinia 2.1
- **路由**: Vue Router 4.2
- **HTTP**: Axios
- **日期**: Day.js

## 项目结构

```
.
├── backend/               # Flask后端
│   ├── app.py            # 应用主入口
│   ├── config.py         # 配置文件
│   ├── models/           # 数据模型
│   │   ├── user.py       # 用户模型
│   │   ├── template.py   # 模板模型
│   │   └── review.py     # 复盘模型
│   ├── routes/           # API路由
│   │   ├── auth.py       # 认证接口
│   │   ├── templates.py  # 模板接口
│   │   ├── reviews.py    # 复盘接口
│   │   └── stats.py      # 统计接口
│   └── requirements.txt  # Python依赖
│
├── frontend/              # Vue前端
│   ├── index.html        # HTML入口
│   ├── package.json      # Node依赖
│   ├── vite.config.js    # Vite配置
│   └── src/
│       ├── main.js       # 应用入口
│       ├── App.vue       # 根组件
│       ├── router/       # 路由配置
│       ├── views/        # 页面组件
│       ├── stores/       # Pinia状态
│       └── api/          # API封装
│
├── README.md             # 项目说明
├── DEPLOY.md             # 部署指南
└── ROADMAP.md            # 迭代规划
```

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd 5分钟快速复盘网页
```

### 2. 启动后端
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```
后端服务运行在 http://localhost:5000

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```
前端服务运行在 http://localhost:5173

## 默认账号

注册新账号即可使用，无需预设账号。

## 开发规范

### AI维护注意点
1. 所有代码文件包含详细的注释说明
2. 关键配置和注意事项标记为"AI维护注意点"
3. 模块间低耦合设计，便于独立维护
4. 数据库模型变更需同步更新Alembic迁移

### 代码规范
- **Python**: PEP8规范，使用4空格缩进
- **JavaScript**: ESLint + Prettier配置
- **Git**: 提交信息遵循Conventional Commits

## 环境变量

### 后端 (.env)
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite:///review_app.db
```

### 前端 (.env)
```env
VITE_API_BASE_URL=http://localhost:5000
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，欢迎提交 Issue 或 PR。

---

**AI维护注意点**: 此README为项目主要文档，更新功能时需同步更新。
