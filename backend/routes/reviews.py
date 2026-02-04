"""
5分钟快速复盘 - 复盘路由
======================
AI维护注意点:
1. 复盘记录创建后不可修改，保持历史完整性
2. 同一日期的复盘可多次提交，取最新记录
3. 答案数据需校验字段类型有效性
4. 复盘统计需考虑性能优化
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from sqlalchemy import func, and_

from models.review import Review, ReviewAnswer
from models.template import ReviewTemplate
from models.user import User
from extensions import db

# 创建蓝图
reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('', methods=['GET'])
@jwt_required()
def get_reviews():
    """
    获取复盘列表
    
    GET /api/reviews?start_date=2024-01-01&end_date=2024-01-31&type=daily&page=1
    
    Query Parameters:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        type: 复盘类型筛选
        page: 页码(默认1)
        per_page: 每页数量(默认20)
    
    AI维护注意点: 日期格式校验和默认值处理
    """
    current_user_id = get_jwt_identity()
    
    # 查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    review_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 限制每页最大数量
    per_page = min(per_page, 50)
    
    # 构建查询
    query = Review.query.filter_by(user_id=current_user_id)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Review.review_date >= start)
        except ValueError:
            return jsonify({"error": "开始日期格式错误，应为YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Review.review_date <= end)
        except ValueError:
            return jsonify({"error": "结束日期格式错误，应为YYYY-MM-DD"}), 400
    
    if review_type:
        query = query.filter_by(review_type=review_type)
    
    # 分页查询
    pagination = query.order_by(Review.review_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "reviews": [r.to_dict(include_answers=False) for r in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
        "per_page": per_page
    }), 200


@reviews_bp.route('/<int:review_id>', methods=['GET'])
@jwt_required()
def get_review(review_id):
    """
    获取单个复盘详情
    
    GET /api/reviews/{id}
    
    AI维护注意点: 只能查看自己的复盘
    """
    current_user_id = get_jwt_identity()
    
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user_id:
        return jsonify({"error": "无权访问此复盘"}), 403
    
    return jsonify({
        "review": review.to_dict(include_answers=True)
    }), 200


@reviews_bp.route('', methods=['POST'])
@jwt_required()
def create_review():
    """
    创建复盘记录
    
    POST /api/reviews
    
    Request Body:
        {
            "template_id": 1,
            "review_date": "2024-01-15",
            "title": "今日复盘",
            "answers": {
                "field1": "回答内容",
                "field2": 5
            },
            "duration_minutes": 5
        }
    
    AI维护注意点:
    - 同一日期同类型复盘可覆盖
    - 答案需校验字段类型
    - 自动计算字数统计
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    template_id = data.get('template_id')
    if not template_id:
        return jsonify({"error": "template_id为必填项"}), 400
    
    # 获取模板
    template = ReviewTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "模板不存在"}), 404
    
    # 校验模板使用权限
    if not template.is_public and template.user_id != current_user_id and not template.is_system:
        return jsonify({"error": "无权使用此模板"}), 403
    
    # 解析复盘日期
    review_date_str = data.get('review_date')
    if review_date_str:
        try:
            review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "日期格式错误，应为YYYY-MM-DD"}), 400
    else:
        review_date = date.today()
    
    # 检查是否已有当日复盘(同类型)
    # AI维护注意点: 可配置为允许每日多条或仅一条
    existing_review = Review.query.filter_by(
        user_id=current_user_id,
        review_date=review_date,
        review_type=template.template_type
    ).first()
    
    try:
        if existing_review:
            # 删除旧复盘及其答案
            ReviewAnswer.query.filter_by(review_id=existing_review.id).delete()
            db.session.delete(existing_review)
            db.session.flush()
        
        # 创建新复盘
        review = Review(
            user_id=current_user_id,
            template_id=template_id,
            template_name=template.name,
            review_type=template.template_type,
            title=data.get('title', f"{review_date}复盘"),
            review_date=review_date,
            duration_minutes=data.get('duration_minutes', 5),
            is_completed=True
        )
        
        db.session.add(review)
        db.session.flush()  # 获取review.id
        
        # 处理答案
        answers_data = data.get('answers', {})
        fields = {f.name: f for f in template.fields.all()}
        
        for field_name, field in fields.items():
            answer_value = answers_data.get(field_name)
            
            answer = ReviewAnswer(
                review_id=review.id,
                field_name=field.name,
                field_label=field.label,
                field_type=field.field_type
            )
            answer.set_answer(answer_value, field.field_type)
            
            db.session.add(answer)
        
        # 计算字数
        db.session.flush()  # 确保answers已写入
        review.calculate_word_count()
        
        # 增加模板使用计数
        template.increment_use_count()
        
        # 更新用户连续打卡统计(可扩展)
        # AI维护注意点: 可在此触发成就系统
        
        db.session.commit()
        
        return jsonify({
            "message": "复盘保存成功" if not existing_review else "复盘更新成功",
            "review": review.to_dict(include_answers=True)
        }), 201 if not existing_review else 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "保存失败，请稍后重试"}), 500


@reviews_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_review():
    """
    获取今日复盘
    
    GET /api/reviews/today
    
    AI维护注意点: 用于首页快速查看今日是否已复盘
    """
    current_user_id = get_jwt_identity()
    today = date.today()
    
    review = Review.get_daily_review(current_user_id, today)
    
    if not review:
        return jsonify({
            "has_review": False,
            "message": "今日尚未复盘"
        }), 200
    
    return jsonify({
        "has_review": True,
        "review": review.to_dict(include_answers=True)
    }), 200


@reviews_bp.route('/checkin', methods=['GET'])
@jwt_required()
def get_checkin_status():
    """
    获取打卡状态(最近7天)
    
    GET /api/reviews/checkin
    
    AI维护注意点: 用于日历热力图展示
    """
    current_user_id = get_jwt_identity()
    
    # 获取最近30天的复盘日期
    from datetime import timedelta
    
    end_date = date.today()
    start_date = end_date - timedelta(days=29)
    
    reviews = Review.query.filter(
        Review.user_id == current_user_id,
        Review.review_date >= start_date,
        Review.review_date <= end_date
    ).all()
    
    # 构建日期映射
    checkin_dates = {}
    for review in reviews:
        date_str = review.review_date.strftime('%Y-%m-%d')
        if date_str not in checkin_dates:
            checkin_dates[date_str] = {
                "has_review": True,
                "count": 0,
                "word_count": 0
            }
        checkin_dates[date_str]["count"] += 1
        checkin_dates[date_str]["word_count"] += review.word_count
    
    # 计算连续打卡天数
    streak = 0
    check_date = end_date
    while True:
        date_str = check_date.strftime('%Y-%m-%d')
        if date_str in checkin_dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return jsonify({
        "checkin_dates": checkin_dates,
        "current_streak": streak,
        "total_days": len(checkin_dates),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat()
    }), 200


@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """
    删除复盘记录
    
    DELETE /api/reviews/{id}
    
    AI维护注意点: 复盘记录删除不可逆，建议添加确认对话框
    """
    current_user_id = get_jwt_identity()
    
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user_id:
        return jsonify({"error": "无权删除此复盘"}), 403
    
    try:
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({"message": "复盘已删除"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "删除失败"}), 500
