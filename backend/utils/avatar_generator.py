"""
5分钟快速复盘 - 默认头像生成器
================================
生成姓氏首字母的彩色圆形头像
AI维护注意点:
1. 生成80x80像素的圆形头像
2. 使用预定义配色方案（柔和色彩）
3. 字体回退机制：优先使用系统字体
4. 生成后保存到 static/avatars/default/ 目录
"""

from PIL import Image, ImageDraw, ImageFont
import os
import hashlib

# 柔和配色方案（保证视觉舒适）
COLOR_PALETTE = [
    (255, 154, 162),  # 珊瑚粉
    (255, 183, 178),  # 浅玫瑰
    (255, 218, 193),  # 蜜桃
    (226, 240, 203),  # 薄荷绿
    (181, 234, 215),  # 薄荷蓝
    (199, 206, 234),  # 淡紫
    (236, 192, 222),  # 粉色
    (160, 196, 255),  # 天蓝
    (196, 160, 255),  # 紫罗兰
    (255, 224, 130),  # 鹅黄
    (178, 235, 242),  # 青蓝
    (200, 230, 201),  # 淡绿
]


def get_color_for_name(name: str) -> tuple:
    """
    根据姓名生成固定的背景色
    
    AI维护注意点:
    使用哈希算法确保同一人总是相同颜色
    """
    # 使用姓名哈希选择颜色
    hash_val = int(hashlib.md5(name.encode()).hexdigest(), 16)
    color_index = hash_val % len(COLOR_PALETTE)
    return COLOR_PALETTE[color_index]


def generate_default_avatar(name: str, output_dir: str = None) -> str:
    """
    生成姓氏首字母头像
    
    Args:
        name: 姓名（如"李阳州"）
        output_dir: 输出目录，默认为 static/avatars/default
        
    Returns:
        str: 生成的文件路径
        
    AI维护注意点:
    1. 取姓名第一个字符（通常是姓氏）
    2. 圆形头像，白色文字
    3. 字体回退：先尝试Arial，再尝试系统默认
    """
    if not name:
        name = "匿名"
    
    # 取第一个字符（通常是姓氏）
    char = name[0].upper() if name[0].isalpha() else name[0]
    
    # 确定输出路径
    if output_dir is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        output_dir = os.path.join(base_dir, 'static', 'avatars', 'default')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名（使用字符避免特殊字符问题）
    filename = f"{char}.png"
    filepath = os.path.join(output_dir, filename)
    
    # 如果已存在，直接返回
    if os.path.exists(filepath):
        return filepath
    
    # 创建80x80像素的图像
    size = 80
    img = Image.new('RGB', (size, size), get_color_for_name(name))
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体（优先Arial，其次是系统默认）
    font = None
    font_size = 36
    
    try:
        # Windows系统字体
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/simsun.ttc",  # 宋体（支持中文）
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
    except:
        pass
    
    if font is None:
        # 使用默认字体
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), char, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]
    
    # 绘制白色文字
    draw.text((x, y), char, fill=(255, 255, 255), font=font)
    
    # 保存
    img.save(filepath, 'PNG')
    
    return filepath


def generate_all_default_avatars(names: list = None):
    """
    批量生成默认头像
    
    AI维护注意点:
    预生成常见姓氏的头像，提升首次加载速度
    """
    if names is None:
        # 常见姓氏（中文+英文）
        names = [
            # 中文常见姓氏
            "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
            "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
            "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
            "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎",
            "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜",
            "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆",
            "郝", "孔", "白", "崔", "康", "毛", "邱", "秦", "江", "史",
            "顾", "侯", "邵", "孟", "龙", "万", "段", "雷", "钱", "汤",
            "尹", "黎", "易", "常", "武", "乔", "贺", "赖", "龚", "文",
            # 英文首字母
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
            "U", "V", "W", "X", "Y", "Z",
            # 特殊
            "光", "影", "时", "团", "声", "J", "S"  # 你的示例分享者
        ]
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'avatars', 'default')
    
    for name in names:
        generate_default_avatar(name, output_dir)
    
    print(f"已生成 {len(names)} 个默认头像")


if __name__ == "__main__":
    # 测试生成
    generate_all_default_avatars()
    
    # 测试特定姓名
    test_names = ["李阳州", "小马哥", "Judy", "光影", "时成成"]
    for name in test_names:
        path = generate_default_avatar(name)
        print(f"生成头像：{name} -> {path}")
