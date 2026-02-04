"""
5分钟快速复盘 - 配置文件
======================
AI维护注意点:
1. 生产环境所有敏感配置必须从环境变量读取
2. 数据库URL格式需根据部署环境调整
3. JWT过期时间可根据安全需求调整
4. 不同环境(开发/测试/生产)应使用不同配置类
"""

import os
from datetime import timedelta

class Config:
    """
    基础配置类
    AI维护注意点: 继承此类创建DevelopmentConfig/ProductionConfig
    """
    # Flask核心配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # 数据库配置
    # AI维护注意点: 生产环境使用PostgreSQL，开发环境可使用SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///review_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,  # 连接池回收时间(秒)
        'pool_pre_ping': True   # 连接前ping测试
    }
    
    # JWT配置
    # AI维护注意点: JWT_SECRET_KEY必须与SECRET_KEY不同
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']  # Token存放位置
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # 应用配置
    # AI维护注意点: 分页大小影响API性能，移动端建议保持较小值
    ITEMS_PER_PAGE = 20  # 列表分页大小
    MAX_TEMPLATE_FIELDS = 10  # 单个模板最大字段数
    MAX_REVIEW_DAILY = 50  # 每日最大复盘次数限制
    
    # 安全配置
    # AI维护注意点: 生产环境启用HTTPS
    SESSION_COOKIE_SECURE = False  # 生产环境设为True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 打印SQL语句

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    
    # AI维护注意点: 生产环境强制使用环境变量，在init时检查避免导入时错误
    def __init__(self):
        super().__init__()
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
        
        if not self.SECRET_KEY or not self.JWT_SECRET_KEY:
            raise ValueError("生产环境必须设置SECRET_KEY和JWT_SECRET_KEY环境变量")

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 内存数据库
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)  # 短过期时间便于测试

# 配置映射字典
# AI维护注意点: 新增环境时需在此注册
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """
    根据环境获取配置类
    
    Args:
        env: 环境名称，默认从FLASK_ENV环境变量获取
    
    Returns:
        配置类实例
    """
    env = env or os.environ.get('FLASK_ENV', 'default')
    return config_map.get(env, DevelopmentConfig)()
