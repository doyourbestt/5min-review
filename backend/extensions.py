"""
5分钟快速复盘 - Flask扩展初始化
==============================
用于避免循环导入问题
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# 初始化扩展（不绑定到app）
db = SQLAlchemy()
jwt = JWTManager()
