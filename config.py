import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8605
HOST = "127.0.0.1"

STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
OUTPUT_DIR = os.path.join(STORAGE_DIR, "outputs")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

for d in [STORAGE_DIR, UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

STATS_FILE = os.path.join(DATA_DIR, "stats.json")

MAX_UPLOAD_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_LEVEL = "INFO"

STYLES = [
    {"id": "anime", "name": "动漫风", "description": "将照片转换为日系动漫风格，色彩鲜艳线条清晰"},
    {"id": "sketch", "name": "手绘素描", "description": "铅笔素描效果，模拟手绘质感"},
    {"id": "vintage", "name": "复古胶片", "description": "怀旧胶片色调，颗粒感复古氛围"},
    {"id": "cartoon", "name": "卡通涂鸦", "description": "夸张色彩和轮廓，童趣涂鸦风格"},
    {"id": "oil_paint", "name": "油画风格", "description": "模拟油画笔触，厚重艺术质感"},
    {"id": "watercolor", "name": "水彩画", "description": "清新透明水彩效果，柔和晕染"},
    {"id": "pixel", "name": "像素风", "description": "复古像素艺术，游戏怀旧感"},
    {"id": "cyberpunk", "name": "赛博朋克", "description": "霓虹光影，未来科技感"},
]
