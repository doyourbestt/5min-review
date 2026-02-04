"""
5分钟快速复盘 - 模型包初始化
============================
AI维护注意点:
1. 新增模型需在此导入以确保Alembic能检测到
2. 模型关系定义顺序影响外键约束创建
3. 数据库迁移前确认所有模型导入正确
"""

from models.user import User
from models.template import ReviewTemplate, TemplateField
from models.review import Review, ReviewAnswer
from models.visualization import ReviewDay, Sharer, Insight, Like

# AI维护注意点: 导出所有模型供Alembic使用
__all__ = [
    'User',
    'ReviewTemplate', 
    'TemplateField',
    'Review',
    'ReviewAnswer',
    'ReviewDay',
    'Sharer',
    'Insight',
    'Like'
]
