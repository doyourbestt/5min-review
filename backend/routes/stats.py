"""
5分钟快速复盘 - 统计路由
======================
AI维护注意点:
1. 统计查询注意性能优化，避免全表扫描
2. 大数据量时需考虑缓存或异步计算
3. 时间范围查询需建立合适索引
4. 统计结果可缓存以减少数据库压力
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, extract, and_
from datetime import datetime, date, timedelta
import calendar

from models.review import Review, ReviewAnswer
from models.template import ReviewTemplate
from extensions import db

# 创建蓝图
stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview_stats():
    """
    获取复盘概览统计
    
    GET /api/stats/overview
    
    Returns:
        总复盘次数、连续打卡天数、总字数等核心指标
    
    AI维护注意点: 此接口调用频繁，考虑添加缓存
    """
    current_user_id = get_jwt_identity()
    
    # 基础统计
    total_reviews = Review.query.filter_by(user_id=current_user_id).count()
    total_words = db.session.query(func.sum(Review.word_count)).filter(
        Review.user_id == current_user_id
    ).scalar() or 0
    
    # 连续打卡天数
    streak = calculate_streak(current_user_id)
    
    # 本月统计
    today = date.today()
    month_start = today.replace(day=1)
    month_reviews = Review.query.filter(
        Review.user_id == current_user_id,
        Review.review_date >= month_start
    ).count()
    
    # 今日是否打卡
    has_review_today = Review.query.filter_by(
        user_id=current_user_id,
        review_date=today
    ).first() is not None
    
    return jsonify({
        "total_reviews": total_reviews,
        "total_words": int(total_words),
        "current_streak": streak,
        "month_reviews": month_reviews,
        "has_review_today": has_review_today,
        "last_updated": datetime.utcnow().isoformat()
    }), 200


def calculate_streak(user_id):
    """
    计算连续打卡天数
    
    AI维护注意点: 从昨天开始往前计算，今天已打卡则+1
    """
    today = date.today()
    streak = 0
    check_date = today
    
    # 检查今天是否已打卡
    if Review.query.filter_by(user_id=user_id, review_date=today).first():
        streak = 1
        check_date = today - timedelta(days=1)
    else:
        check_date = today - timedelta(days=1)
    
    # 往前计算
    while True:
        if Review.query.filter_by(user_id=user_id, review_date=check_date).first():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return streak


@stats_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_stats():
    """
    获取日历热力图数据
    
    GET /api/stats/calendar?year=2024&month=1
    
    AI维护注意点: 返回整月数据用于日历展示
    """
    current_user_id = get_jwt_identity()
    
    # 获取年月参数
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # 计算日期范围
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # 查询该月复盘
    reviews = Review.query.filter(
        Review.user_id == current_user_id,
        Review.review_date >= start_date,
        Review.review_date <= end_date
    ).all()
    
    # 按日期聚合
    daily_stats = {}
    for review in reviews:
        date_str = review.review_date.strftime('%Y-%m-%d')
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                "count": 0,
                "word_count": 0,
                "has_review": True
            }
        daily_stats[date_str]["count"] += 1
        daily_stats[date_str]["word_count"] += review.word_count
    
    return jsonify({
        "year": year,
        "month": month,
        "daily_stats": daily_stats,
        "month_total": len(daily_stats),
        "days_in_month": last_day
    }), 200


@stats_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends_stats():
    """
    获取复盘趋势数据
    
    GET /api/stats/trends?days=30
    
    AI维护注意点: 用于折线图展示复盘频率趋势
    """
    current_user_id = get_jwt_identity()
    
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)  # 最多365天
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # 查询每日复盘数
    daily_counts = db.session.query(
        Review.review_date,
        func.count(Review.id).label('count'),
        func.sum(Review.word_count).label('words')
    ).filter(
        Review.user_id == current_user_id,
        Review.review_date >= start_date,
        Review.review_date <= end_date
    ).group_by(Review.review_date).order_by(Review.review_date).all()
    
    # 构建完整日期序列
    trends = []
    current = start_date
    counts_map = {r[0]: (r[1], r[2] or 0) for r in daily_counts}
    
    while current <= end_date:
        count, words = counts_map.get(current, (0, 0))
        trends.append({
            "date": current.isoformat(),
            "count": count,
            "word_count": int(words),
            "has_review": count > 0
        })
        current += timedelta(days=1)
    
    return jsonify({
        "trends": trends,
        "days": days,
        "active_days": len(daily_counts),
        "avg_words_per_day": sum(t["word_count"] for t in trends) // days if days > 0 else 0
    }), 200


@stats_bp.route('/fields', methods=['GET'])
@jwt_required()
def get_field_stats():
    """
    获取字段统计(用于评分类字段分析)
    
    GET /api/stats/fields?field_name=mood&days=30
    
    AI维护注意点: 主要用于rating/number类型字段的趋势分析
    """
    current_user_id = get_jwt_identity()
    
    field_name = request.args.get('field_name')
    days = request.args.get('days', 30, type=int)
    
    if not field_name:
        return jsonify({"error": "field_name为必填参数"}), 400
    
    days = min(days, 90)  # 最多90天
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # 查询该字段的答案
    answers = db.session.query(ReviewAnswer, Review).join(Review).filter(
        Review.user_id == current_user_id,
        Review.review_date >= start_date,
        Review.review_date <= end_date,
        ReviewAnswer.field_name == field_name,
        ReviewAnswer.numeric_value != None
    ).order_by(Review.review_date).all()
    
    if not answers:
        return jsonify({
            "field_name": field_name,
            "message": "该时间段没有相关数据",
            "data": []
        }), 200
    
    # 统计数据
    values = [a[0].numeric_value for a in answers]
    data_points = [{
        "date": a[1].review_date.isoformat(),
        "value": a[0].numeric_value,
        "answer": a[0].answer_text
    } for a in answers]
    
    return jsonify({
        "field_name": field_name,
        "field_label": answers[0][0].field_label,
        "count": len(values),
        "average": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values),
        "data": data_points
    }), 200


@stats_bp.route('/wordcloud', methods=['GET'])
@jwt_required()
def get_wordcloud_data():
    """
    获取词云数据(简单频率统计)
    
    GET /api/stats/wordcloud?limit=50
    
    AI维护注意点: 实际项目中应接入NLP服务进行分词和关键词提取
    """
    current_user_id = get_jwt_identity()
    limit = request.args.get('limit', 50, type=int)
    
    # 获取最近100条复盘的文本内容
    recent_reviews = Review.query.filter_by(user_id=current_user_id).order_by(
        Review.created_at.desc()
    ).limit(100).all()
    
    # 简单词频统计(中文需要jieba分词，这里简化处理)
    word_freq = {}
    stopwords = {'的', '了', '是', '我', '有', '和', '就', '不', '人', '都', '一', 
                 '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
                 '没有', '看', '好', '自己', '这', '那', '什么', '怎么', '今天', '明天'}
    
    for review in recent_reviews:
        for answer in review.answers.all():
            if answer.answer_text and answer.field_type in ['text', 'textarea']:
                text = answer.answer_text
                # 简单分割(实际应使用jieba)
                words = [w for w in text if len(w) >= 2 and w not in stopwords]
                for word in words:
                    word_freq[word] = word_freq.get(word, 0) + 1
    
    # 取高频词
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return jsonify({
        "words": [{"text": w[0], "value": w[1]} for w in sorted_words],
        "total_processed": len(recent_reviews),
        "note": "此为简化版本，建议接入jieba进行中文分词"
    }), 200


@stats_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_template_usage():
    """
    获取模板使用统计
    
    GET /api/stats/templates
    
    AI维护注意点: 展示用户各模板的使用频率
    """
    current_user_id = get_jwt_identity()
    
    # 按模板统计复盘数
    template_stats = db.session.query(
        Review.template_id,
        Review.template_name,
        func.count(Review.id).label('count'),
        func.max(Review.review_date).label('last_used')
    ).filter(
        Review.user_id == current_user_id
    ).group_by(Review.template_id, Review.template_name).order_by(
        func.count(Review.id).desc()
    ).all()
    
    total = sum(s[2] for s in template_stats)
    
    return jsonify({
        "templates": [
            {
                "template_id": s[0],
                "template_name": s[1],
                "count": s[2],
                "percentage": round(s[2] / total * 100, 1) if total > 0 else 0,
                "last_used": s[3].isoformat() if s[3] else None
            }
            for s in template_stats
        ],
        "total_reviews": total
    }), 200
