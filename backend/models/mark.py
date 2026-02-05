"""
5分钟快速复盘 - 复盘标记数据模型
================================
AI维护注意点:
1. 解析后的复盘标记存储
2. 支持公开分享链接
"""

from extensions import db
from datetime import datetime
import uuid


class MarkCard(db.Model):
    """复盘标记卡片"""
    __tablename__ = 'mark_cards'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), default='')
    content = db.Column(db.Text, nullable=False)
    share_token = db.Column(db.String(36), unique=True, index=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'name': self.name,
            'emoji': self.emoji or '',
            'content': self.content,
            'is_public': self.is_public,
            'share_token': self.share_token,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
