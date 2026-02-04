"""
5分钟快速复盘 - 用户模型
=======================
AI维护注意点:
1. 密码使用werkzeug.security加密，不可逆
2. 用户状态字段影响登录权限校验
3. 删除用户需考虑级联操作(模板/复盘记录)
4. 邮箱字段建议添加唯一索引和验证
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# AI维护注意点: 从extensions模块导入db避免循环导入
from extensions import db

class User(db.Model):
    """
    用户模型
    存储用户账户信息和认证数据
    """
    
    # 表名定义
    __tablename__ = 'users'
    
    # 主键ID - AI维护注意点: 使用自增整数ID，UUID可作为替代方案
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 用户基本信息
    # AI维护注意点: username限制长度需与前端表单校验一致
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # 密码字段 - 存储加密后的哈希值
    # AI维护注意点: 永远不要存储明文密码
    password_hash = db.Column(db.String(256), nullable=False)
    
    # 用户状态
    # AI维护注意点: 软删除使用is_active=False，保留数据便于审计
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 最后登录时间 - 用于统计活跃用户
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # 关系定义 - AI维护注意点: cascade行为需谨慎设置
    templates = db.relationship('ReviewTemplate', backref='creator', lazy='dynamic',
                                cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        设置用户密码
        
        Args:
            password: 明文密码
            
        AI维护注意点: 密码强度校验应在调用此方法前完成
        """
        # 使用werkzeug生成安全哈希
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """
        验证密码
        
        Args:
            password: 明文密码
            
        Returns:
            bool: 密码是否匹配
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """
        转换为字典格式
        
        Args:
            include_sensitive: 是否包含敏感信息(如email)
            
        Returns:
            dict: 用户数据字典
            
        AI维护注意点: API响应默认不应包含敏感字段
        """
        data = {
            'id': self.id,
            'username': self.username,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data['email'] = self.email
            
        return data
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def find_by_username(cls, username):
        """
        根据用户名查找用户
        
        AI维护注意点: 用户名查询不区分大小写
        """
        return cls.query.filter(db.func.lower(cls.username) == username.lower()).first()
    
    @classmethod
    def find_by_email(cls, email):
        """根据邮箱查找用户"""
        return cls.query.filter_by(email=email).first()
    
    def __repr__(self):
        return f'<User {self.username}>'
