"""
5分钟快速复盘 - 复盘标记API
===========================
支持markdown解析、卡片管理、公开分享
AI维护注意点:
1. 解析逻辑在parser中实现
2. 公开分享通过share_token验证
"""

import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_jwt_cookies, create_access_token
from datetime import datetime
import uuid

from extensions import db
from models.mark import MarkCard

marks_bp = Blueprint('marks', __name__)


def parse_markdown_to_cards(markdown_text):
    """
    解析markdown文本为卡片列表
    
    格式:
    # 可选标题（会被忽略）
    ## 姓名 [emoji]
    - 标签1：内容1
    - 标签2：内容2
    
    ## 姓名2 [emoji]
    - 内容...
    """
    cards = []
    lines = markdown_text.strip().split('\n')
    
    current_card = None
    current_content = []
    in_header_section = True  # 是否在标题区域（前几行的非##内容）
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # 匹配 ## 姓名 [emoji] 格式
        header_match = re.match(r'^##\s+(.+?)(?:\s+([^\s]+))?\s*$', line)
        if header_match:
            # 跳过小彩蛋等非卡片内容
            if '小彩蛋' in header_match.group(1):
                continue
            
            # 保存之前的卡片
            if current_card and current_content:
                current_card['content'] = '\n'.join(current_content)
                cards.append(current_card)
            
            name_part = header_match.group(1).strip()
            emoji = header_match.group(2) or ''
            
            current_card = {
                'name': name_part,
                'emoji': emoji,
                'content': ''
            }
            current_content = []
            in_header_section = False
        
        elif not in_header_section and current_card:
            # 收集内容行
            if line.startswith('- '):
                content = line[2:].strip()
                if content:
                    current_content.append(content)
            elif line.startswith('• ') or line.startswith('* '):
                content = line[2:].strip()
                if content:
                    current_content.append(content)
            elif current_content:
                # 如果不是列表项但有已有内容，追加到上一行
                current_content[-1] += ' ' + line
    
    # 保存最后一张卡片
    if current_card and current_content:
        current_card['content'] = '\n'.join(current_content)
        cards.append(current_card)
    
    return cards


def format_card_content(content):
    """将卡片内容格式化为带标签的markdown格式"""
    lines = content.split('\n')
    formatted = []
    for line in lines:
        line = line.strip()
        if line:
            # 如果没有冒号，添加通用标签
            if '：' not in line and ':' not in line:
                line = f'要点：{line}'
            formatted.append(f'- {line}')
    return '\n'.join(formatted)


@marks_bp.route('/parse', methods=['POST'])
@jwt_required()
def parse_markdown():
    """
    解析markdown文本（不保存）
    
    POST /api/marks/parse
    Body: { markdown: "..." }
    
    Returns: { cards: [{name, emoji, content}, ...] }
    """
    data = request.get_json()
    markdown = data.get('markdown', '').strip()
    
    if not markdown:
        return jsonify({'error': 'markdown内容不能为空'}), 400
    
    try:
        cards = parse_markdown_to_cards(markdown)
        return jsonify({
            'cards': cards,
            'count': len(cards)
        })
    except Exception as e:
        return jsonify({'error': f'解析失败: {str(e)}'}), 400


@marks_bp.route('', methods=['POST'])
@jwt_required()
def save_cards():
    """
    保存解析后的卡片
    
    POST /api/marks
    Body: {
        date: "2024-01-20",
        cards: [{name, emoji, content}, ...]
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    data = request.get_json()
    logger.info(f"Received data: {data}")
    
    date_str = data.get('date')
    cards_data = data.get('cards', [])
    
    logger.info(f"date_str: {date_str}, cards_data: {cards_data}")
    
    if not date_str:
        return jsonify({'error': '日期不能为空'}), 400
    
    if not cards_data:
        return jsonify({'error': '没有可保存的卡片数据'}), 400
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误，应为YYYY-MM-DD'}), 400
    
    user_id = get_jwt_identity()
    logger.info(f"user_id: {user_id}")
    
    saved_cards = []
    
    for card_data in cards_data:
        logger.info(f"Processing card: {card_data}")
        if not card_data.get('name') or not card_data.get('content'):
            continue
        
        card = MarkCard(
            id=str(uuid.uuid4()),
            user_id=user_id,
            date=date_obj,
            name=card_data['name'],
            emoji=card_data.get('emoji', ''),
            content=format_card_content(card_data['content']),
            share_token=str(uuid.uuid4()),
            is_public=True
        )
        db.session.add(card)
        saved_cards.append(card.to_dict())
    
    try:
        db.session.commit()
        logger.info(f"Successfully saved {len(saved_cards)} cards")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    
    return jsonify({
        'message': f'成功保存 {len(saved_cards)} 张卡片',
        'cards': saved_cards
    })


@marks_bp.route('', methods=['GET'])
@jwt_required()
def get_my_cards():
    """
    获取当前用户的所有卡片
    
    GET /api/marks
    Query: date (可选，按日期筛选)
    """
    user_id = get_jwt_identity()
    date_filter = request.args.get('date')
    
    query = MarkCard.query.filter_by(user_id=user_id)
    
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(date=date_obj)
        except ValueError:
            pass
    
    cards = query.order_by(MarkCard.date.desc(), MarkCard.created_at.desc()).all()
    
    return jsonify({
        'cards': [card.to_dict() for card in cards],
        'count': len(cards)
    })


@marks_bp.route('/<card_id>', methods=['PUT'])
@jwt_required()
def update_card(card_id):
    """
    更新卡片
    
    PUT /api/marks/<card_id>
    Body: { date, name, emoji, content }
    """
    user_id = get_jwt_identity()
    
    card = MarkCard.query.filter_by(id=card_id, user_id=user_id).first()
    if not card:
        return jsonify({'error': '卡片不存在'}), 404
    
    data = request.get_json()
    
    if 'date' in data:
        try:
            card.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
    
    if 'name' in data:
        card.name = data['name']
    
    if 'emoji' in data:
        card.emoji = data['emoji']
    
    if 'content' in data:
        card.content = format_card_content(data['content'])
    
    card.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': '更新成功',
        'card': card.to_dict()
    })


@marks_bp.route('/<card_id>', methods=['DELETE'])
@jwt_required()
def delete_card(card_id):
    """
    删除卡片
    
    DELETE /api/marks/<card_id>
    """
    user_id = get_jwt_identity()
    
    card = MarkCard.query.filter_by(id=card_id, user_id=user_id).first()
    if not card:
        return jsonify({'error': '卡片不存在'}), 404
    
    db.session.delete(card)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})


@marks_bp.route('/share/<share_token>', methods=['GET'])
def get_public_card(share_token):
    """
    通过分享链接获取卡片（公开访问）
    
    GET /api/marks/share/<share_token>
    """
    card = MarkCard.query.filter_by(share_token=share_token, is_public=True).first()
    
    if not card:
        return jsonify({'error': '卡片不存在或已删除'}), 404
    
    return jsonify({'card': card.to_dict()})
