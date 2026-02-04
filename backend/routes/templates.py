"""
5分钟快速复盘 - 模板路由
======================
AI维护注意点:
1. 系统模板只有管理员可修改
2. 字段顺序通过order_index维护
3. 模板删除影响关联复盘，需谨慎处理
4. 公开模板可被其他用户使用但不可修改
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from models.template import ReviewTemplate, TemplateField
from models.user import User
from extensions import db

# 创建蓝图
templates_bp = Blueprint('templates', __name__)

# AI维护注意点: 模板字段类型定义
FIELD_TYPES = ['text', 'textarea', 'number', 'select', 
               'multiselect', 'date', 'rating', 'checkbox']


@templates_bp.route('', methods=['GET'])
@jwt_required()
def get_templates():
    """
    获取模板列表
    
    GET /api/templates?include_system=true&type=daily
    
    Query Parameters:
        include_system: 是否包含系统模板 (默认true)
        type: 按类型筛选 (daily/weekly/project/custom)
    
    AI维护注意点: 需确保用户只能看到自己有权限的模板
    """
    current_user_id = get_jwt_identity()
    
    # 查询参数
    include_system = request.args.get('include_system', 'true').lower() == 'true'
    template_type = request.args.get('type')
    
    # 构建查询
    query = ReviewTemplate.query.filter(
        or_(
            ReviewTemplate.user_id == current_user_id,
            ReviewTemplate.is_public == True,
            ReviewTemplate.is_system == True if include_system else False
        )
    )
    
    if template_type:
        query = query.filter_by(template_type=template_type)
    
    # 排序：系统模板在前，然后按创建时间倒序
    templates = query.order_by(
        ReviewTemplate.is_system.desc(),
        ReviewTemplate.created_at.desc()
    ).all()
    
    return jsonify({
        "templates": [t.to_dict(include_fields=False) for t in templates]
    }), 200


@templates_bp.route('/<int:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """
    获取单个模板详情
    
    GET /api/templates/{id}
    
    AI维护注意点: 检查用户是否有权限查看此模板
    """
    current_user_id = get_jwt_identity()
    
    template = ReviewTemplate.query.get_or_404(template_id)
    
    # 权限检查
    if not can_access_template(template, current_user_id):
        return jsonify({"error": "无权访问此模板"}), 403
    
    return jsonify({
        "template": template.to_dict(include_fields=True)
    }), 200


def can_access_template(template, user_id):
    """
    检查用户是否可以访问模板
    
    AI维护注意点: 系统模板、公开模板、自己的模板均可访问
    """
    return (
        template.is_system or 
        template.is_public or 
        template.user_id == user_id
    )


@templates_bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """
    创建新模板
    
    POST /api/templates
    
    Request Body:
        {
            "name": "模板名称",
            "description": "描述",
            "template_type": "daily",
            "is_public": false,
            "fields": [
                {
                    "name": "field1",
                    "label": "字段标签",
                    "field_type": "text",
                    "required": true,
                    "order_index": 0
                }
            ]
        }
    
    AI维护注意点:
    - 字段数量和类型需校验
    - 字段name需唯一
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    # 基本字段校验
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "模板名称为必填项"}), 400
    
    if len(name) > 100:
        return jsonify({"error": "模板名称不能超过100字符"}), 400
    
    # 字段校验
    fields_data = data.get('fields', [])
    if not fields_data:
        return jsonify({"error": "模板至少需要一个字段"}), 400
    
    if len(fields_data) > 10:
        return jsonify({"error": "模板字段不能超过10个"}), 400
    
    # 校验字段数据
    field_names = set()
    for idx, field in enumerate(fields_data):
        # 必填项检查
        if not field.get('name') or not field.get('label') or not field.get('field_type'):
            return jsonify({"error": f"第{idx+1}个字段缺少必填项"}), 400
        
        # 字段名唯一性
        if field['name'] in field_names:
            return jsonify({"error": f"字段名'{field['name']}'重复"}), 400
        field_names.add(field['name'])
        
        # 字段类型有效性
        if field['field_type'] not in FIELD_TYPES:
            return jsonify({"error": f"不支持的字段类型: {field['field_type']}"}), 400
    
    try:
        # 创建模板
        template = ReviewTemplate(
            name=name,
            description=data.get('description', ''),
            template_type=data.get('template_type', 'custom'),
            is_public=data.get('is_public', False),
            user_id=current_user_id,
            is_system=False  # 用户创建的不能是系统模板
        )
        
        db.session.add(template)
        db.session.flush()  # 获取template.id
        
        # 创建字段
        for idx, field_data in enumerate(fields_data):
            field = TemplateField(
                template_id=template.id,
                name=field_data['name'],
                label=field_data['label'],
                field_type=field_data['field_type'],
                required=field_data.get('required', False),
                order_index=field_data.get('order_index', idx),
                placeholder=field_data.get('placeholder', ''),
                default_value=field_data.get('default_value', ''),
                config=field_data.get('config') if isinstance(field_data.get('config'), str) 
                       else str(field_data.get('config', {}))
            )
            db.session.add(field)
        
        db.session.commit()
        
        return jsonify({
            "message": "模板创建成功",
            "template": template.to_dict(include_fields=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "创建失败，请稍后重试"}), 500


@templates_bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """
    更新模板
    
    PUT /api/templates/{id}
    
    AI维护注意点:
    - 系统模板需管理员权限
    - 字段更新采用全量替换策略
    """
    current_user_id = get_jwt_identity()
    template = ReviewTemplate.query.get_or_404(template_id)
    
    # 权限检查
    if not template.can_edit(current_user_id):
        return jsonify({"error": "无权修改此模板"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    try:
        # 更新基本信息
        if 'name' in data:
            template.name = data['name'].strip()
        if 'description' in data:
            template.description = data.get('description', '')
        if 'is_public' in data:
            template.is_public = data['is_public']
        
        # 更新字段(全量替换)
        if 'fields' in data:
            # 删除旧字段
            TemplateField.query.filter_by(template_id=template_id).delete()
            
            # 创建新字段
            for idx, field_data in enumerate(data['fields']):
                field = TemplateField(
                    template_id=template.id,
                    name=field_data['name'],
                    label=field_data['label'],
                    field_type=field_data['field_type'],
                    required=field_data.get('required', False),
                    order_index=field_data.get('order_index', idx),
                    placeholder=field_data.get('placeholder', ''),
                    default_value=field_data.get('default_value', ''),
                    config=str(field_data.get('config', {}))
                )
                db.session.add(field)
        
        db.session.commit()
        
        return jsonify({
            "message": "模板更新成功",
            "template": template.to_dict(include_fields=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "更新失败"}), 500


@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """
    删除模板
    
    DELETE /api/templates/{id}
    
    AI维护注意点:
    - 系统模板不可删除
    - 有复盘记录关联时需谨慎处理
    """
    current_user_id = get_jwt_identity()
    template = ReviewTemplate.query.get_or_404(template_id)
    
    # 系统模板不可删除
    if template.is_system:
        return jsonify({"error": "系统预设模板不可删除"}), 403
    
    # 权限检查
    if template.user_id != current_user_id:
        return jsonify({"error": "无权删除此模板"}), 403
    
    # AI维护注意点: 检查是否有关联复盘记录
    review_count = template.reviews.count()
    if review_count > 0:
        # 有复盘记录，软删除或标记
        return jsonify({
            "error": f"此模板已被使用{review_count}次，不可删除",
            "review_count": review_count
        }), 400
    
    try:
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({"message": "模板删除成功"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "删除失败"}), 500


@templates_bp.route('/system', methods=['GET'])
def get_system_templates():
    """
    获取系统预设模板(无需登录)
    
    GET /api/templates/system
    
    AI维护注意点: 用于展示页面，返回简化信息
    """
    templates = ReviewTemplate.query.filter_by(is_system=True).all()
    
    return jsonify({
        "templates": [t.to_dict(include_fields=True) for t in templates]
    }), 200
