"""
5分钟快速复盘 - 认证路由
======================
AI维护注意点:
1. 密码强度校验规则应前后端一致
2. JWT Token刷新机制需在前端实现
3. 登录失败次数限制防止暴力破解
4. 注册邮箱验证功能待完善
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
import re

from models.user import User
from extensions import db

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# AI维护注意点: 注册时的密码强度要求
PASSWORD_MIN_LENGTH = 6
PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]')


def validate_password_strength(password):
    """
    验证密码强度
    
    AI维护注意点: 修改规则时需同步更新前端校验
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"密码长度至少{PASSWORD_MIN_LENGTH}位"
    
    # 要求包含字母和数字
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False, "密码必须包含字母和数字"
    
    return True, "密码强度符合要求"


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    
    POST /api/auth/register
    
    Request Body:
        {
            "username": "用户名",
            "email": "邮箱",
            "password": "密码"
        }
    
    AI维护注意点: 
    - 用户名和邮箱需唯一
    - 密码加密存储
    - 建议添加邮箱验证步骤
    """
    data = request.get_json()
    
    # 参数校验
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    # 必填字段检查
    if not username or not email or not password:
        return jsonify({"error": "用户名、邮箱和密码为必填项"}), 400
    
    # 用户名格式校验
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$', username):
        return jsonify({"error": "用户名2-20位，支持中英文、数字和下划线"}), 400
    
    # 邮箱格式校验
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"error": "邮箱格式不正确"}), 400
    
    # 密码强度校验
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        return jsonify({"error": msg}), 400
    
    # 检查用户名是否已存在
    if User.find_by_username(username):
        return jsonify({"error": "用户名已被使用"}), 409
    
    # 检查邮箱是否已存在
    if User.find_by_email(email):
        return jsonify({"error": "邮箱已被注册"}), 409
    
    # 创建新用户
    try:
        new_user = User(
            username=username,
            email=email,
            is_active=True
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # 生成Token
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)
        
        return jsonify({
            "message": "注册成功",
            "user": new_user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # AI维护注意点: 生产环境不应返回详细错误信息
        return jsonify({"error": "注册失败，请稍后重试"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    
    POST /api/auth/login
    
    Request Body:
        {
            "username": "用户名或邮箱",
            "password": "密码"
        }
    
    AI维护注意点:
    - 支持用户名或邮箱登录
    - 更新最后登录时间
    - 可添加登录失败限制
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    login_name = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not login_name:
        return jsonify({"error": "请输入群昵称"}), 400
    
    # 查找用户(支持用户名或邮箱)
    user = User.find_by_username(login_name) or User.find_by_email(login_name)
    
    # 简化登录：如果没有该用户，自动创建；如果有用户但无密码，也允许登录
    if not user:
        # 自动注册新用户（使用默认密码）
        user = User(
            username=login_name,
            email=f"{login_name}@temp.local"
        )
        user.set_password('123456')  # 设置默认密码
        db.session.add(user)
        db.session.commit()
    elif password and not user.check_password(password):
        # 如果有提供密码但验证失败
        return jsonify({"error": "密码错误"}), 401
    # 如果没有提供密码，直接允许登录（简化版）
    
    # 更新登录时间
    user.update_last_login()
    
    # 生成Token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        "message": "登录成功",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    刷新访问令牌
    
    POST /api/auth/refresh
    
    Headers: Authorization: Bearer <refresh_token>
    
    AI维护注意点:
    - 前端应在access_token即将过期时调用
    - refresh_token也有过期时间
    """
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "access_token": new_token
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取当前用户信息
    
    GET /api/auth/profile
    
    AI维护注意点: 敏感信息如email默认不返回
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    return jsonify({
        "user": user.to_dict(include_sensitive=True)
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    更新用户信息
    
    PUT /api/auth/profile
    
    AI维护注意点:
    - 用户名修改需谨慎，可能影响关联数据
    - 密码修改需要验证旧密码
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    data = request.get_json()
    
    # 更新邮箱
    if 'email' in data:
        new_email = data['email'].strip().lower()
        if new_email != user.email:
            # 检查新邮箱是否已被使用
            existing = User.find_by_email(new_email)
            if existing and existing.id != user.id:
                return jsonify({"error": "邮箱已被其他用户使用"}), 409
            user.email = new_email
    
    # 修改密码
    if 'password' in data and 'old_password' in data:
        if not user.check_password(data['old_password']):
            return jsonify({"error": "原密码错误"}), 400
        
        is_valid, msg = validate_password_strength(data['password'])
        if not is_valid:
            return jsonify({"error": msg}), 400
        
        user.set_password(data['password'])
    
    try:
        db.session.commit()
        return jsonify({
            "message": "资料更新成功",
            "user": user.to_dict(include_sensitive=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "更新失败"}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出
    
    POST /api/auth/logout
    
    AI维护注意点: 如需实现Token黑名单，需在此记录撤销的Token
    """
    # jti = get_jwt()['jti']  # JWT ID
    # 可将jti加入黑名单（如使用Redis）
    
    return jsonify({"message": "登出成功"}), 200
