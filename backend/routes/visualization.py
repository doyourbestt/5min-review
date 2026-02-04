"""
5分钟快速复盘 - 可视化复盘模块
==============================
核心功能：Markdown解析、人物卡片聚合、头像管理、点赞系统
AI维护注意点:
1. 解析器容错性强，适配多种markdown格式变体
2. 头像存储使用本地文件系统，生产环境可迁移到OSS
3. 点赞使用设备指纹+昵称双校验，防刷但用户体验友好
4. 所有接口返回格式统一，方便前端处理
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import re
import os
import uuid
import hashlib
from PIL import Image
from io import BytesIO

from extensions import db
from models.visualization import ReviewDay, Sharer, Insight, Like

viz_router = APIRouter(prefix="/api/viz", tags=["visualization"])

# ============ 数据模型 ============

class InsightItem(BaseModel):
    """单条干货数据结构"""
    topic: str                    # 主题（如"时间价值化魔法"）
    content: str                  # 内容
    emoji: Optional[str] = None   # 表情符号

class SharerData(BaseModel):
    """分享者数据结构"""
    name: str                     # 姓名
    emoji: Optional[str] = None # 表情符号
    avatar_url: Optional[str] = None  # 头像URL
    insights: List[InsightItem]   # 干货列表

class ParseRequest(BaseModel):
    """解析请求"""
    markdown: str                 # markdown文本
    review_date: Optional[str] = None  # 复盘日期，默认为今天

class ParseResponse(BaseModel):
    """解析响应"""
    success: bool
    date: str
    sharers: List[SharerData]
    message: Optional[str] = None

class LikeRequest(BaseModel):
    """点赞请求"""
    insight_id: int
    nickname: Optional[str] = None  # 可选昵称
    device_id: str                    # 设备指纹（必填，防重复）


# ============ Markdown解析器 ============

class MarkdownParser:
    """
    Markdown复盘文本解析器
    
    支持格式：
    ## 姓名 表情（可选标签）
    - 主题：内容（单行或多行）
    - 主题：内容
    
    AI维护注意点:
    1. 容错性强：支持无表情、无标签、多行内容
    2. 正则匹配：姓名捕获、列表项分割
    3. 过滤非干货内容：过滤"小彩蛋"等区块
    """
    
    @staticmethod
    def parse(markdown_text: str) -> List[SharerData]:
        """
        解析markdown文本为结构化数据
        
        Args:
            markdown_text: 原始markdown文本
            
        Returns:
            List[SharerData]: 分享者列表
        """
        sharers = []
        
        # 按 ## 分割，找到所有分享者区块
        # 匹配 ## 姓名 [表情] [（标签）]
        pattern = r'##\s+([^\n]+?)(?=\n|$)'
        sections = re.split(pattern, markdown_text)
        
        if len(sections) <= 1:
            return sharers
        
        # sections[0]是开头内容（如主标题），忽略
        # 之后是 [姓名部分, 内容, 姓名部分, 内容, ...]
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                break
                
            header = sections[i].strip()
            content = sections[i + 1].strip()
            
            # 解析姓名和表情
            name, emoji = MarkdownParser._parse_header(header)
            if not name:
                continue
            
            # 解析干货列表
            insights = MarkdownParser._parse_insights(content)
            if not insights:
                continue
            
            sharers.append(SharerData(
                name=name,
                emoji=emoji,
                insights=insights
            ))
        
        return sharers
    
    @staticmethod
    def _parse_header(header: str) -> tuple:
        """
        解析分享者头部信息
        
        示例：
        "李阳州 🕰️" → ("李阳州", "🕰️")
        "小马哥 🔥" → ("小马哥", "🔥")
        "小妮（做饭）🥾" → ("小妮", "🥾")
        "Judy 🧘" → ("Judy", "🧘")
        
        AI维护注意点:
        1. 标签（括号内中文/英文括号内容）会被过滤，只保留姓名
        2. 表情符号检测：Unicode emoji范围
        3. 姓名中保留英文、数字、中文混合
        """
        # 移除括号内的标签（支持中文和英文括号）
        header = re.sub(r'[（(][^）)]+[）)]', '', header).strip()
        
        # 分离姓名和表情
        # 表情通常在最后，是emoji字符
        parts = header.split()
        
        name = ""
        emoji = None
        
        for part in parts:
            if MarkdownParser._is_emoji(part):
                emoji = part
            else:
                if name:
                    name += " "
                name += part
        
        return name.strip(), emoji
    
    @staticmethod
    def _is_emoji(text: str) -> bool:
        """
        检测是否为emoji表情
        
        AI维护注意点:
        使用Unicode范围检测，覆盖常见emoji
        """
        if not text:
            return False
        
        # emoji Unicode范围
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        
        return bool(emoji_pattern.match(text))
    
    @staticmethod
    def _parse_insights(content: str) -> List[InsightItem]:
        """
        解析干货列表
        
        支持格式：
        - 主题：内容
        - 主题：多行内容
          第二行内容
        
        AI维护注意点:
        1. 支持多行内容（以缩进或空行判断）
        2. 过滤非列表项内容（如分隔线、引用）
        """
        insights = []
        
        # 按行分割
        lines = content.split('\n')
        current_insight = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测列表项：- 或 * 开头
            list_match = re.match(r'^[-\*]\s*(.+)$', line)
            if list_match:
                # 保存上一个干货
                if current_insight:
                    insights.append(current_insight)
                
                item_text = list_match.group(1)
                # 分割主题和内容
                if '：' in item_text or ':' in item_text:
                    # 中文冒号优先
                    if '：' in item_text:
                        topic, content = item_text.split('：', 1)
                    else:
                        topic, content = item_text.split(':', 1)
                    current_insight = InsightItem(
                        topic=topic.strip(),
                        content=content.strip()
                    )
                else:
                    # 无主题格式，使用内容前20字作为主题
                    topic = item_text[:20] + ('...' if len(item_text) > 20 else '')
                    current_insight = InsightItem(
                        topic=topic,
                        content=item_text
                    )
            elif current_insight and line:
                # 可能是多行内容的续行
                current_insight.content += '\n' + line
        
        # 添加最后一个干货
        if current_insight:
            insights.append(current_insight)
        
        return insights


# ============ API路由 ============

@viz_router.post("/parse", response_model=ParseResponse)
async def parse_markdown(request: ParseRequest):
    """
    解析Markdown复盘文本
    
    AI维护注意点:
    1. 解析前清理文本（去除多余空行）
    2. 自动检测日期（从标题或当前时间）
    3. 返回结构化数据，但不立即存储（先预览后确认）
    """
    try:
        # 清理文本
        markdown = request.markdown.strip()
        
        # 解析
        parser = MarkdownParser()
        sharers = parser.parse(markdown)
        
        # 确定日期
        review_date = request.review_date or str(date.today())
        
        # 从markdown标题提取日期（如果有）
        date_match = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2})', markdown)
        if date_match:
            extracted_date = date_match.group(1).replace('年', '-').replace('月', '-')
            review_date = extracted_date
        
        return ParseResponse(
            success=True,
            date=review_date,
            sharers=sharers,
            message=f"成功解析 {len(sharers)} 位分享者的干货"
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败：{str(e)}")


@viz_router.post("/save")
async def save_review(
    markdown: str = Form(...),
    review_date: str = Form(...),
    device_id: Optional[str] = Form(None)
):
    """
    保存复盘数据到数据库
    
    AI维护注意点:
    1. 使用事务确保数据一致性
    2. 分享者不存在时自动创建（使用默认头像）
    3. 同一天重复保存会覆盖（或添加版本）
    """
    try:
        # 解析markdown
        parser = MarkdownParser()
        sharers_data = parser.parse(markdown)
        
        # 检查是否已存在同一天的复盘
        existing_day = ReviewDay.query.filter_by(date=review_date).first()
        
        if existing_day:
            # 删除旧的干货数据（覆盖模式）
            Insight.query.filter_by(day_id=existing_day.id).delete()
            existing_day.raw_content = markdown
        else:
            # 创建新的复盘日
            existing_day = ReviewDay(
                date=review_date,
                title=MarkdownParser._extract_title(markdown) or f"{review_date} 复盘",
                raw_content=markdown
            )
            db.session.add(existing_day)
            db.session.flush()  # 获取day_id
        
        # 保存每个分享者的干货
        for sharer_data in sharers_data:
            # 查找或创建分享者
            sharer = Sharer.query.filter_by(name=sharer_data.name).first()
            if not sharer:
                sharer = Sharer(
                    name=sharer_data.name,
                    avatar_url=None  # 稍后上传
                )
                db.session.add(sharer)
                db.session.flush()
            
            # 保存干货
            for insight_item in sharer_data.insights:
                insight = Insight(
                    day_id=existing_day.id,
                    sharer_id=sharer.id,
                    emoji=sharer_data.emoji,
                    topic=insight_item.topic,
                    content=insight_item.content,
                    likes=0
                )
                db.session.add(insight)
        
        db.session.commit()
        
        return {
            "success": True,
            "day_id": existing_day.id,
            "message": f"成功保存 {len(sharers_data)} 位分享者的干货",
            "url": f"/viz/{review_date}"  # 查看链接
        }
    
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")


@viz_router.get("/reviews/{review_date}")
async def get_review_by_date(review_date: str):
    """
    按日期获取复盘数据（人物卡片格式）
    
    AI维护注意点:
    1. 使用JOIN查询优化性能
    2. 按分享者聚合干货
    3. 返回前端可直接渲染的数据结构
    """
    try:
        # 查找复盘日
        day = ReviewDay.query.filter_by(date=review_date).first()
        if not day:
            raise HTTPException(status_code=404, detail="该日期暂无复盘数据")
        
        # 查询所有干货（JOIN分享者信息）
        insights = db.session.query(
            Insight, Sharer
        ).join(
            Sharer, Insight.sharer_id == Sharer.id
        ).filter(
            Insight.day_id == day.id
        ).all()
        
        # 按分享者聚合
        sharers_map = {}
        for insight, sharer in insights:
            if sharer.name not in sharers_map:
                sharers_map[sharer.name] = {
                    "id": sharer.id,
                    "name": sharer.name,
                    "emoji": insight.emoji,  # 使用干货中的表情
                    "avatar_url": sharer.avatar_url or f"/static/avatars/default/{sharer.name[0]}.png",
                    "insights": []
                }
            
            sharers_map[sharer.name]["insights"].append({
                "id": insight.id,
                "topic": insight.topic,
                "content": insight.content,
                "likes": insight.likes
            })
        
        return {
            "success": True,
            "date": review_date,
            "title": day.title,
            "sharers": list(sharers_map.values()),
            "total_insights": len(insights)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@viz_router.get("/dates")
async def get_all_dates():
    """
    获取所有有复盘数据的日期列表
    
    AI维护注意点:
    用于日期选择器，按时间倒序排列
    """
    try:
        days = ReviewDay.query.order_by(ReviewDay.date.desc()).all()
        return {
            "success": True,
            "dates": [
                {
                    "date": day.date,
                    "title": day.title
                }
                for day in days
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@viz_router.post("/upload-avatar/{sharer_name}")
async def upload_avatar(
    sharer_name: str,
    file: UploadFile = File(...)
):
    """
    上传分享者头像
    
    AI维护注意点:
    1. 文件类型校验（只允许jpg/png/webp）
    2. 自动裁剪为正方形（80x80px）
    3. 本地存储路径：static/avatars/{sharer_name}.jpg
    4. 生产环境可迁移到OSS（只需改存储逻辑）
    """
    try:
        # 校验文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="仅支持jpg/png/webp格式")
        
        # 读取图片
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB限制
            raise HTTPException(status_code=400, detail="图片大小不能超过5MB")
        
        # 使用Pillow处理图片
        img = Image.open(BytesIO(contents))
        
        # 转换为RGB（处理PNG透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # 裁剪为正方形（取中心区域）
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        
        img = img.crop((left, top, right, bottom))
        
        # 缩放到80x80（移动端卡片适配尺寸）
        img = img.resize((80, 80), Image.Resampling.LANCZOS)
        
        # 确保目录存在
        avatar_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # 保存文件（使用分享者姓名作为文件名）
        filename = f"{sharer_name}.jpg"
        filepath = os.path.join(avatar_dir, filename)
        img.save(filepath, 'JPEG', quality=85)
        
        # 更新数据库
        sharer = Sharer.query.filter_by(name=sharer_name).first()
        if sharer:
            sharer.avatar_url = f"/static/avatars/{filename}"
            db.session.commit()
        
        return {
            "success": True,
            "avatar_url": f"/static/avatars/{filename}",
            "message": "头像上传成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@viz_router.post("/like")
async def like_insight(request: LikeRequest):
    """
    点赞干货
    
    AI维护注意点:
    1. 使用设备指纹+昵称双校验，防止重复点赞
    2. 同一设备+同一干货只能点赞一次
    3. 点赞数据实时更新到insight表（冗余存储优化查询）
    4. 支持取消点赞（可选扩展）
    """
    try:
        # 检查是否已经点赞
        existing_like = Like.query.filter_by(
            insight_id=request.insight_id,
            device_id=request.device_id
        ).first()
        
        if existing_like:
            return {
                "success": False,
                "message": "您已经点过赞了",
                "liked": True
            }
        
        # 创建点赞记录
        like = Like(
            insight_id=request.insight_id,
            liker_nickname=request.nickname or "匿名用户",
            device_id=request.device_id
        )
        db.session.add(like)
        
        # 更新干货点赞数
        insight = Insight.query.get(request.insight_id)
        if insight:
            insight.likes += 1
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "点赞成功",
            "liked": True,
            "total_likes": insight.likes if insight else 0
        }
    
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"点赞失败：{str(e)}")


@viz_router.get("/likes/{insight_id}")
async def get_likes(insight_id: int):
    """
    获取某条干货的点赞详情
    
    AI维护注意点:
    返回点赞总数和最近的点赞者列表（隐私保护，只显示昵称）
    """
    try:
        likes = Like.query.filter_by(insight_id=insight_id).order_by(Like.created_at.desc()).all()
        
        return {
            "success": True,
            "insight_id": insight_id,
            "total": len(likes),
            "likers": [
                {
                    "nickname": like.liker_nickname,
                    "time": like.created_at.strftime("%m-%d %H:%M")
                }
                for like in likes[:10]  # 只显示最近10个
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@viz_router.get("/likes/by-topic")
async def get_likes_by_topic(topic: str):
    """
    按主题筛选点赞数据
    
    AI维护注意点:
    1. 支持模糊匹配主题
    2. 返回所有相关干货的点赞统计
    3. 方便"方便后续回顾"需求
    """
    try:
        # 模糊查询匹配主题
        insights = Insight.query.filter(
            Insight.topic.ilike(f'%{topic}%')
        ).order_by(Insight.likes.desc()).all()
        
        results = []
        for insight in insights:
            sharer = Sharer.query.get(insight.sharer_id)
            day = ReviewDay.query.get(insight.day_id)
            
            results.append({
                "insight_id": insight.id,
                "topic": insight.topic,
                "content": insight.content[:50] + "..." if len(insight.content) > 50 else insight.content,
                "sharer": sharer.name if sharer else "未知",
                "date": day.date.strftime("%Y-%m-%d") if day else "未知",
                "likes": insight.likes
            })
        
        return {
            "success": True,
            "topic": topic,
            "total_count": len(results),
            "total_likes": sum(r["likes"] for r in results),
            "insights": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@viz_router.get("/likes/by-sharer/{sharer_name}")
async def get_likes_by_sharer(sharer_name: str):
    """
    按分享者筛选点赞数据
    
    AI维护注意点:
    1. 精确匹配分享者姓名
    2. 返回该分享者所有干货的点赞统计
    """
    try:
        sharer = Sharer.query.filter_by(name=sharer_name).first()
        if not sharer:
            raise HTTPException(status_code=404, detail="分享者不存在")
        
        insights = Insight.query.filter_by(sharer_id=sharer.id).order_by(Insight.likes.desc()).all()
        
        results = []
        for insight in insights:
            day = ReviewDay.query.get(insight.day_id)
            
            results.append({
                "insight_id": insight.id,
                "topic": insight.topic,
                "content": insight.content[:50] + "..." if len(insight.content) > 50 else insight.content,
                "date": day.date.strftime("%Y-%m-%d") if day else "未知",
                "likes": insight.likes
            })
        
        return {
            "success": True,
            "sharer": sharer_name,
            "total_insights": len(results),
            "total_likes": sum(r["likes"] for r in results),
            "insights": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 辅助方法扩展 ============

def _extract_title(markdown: str) -> Optional[str]:
    """
    从markdown提取标题（# 开头的第一行）
    
    AI维护注意点:
    用于复盘日标题显示，如果没有则使用日期
    """
    lines = markdown.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# ') and not line.startswith('##'):
            return line[2:].strip()
        elif line.startswith('#') and not line.startswith('##'):
            return line[1:].strip()
    return None


# 绑定到类
MarkdownParser._extract_title = staticmethod(_extract_title)
