"""
5分钟快速复盘 - 复盘模板模型
============================
AI维护注意点:
1. 模板与用户多对一关系，删除用户影响其模板
2. 字段顺序(order_index)用于前端展示排序
3. 字段类型限制前端输入控件类型
4. 系统预设模板is_system=True，普通用户不可修改
"""

from datetime import datetime
from extensions import db
import json

class ReviewTemplate(db.Model):
    """
    复盘模板模型
    定义复盘表单的结构和字段
    """
    
    __tablename__ = 'review_templates'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 模板元信息
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # 所属用户 - AI维护注意点: 系统模板user_id可为NULL
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # 模板类型
    # AI维护注意点: daily=每日, weekly=每周, project=项目, custom=自定义
    template_type = db.Column(db.String(20), default='daily', nullable=False)
    
    # 系统预设标记
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    
    # 是否公开分享
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    
    # 使用统计
    use_count = db.Column(db.Integer, default=0, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系 - 级联删除所有字段
    fields = db.relationship('TemplateField', backref='template', lazy='dynamic',
                            cascade='all, delete-orphan', order_by='TemplateField.order_index')
    reviews = db.relationship('Review', backref='template', lazy='dynamic')
    
    def to_dict(self, include_fields=True):
        """
        转换为字典格式
        
        Args:
            include_fields: 是否包含字段详情
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'is_system': self.is_system,
            'is_public': self.is_public,
            'user_id': self.user_id,
            'use_count': self.use_count,
            'field_count': self.fields.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_fields:
            data['fields'] = [field.to_dict() for field in self.fields.all()]
            
        return data
    
    def increment_use_count(self):
        """增加使用计数"""
        self.use_count += 1
        db.session.commit()
    
    def can_edit(self, user_id):
        """
        检查用户是否有编辑权限
        
        AI维护注意点: 系统模板只有管理员可编辑
        """
        if self.is_system:
            # 检查是否为管理员
            from backend.models.user import User
            user = User.query.get(user_id)
            return user and user.is_admin
        return self.user_id == user_id
    
    @classmethod
    def get_system_templates(cls):
        """获取所有系统预设模板"""
        return cls.query.filter_by(is_system=True).all()
    
    @classmethod
    def get_user_templates(cls, user_id, include_system=True):
        """
        获取用户的模板列表
        
        Args:
            user_id: 用户ID
            include_system: 是否包含系统模板
        """
        query = cls.query.filter(
            db.or_(
                cls.user_id == user_id,
                cls.is_public == True
            )
        )
        
        if include_system:
            query = query.union(cls.query.filter_by(is_system=True))
            
        return query.order_by(cls.is_system.desc(), cls.created_at.desc()).all()


class TemplateField(db.Model):
    """
    模板字段模型
    定义复盘表单中的单个输入项
    """
    
    __tablename__ = 'template_fields'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 关联模板
    template_id = db.Column(db.Integer, db.ForeignKey('review_templates.id'), nullable=False)
    
    # 字段属性
    name = db.Column(db.String(50), nullable=False)  # 字段标识名
    label = db.Column(db.String(100), nullable=False)  # 显示标签
    field_type = db.Column(db.String(20), nullable=False)  # 类型
    
    # AI维护注意点: 支持的字段类型
    # text: 单行文本, textarea: 多行文本, number: 数字
    # select: 单选, multiselect: 多选, date: 日期
    # rating: 评分(1-5星), checkbox: 复选框
    
    # 字段配置(JSON存储)
    # AI维护注意点: options用于select/multiselect类型
    config = db.Column(db.Text, nullable=True)
    
    # 是否必填
    required = db.Column(db.Boolean, default=False, nullable=False)
    
    # 显示顺序
    order_index = db.Column(db.Integer, default=0, nullable=False)
    
    # 默认值
    default_value = db.Column(db.Text, nullable=True)
    
    # 占位提示文本
    placeholder = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        config_data = {}
        if self.config:
            try:
                config_data = json.loads(self.config)
            except json.JSONDecodeError:
                pass
        
        return {
            'id': self.id,
            'name': self.name,
            'label': self.label,
            'field_type': self.field_type,
            'config': config_data,
            'required': self.required,
            'order_index': self.order_index,
            'default_value': self.default_value,
            'placeholder': self.placeholder
        }
    
    @classmethod
    def validate_field_type(cls, field_type):
        """
        验证字段类型是否有效
        
        AI维护注意点: 新增字段类型时需更新此列表
        """
        valid_types = ['text', 'textarea', 'number', 'select', 
                      'multiselect', 'date', 'rating', 'checkbox']
        return field_type in valid_types
