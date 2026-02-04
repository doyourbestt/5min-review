"""
5分钟快速复盘 - 可视化模块数据模型
==================================
核心表：复盘日、分享者、干货条目、点赞
AI维护注意点:
1. 分享者独立表，便于头像管理
2. 干货按天+分享者双重关联
3. 点赞使用设备指纹防重复
4. 所有表都有created_at，方便追溯
"""

from datetime import datetime
from extensions import db


class ReviewDay(db.Model):
    """
    复盘日表
    按天聚合所有复盘数据
    """
    __tablename__ = 'review_days'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)  # 复盘日期
    title = db.Column(db.String(200))  # 复盘标题（从markdown提取）
    raw_content = db.Column(db.Text)   # 原始markdown文本（备份）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    insights = db.relationship('Insight', backref='review_day', lazy='dynamic',
                             cascade='all, delete-orphan')


class Sharer(db.Model):
    """
    分享者表
    存储所有分享过干货的成员信息
    
    AI维护注意点:
    1. name唯一，防止重复创建
    2. avatar_url可为空，使用默认头像
    3. 不与具体某天的复盘绑定，是全局数据
    """
    __tablename__ = 'sharers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    avatar_url = db.Column(db.String(500))  # 头像路径，如 "/static/avatars/李阳州.jpg"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    insights = db.relationship('Insight', backref='sharer', lazy='dynamic')


class Insight(db.Model):
    """
    干货条目表
    存储每条复盘干货
    
    AI维护注意点:
    1. 与ReviewDay和Sharer都建立外键
    2. emoji存储在干货级别（不同天可能有不同表情）
    3. likes冗余存储，避免频繁查询like表
    """
    __tablename__ = 'insights'
    
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey('review_days.id'), nullable=False, index=True)
    sharer_id = db.Column(db.Integer, db.ForeignKey('sharers.id'), nullable=False, index=True)
    
    emoji = db.Column(db.String(10))        # 表情符号，如 "🕰️"
    topic = db.Column(db.String(100))       # 主题，如 "时间价值化魔法"
    content = db.Column(db.Text, nullable=False)  # 详细内容
    
    likes = db.Column(db.Integer, default=0)  # 冗余存储，优化查询
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    like_records = db.relationship('Like', backref='insight', lazy='dynamic',
                                   cascade='all, delete-orphan')


class Like(db.Model):
    """
    点赞记录表
    记录每条干货的点赞详情
    
    AI维护注意点:
    1. 使用device_id（设备指纹）+ insight_id联合唯一，防重复点赞
    2. liker_nickname可选，增加社交属性但不强制
    3. 大量数据时可考虑分表或归档
    """
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    insight_id = db.Column(db.Integer, db.ForeignKey('insights.id'), nullable=False, index=True)
    
    liker_nickname = db.Column(db.String(50))  # 点赞者昵称（可选）
    device_id = db.Column(db.String(64), nullable=False)  # 设备指纹（必填）
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 联合唯一约束：同一设备不能对同一条干货重复点赞
    __table_args__ = (
        db.UniqueConstraint('insight_id', 'device_id', name='unique_device_like'),
    )
