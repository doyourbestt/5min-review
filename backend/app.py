# -*- coding: utf-8 -*-
"""
5分钟快速复盘 - Flask后端应用主入口
======================================
AI维护注意点:
1. 数据库连接配置在config.py中，修改数据库类型时需要同步更新
2. JWT密钥需要定期轮换，建议每90天更换一次
3. CORS配置生产环境需要限制具体域名，当前为开发环境配置
4. 注册蓝图时注意URL前缀冲突
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import timedelta
import os

# 从扩展模块导入（避免循环导入）
from extensions import db, jwt

# 初始化Flask应用实例
app = Flask(__name__, static_folder='static')

# 静态文件目录（头像存储）
static_dir = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(os.path.join(static_dir, 'avatars'), exist_ok=True)

# 从环境变量或配置文件加载配置
# AI维护注意点: 直接导入本地config模块
from config import Config
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)
jwt.init_app(app)
cors = CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://5min-review-frontend.onrender.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 注册错误处理
@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({"error": "接口不存在", "code": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误并回滚数据库"""
    db.session.rollback()
    return jsonify({"error": "服务器内部错误", "code": 500}), 500

# 延迟导入路由避免循环依赖
# AI维护注意点: 蓝图注册顺序影响中间件执行顺序
with app.app_context():
    from routes.auth import auth_bp
    from routes.templates import templates_bp
    from routes.reviews import reviews_bp
    from routes.stats import stats_bp
    from routes.visualization import viz_router
    
    # 注册蓝图 - URL前缀统一管理
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(viz_router)
    
    # 创建所有数据库表
    # AI维护注意点: 生产环境应使用Alembic进行数据库迁移，不要auto create
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "5min-review-api",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    # AI维护注意点: 生产环境应使用gunicorn/uwsgi，禁用debug模式
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
