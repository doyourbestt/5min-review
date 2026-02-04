"""
5分钟快速复盘 - 复盘记录模型
============================
AI维护注意点:
1. 复盘记录不可修改，保持历史完整性
2. 答案以JSON存储，灵活支持各种字段类型
3. 关联模板删除时，复盘记录应保留但标记模板已删除
4. 查询性能考虑：按用户ID和时间范围建立复合索引
"""

from datetime import datetime
from extensions import db
import json

class Review(db.Model):
    """
    复盘记录模型
    存储用户每次复盘的完整数据
    """
    
    __tablename__ = 'reviews'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 关联模板 - AI维护注意点: 模板删除时设为NULL
    template_id = db.Column(db.Integer, db.ForeignKey('review_templates.id'), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)  # 冗余存储模板名
    
    # 复盘类型
    review_type = db.Column(db.String(20), default='daily', nullable=False)
    
    # 复盘标题 - AI维护注意点: 允许用户自定义标题
    title = db.Column(db.String(200), nullable=True)
    
    # 复盘日期 - 用于按日期筛选
    review_date = db.Column(db.Date, nullable=False, index=True)
    
    # 完成时长(分钟) - 统计使用
    duration_minutes = db.Column(db.Integer, default=5, nullable=False)
    
    # 总字数统计
    word_count = db.Column(db.Integer, default=0, nullable=False)
    
    # 完成标记
    is_completed = db.Column(db.Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系 - 级联删除所有答案
    answers = db.relationship('ReviewAnswer', backref='review', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def to_dict(self, include_answers=True):
        """
        转换为字典格式
        
        Args:
            include_answers: 是否包含答案详情
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'template_id': self.template_id,
            'template_name': self.template_name,
            'review_type': self.review_type,
            'title': self.title,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'duration_minutes': self.duration_minutes,
            'word_count': self.word_count,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'answer_count': self.answers.count()
        }
        
        if include_answers:
            data['answers'] = [answer.to_dict() for answer in self.answers.all()]
            
        return data
    
    def calculate_word_count(self):
        """
        计算复盘总字数
        AI维护注意点: 中文按字符计，英文按单词计
        """
        total = 0
        for answer in self.answers.all():
            if answer.answer_text:
                # 简单统计：中文按字符，英文按空格分割
                import re
                # 统计中文字符
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', answer.answer_text))
                # 统计英文单词(粗略)
                english_words = len(re.findall(r'[a-zA-Z]+', answer.answer_text))
                total += chinese_chars + english_words
        
        self.word_count = total
        return total
    
    @classmethod
    def get_user_reviews(cls, user_id, start_date=None, end_date=None, 
                        review_type=None, limit=None):
        """
        获取用户的复盘列表
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            review_type: 复盘类型筛选
            limit: 返回数量限制
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(cls.review_date >= start_date)
        if end_date:
            query = query.filter(cls.review_date <= end_date)
        if review_type:
            query = query.filter_by(review_type=review_type)
            
        query = query.order_by(cls.review_date.desc(), cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def get_daily_review(cls, user_id, review_date):
        """
        获取用户某日的复盘记录
        AI维护注意点: 每日复盘应唯一，如有多条取最新
        """
        return cls.query.filter_by(
            user_id=user_id, 
            review_date=review_date,
            review_type='daily'
        ).order_by(cls.created_at.desc()).first()


class ReviewAnswer(db.Model):
    """
    复盘答案模型
    存储复盘表单中每个字段的答案
    """
    
    __tablename__ = 'review_answers'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 关联复盘记录
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    
    # 字段信息 - AI维护注意点: 模板删除后仍能知道字段名
    field_name = db.Column(db.String(50), nullable=False)
    field_label = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)
    
    # 答案内容
    # AI维护注意点: 复杂类型(multiselect等)以JSON存储
    answer_text = db.Column(db.Text, nullable=True)
    
    # 用于筛选/统计的标准化值
    # AI维护注意点: rating类型存储为数字便于统计
    numeric_value = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        # 处理复杂类型的答案
        answer_value = self.answer_text
        if self.field_type in ['multiselect', 'checkbox'] and self.answer_text:
            try:
                answer_value = json.loads(self.answer_text)
            except json.JSONDecodeError:
                pass
        
        return {
            'id': self.id,
            'field_name': self.field_name,
            'field_label': self.field_label,
            'field_type': self.field_type,
            'answer': answer_value,
            'numeric_value': self.numeric_value
        }
    
    def set_answer(self, value, field_type):
        """
        设置答案值
        
        Args:
            value: 答案值
            field_type: 字段类型
            
        AI维护注意点: 不同字段类型需要不同处理
        """
        if field_type in ['multiselect', 'checkbox'] and isinstance(value, (list, dict)):
            self.answer_text = json.dumps(value, ensure_ascii=False)
        else:
            self.answer_text = str(value) if value is not None else None
        
        # 设置数值用于统计
        if field_type == 'rating':
            try:
                self.numeric_value = float(value)
            except (ValueError, TypeError):
                self.numeric_value = None
        elif field_type == 'number':
            try:
                self.numeric_value = float(value)
            except (ValueError, TypeError):
                self.numeric_value = None
    
    @classmethod
    def get_field_stats(cls, user_id, field_name, start_date=None, end_date=None):
        """
        获取某字段的统计信息
        AI维护注意点: 用于心情评分等趋势分析
        """
        from models.review import Review
        
        query = db.session.query(cls).join(Review).filter(
            Review.user_id == user_id,
            cls.field_name == field_name
        )
        
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
            
        answers = query.all()
        
        # 统计计算
        numeric_values = [a.numeric_value for a in answers if a.numeric_value is not None]
        
        if not numeric_values:
            return None
            
        return {
            'count': len(numeric_values),
            'avg': sum(numeric_values) / len(numeric_values),
            'min': min(numeric_values),
            'max': max(numeric_values)
        }
