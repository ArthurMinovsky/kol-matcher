"""Generate the mixed-industry synthetic demo pool fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "fixtures" / "demo_pool" / "creators.json"


def _post(pid: str, caption: str, hashtags: list[str], views: int, likes: int, comments: int, shares: int):
    return {
        "post_id": pid,
        "caption": caption,
        "hashtags": hashtags,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
    }


_CREATORS = [
    # ── Beauty ─────────────────────────────────────────────────────────────
    {
        "username": "beauty.noon",
        "display_name": "Noon Beauty",
        "bio": "รีวิวสกินแคร์และเมคอัพ ผิวสวยต้องรู้จักตัวเอง",
        "follower_count": 320000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["skincare", "makeup", "beauty review"],
        "style_tags": ["review", "tutorial", "lifestyle"],
        "thai_caption_ratio": 0.9,
        "thai_hashtag_count": 12,
        "posts": [
            ("bn1", "รีวิวเซรั่มลดสิว 7 วัน", ["สกินแคร์", "รีวิว"], 250000, 18000, 1200, 900),
            ("bn2", "เมคอัพลุคใสๆ ไปทำงาน", ["เมคอัพ", "ลุคทำงาน"], 180000, 12000, 800, 500),
        ],
    },
    {
        "username": "derma.doc.view",
        "display_name": "หมอผิวหนังวิว",
        "bio": "แพทย์ผิวหนัง ให้ความรู้เรื่องสิว ฝ้า ริ้วรอย",
        "follower_count": 540000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["dermatology", "skincare", "acne", "beauty education"],
        "style_tags": ["educational", "expert", "tutorial"],
        "thai_caption_ratio": 0.95,
        "thai_hashtag_count": 15,
        "posts": [
            ("dv1", "สิวอักเสบ ดูแลยังไง", ["สิว", "ผิวหนัง"], 400000, 32000, 2100, 1500),
            ("dv2", "ครีมกันแดดทาทุกวัน", ["กันแดด", "ผิว"], 350000, 28000, 1800, 1200),
        ],
    },
    {
        "username": "glow.with.june",
        "display_name": "June Glow",
        "bio": "Skincare routine & honest reviews",
        "follower_count": 180000,
        "location": "Chiang Mai, Thailand",
        "topic_tags": ["skincare", "product review", "self-care"],
        "style_tags": ["review", "lifestyle", "ugc"],
        "thai_caption_ratio": 0.6,
        "thai_hashtag_count": 6,
        "posts": [
            ("gj1", "My morning routine สดใสทั้งวัน", ["skincare", "routine"], 120000, 8500, 500, 300),
            ("gj2", "Honest review กันแดดตัวใหม่", ["review", "sunscreen"], 95000, 6200, 400, 250),
        ],
    },
    {
        "username": "skinlab.min",
        "display_name": "Skin Lab Min",
        "bio": "ผิวสุขภาพดีเริ่มที่วิทยาศาสตร์",
        "follower_count": 760000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["skincare", "ingredient science", "beauty education"],
        "style_tags": ["educational", "expert", "review"],
        "thai_caption_ratio": 0.92,
        "thai_hashtag_count": 14,
        "posts": [
            ("sl1", "Niacinamide ใช้ยังไงให้เห็นผล", ["สกินแคร์", "วิทยาศาสตร์"], 500000, 42000, 2800, 2000),
            ("sl2", "Retinol กับผิวแพ้ง่าย", ["retinol", "ผิวแพ้ง่าย"], 420000, 35000, 2300, 1700),
        ],
    },
    {
        "username": "makeup.pim",
        "display_name": "พิมพ์ เมคอัพ",
        "bio": "แต่งหน้าตามเทรนด์ สอนลุคง่ายๆ",
        "follower_count": 410000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["makeup", "beauty", "tutorial"],
        "style_tags": ["tutorial", "lifestyle", "review"],
        "thai_caption_ratio": 0.88,
        "thai_hashtag_count": 10,
        "posts": [
            ("mp1", "ลุคสายฝอ แต่งง่าย 5 นาที", ["เมคอัพ", "tutorial"], 220000, 15000, 900, 600),
            ("mp2", "รีวิวรองพื้นผิวเงา", ["รองพื้น", "รีวิว"], 190000, 12000, 700, 450),
        ],
    },
    # ── Food ───────────────────────────────────────────────────────────────
    {
        "username": "foodie.bank",
        "display_name": "Bank กินเที่ยว",
        "bio": "กินทั่วไทย รีวิวร้านเด็ด",
        "follower_count": 620000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["food", "restaurant", "street food", "review"],
        "style_tags": ["review", "mukbang", "lifestyle"],
        "thai_caption_ratio": 0.93,
        "thai_hashtag_count": 11,
        "posts": [
            ("fb1", "ก๋วยเตี๋ยวเรือเจ้าเด็ดย่านวังหลัง", ["ก๋วยเตี๋ยว", "streetfood"], 380000, 28000, 1800, 1200),
            ("fb2", "ร้านบุฟเฟ่ต์ซีฟู้ดคุ้มมั้ย", ["บุฟเฟ่ต์", "รีวิว"], 310000, 22000, 1400, 900),
        ],
    },
    {
        "username": "chef.nok",
        "display_name": "เชฟนก สอนทำอาหาร",
        "bio": "สูตรอาหารไทยง่ายๆ ทำได้ที่บ้าน",
        "follower_count": 290000,
        "location": "Nonthaburi, Thailand",
        "topic_tags": ["cooking", "recipe", "thai food"],
        "style_tags": ["tutorial", "review", "lifestyle"],
        "thai_caption_ratio": 0.96,
        "thai_hashtag_count": 13,
        "posts": [
            ("cn1", "ต้มยำกุ้งน้ำข้น ทำเองได้", ["สูตรอาหาร", "ต้มยำ"], 210000, 16000, 1000, 800),
            ("cn2", "ผัดไทยไม่ติดกระทะ", ["ผัดไทย", "ทำอาหาร"], 185000, 13000, 850, 650),
        ],
    },
    {
        "username": "sweet.tooth.mint",
        "display_name": "Mint Sweet Tooth",
        "bio": "คาเฟ่ ขนมหวาน ชาไข่มุก",
        "follower_count": 150000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["dessert", "cafe", "food review"],
        "style_tags": ["review", "lifestyle", "ugc"],
        "thai_caption_ratio": 0.85,
        "thai_hashtag_count": 9,
        "posts": [
            ("sm1", "คาเฟ่ใหม่ย่านอารีย์", ["คาเฟ่", "รีวิว"], 130000, 9200, 550, 350),
            ("sm2", "ชาไข่มุกร้านดัง อร่อยจริงมั้ย", ["ชาไข่มุก", "ของหวาน"], 110000, 7800, 480, 300),
        ],
    },
    {
        "username": "mukbang.ton",
        "display_name": "ต้น มุกบัง",
        "bio": "กินจุ กินอร่อย ทุกวัน",
        "follower_count": 880000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["mukbang", "food", "entertainment"],
        "style_tags": ["mukbang", "entertainment", "lifestyle"],
        "thai_caption_ratio": 0.78,
        "thai_hashtag_count": 7,
        "posts": [
            ("mt1", "ชิมบุฟเฟ่ต์อาหารทะเล", ["มุกบัง", "อาหารทะเล"], 600000, 45000, 3200, 2100),
            ("mt2", "กินชาบู 1 ชม", ["ชาบู", "mukbang"], 520000, 39000, 2700, 1800),
        ],
    },
    {
        "username": "easy.recipe.aom",
        "display_name": "อ้อม สูตรง่าย",
        "bio": "สูตรอาหารง่ายๆ 5 นาที",
        "follower_count": 220000,
        "location": "Chonburi, Thailand",
        "topic_tags": ["recipe", "cooking", "food"],
        "style_tags": ["tutorial", "lifestyle"],
        "thai_caption_ratio": 0.94,
        "thai_hashtag_count": 12,
        "posts": [
            ("ea1", "มาม่าผัดกระเทียมพริกไทย", ["สูตรง่าย", "อาหาร"], 170000, 11000, 650, 500),
            ("ea2", "ไข่กระทะอาหารเช้า", ["อาหารเช้า", "สูตร"], 140000, 9000, 520, 400),
        ],
    },
    # ── Travel ─────────────────────────────────────────────────────────────
    {
        "username": "travel.with.ink",
        "display_name": "Ink เที่ยวไปเรื่อย",
        "bio": "พาเที่ยวทั่วไทย ที่พัก คาเฟ่ ธรรมชาติ",
        "follower_count": 470000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["travel", "hotel", "cafe", "nature"],
        "style_tags": ["vlog", "lifestyle", "review"],
        "thai_caption_ratio": 0.9,
        "thai_hashtag_count": 10,
        "posts": [
            ("ti1", "ที่พักวิวทะเลหมอก เขาค้อ", ["ที่พัก", "เขาค้อ"], 290000, 21000, 1300, 900),
            ("ti2", "คาเฟ่ริมแม่น้ำเชียงใหม่", ["คาเฟ่", "เชียงใหม่"], 240000, 17000, 1050, 700),
        ],
    },
    {
        "username": "hotel.hunter.jay",
        "display_name": "Jay Hotel Hunter",
        "bio": "รีวิวโรงแรมและที่พักทั่วเอเชีย",
        "follower_count": 310000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["hotel", "travel", "review"],
        "style_tags": ["review", "lifestyle", "vlog"],
        "thai_caption_ratio": 0.82,
        "thai_hashtag_count": 8,
        "posts": [
            ("hj1", "โรงแรม 5 ดาวราคาหลักพัน", ["โรงแรม", "รีวิว"], 200000, 14000, 850, 550),
            ("hj2", "Pool villa ภูเก็ต คุ้มไหม", ["ภูเก็ต", "ที่พัก"], 175000, 11500, 700, 450),
        ],
    },
    {
        "username": "backpack.beam",
        "display_name": "Beam Backpacker",
        "bio": "เที่ยวเอง งบน้อย ประเทศเพื่อนบ้าน",
        "follower_count": 190000,
        "location": "Chiang Mai, Thailand",
        "topic_tags": ["travel", "budget travel", "itinerary"],
        "style_tags": ["vlog", "ugc", "lifestyle"],
        "thai_caption_ratio": 0.88,
        "thai_hashtag_count": 9,
        "posts": [
            ("bb1", "เที่ยวลาวใต้ 3 วัน 2 คืน", ["เที่ยว", "ลาว"], 160000, 10500, 620, 420),
            ("bb2", "งบ 5,000 เที่ยวเชียงใหม่", ["เชียงใหม่", "งบน้อย"], 145000, 9200, 540, 380),
        ],
    },
    {
        "username": "sea.sun.sand",
        "display_name": "Sea Sun Sand",
        "bio": "ทะเลไทย เกาะสวย น้ำใส",
        "follower_count": 340000,
        "location": "Phuket, Thailand",
        "topic_tags": ["travel", "beach", "island", "nature"],
        "style_tags": ["vlog", "lifestyle", "ugc"],
        "thai_caption_ratio": 0.86,
        "thai_hashtag_count": 10,
        "posts": [
            ("ss1", "เกาะสิมิลัน 1 วัน น้ำใสมาก", ["ทะเล", "ภูเก็ต"], 250000, 19000, 1100, 800),
            ("ss2", "ที่พักติดทะเลกระบี่", ["กระบี่", "ที่พัก"], 210000, 15000, 900, 600),
        ],
    },
    {
        "username": "city.walker.too",
        "display_name": "City Walker Too",
        "bio": "เที่ยวในเมือง คาเฟ่ มิวเซียม สตรีทอาร์ต",
        "follower_count": 130000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["travel", "city", "cafe", "art"],
        "style_tags": ["vlog", "lifestyle", "review"],
        "thai_caption_ratio": 0.91,
        "thai_hashtag_count": 11,
        "posts": [
            ("cw1", "เที่ยวสยามใน 1 วัน", ["กรุงเทพ", "คาเฟ่"], 115000, 7800, 450, 300),
            ("cw2", "พิพิธภัณฑ์ใหม่ย่านฝั่งธน", ["พิพิธภัณฑ์", "เที่ยวกรุงเทพ"], 98000, 6200, 380, 240),
        ],
    },
    # ── Fashion ────────────────────────────────────────────────────────────
    {
        "username": "style.minty",
        "display_name": "Minty Style",
        "bio": "แฟชั่นไทย ลุคทำงาน สไตล์มินิมอล",
        "follower_count": 280000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["fashion", "style", "outfit"],
        "style_tags": ["lifestyle", "lookbook", "review"],
        "thai_caption_ratio": 0.84,
        "thai_hashtag_count": 8,
        "posts": [
            ("smf1", "Mix & match ชุดทำงานสไตล์มินิมอล", ["แฟชั่น", "ลุคทำงาน"], 180000, 13000, 800, 500),
            ("smf2", "รีวิวกระเป๋าผ้าไทย", ["กระเป๋า", "รีวิว"], 150000, 10000, 600, 400),
        ],
    },
    {
        "username": "lookbook.bee",
        "display_name": "Bee Lookbook",
        "bio": "Outfit ideas & thrift haul",
        "follower_count": 210000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["fashion", "outfit", "trend"],
        "style_tags": ["lookbook", "lifestyle", "ugc"],
        "thai_caption_ratio": 0.55,
        "thai_hashtag_count": 5,
        "has_thai_bio": False,
        "posts": [
            ("lb1", "5 ลุคเที่ยวคาเฟ่", ["outfit", "คาเฟ่"], 140000, 9500, 580, 350),
            ("lb2", "Thrift haul กรุงเทพ", ["thrift", "แฟชั่น"], 120000, 7800, 460, 280),
        ],
    },
    {
        "username": "menswear.max",
        "display_name": "Max Menswear",
        "bio": "แฟชั่นผู้ชาย สไตล์ลำลองและทำงาน",
        "follower_count": 170000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["fashion", "menswear", "style"],
        "style_tags": ["lifestyle", "lookbook", "review"],
        "thai_caption_ratio": 0.89,
        "thai_hashtag_count": 9,
        "posts": [
            ("mm1", "Smart casual ผู้ชายไปออฟฟิศ", ["menswear", "ลุคทำงาน"], 110000, 7200, 420, 280),
            ("mm2", "รองเท้าผ้าใบคู่โปรด", ["รองเท้า", "review"], 95000, 5800, 350, 220),
        ],
    },
    {
        "username": "vintage.nana",
        "display_name": "Nana Vintage",
        "bio": "Vintage fashion & sustainable style",
        "follower_count": 145000,
        "location": "Chiang Mai, Thailand",
        "topic_tags": ["fashion", "vintage", "sustainable"],
        "style_tags": ["lifestyle", "lookbook", "ugc"],
        "thai_caption_ratio": 0.7,
        "thai_hashtag_count": 6,
        "posts": [
            ("vn1", "สไตล์วินเทจไปเที่ยวตลาดนัด", ["vintage", "ตลาดนัด"], 98000, 6500, 400, 260),
            ("vn2", "How to style กระโปรงลายดอก", ["fashion", "styling"], 85000, 5200, 320, 200),
        ],
    },
    {
        "username": "street.style.ken",
        "display_name": "Ken Street Style",
        "bio": "Street style Bangkok แต่งตัวเท่ทุกวัน",
        "follower_count": 260000,
        "location": "Bangkok, Thailand",
        "topic_tags": ["fashion", "street style", "trend"],
        "style_tags": ["lifestyle", "lookbook", "ugc"],
        "thai_caption_ratio": 0.87,
        "thai_hashtag_count": 10,
        "posts": [
            ("sk1", "Street style ย่านสiam", ["streetstyle", "กรุงเทพ"], 170000, 12000, 750, 480),
            ("sk2", " layering หน้าหนาวในเมืองร้อน", ["แฟชั่น", "styling"], 145000, 9800, 600, 380),
        ],
    },
]


def _build_creator(data: dict) -> dict:
    posts = [_post(pid, cap, tags, v, l, c, s) for pid, cap, tags, v, l, c, s in data.get("posts", [])]
    return {
        "username": data["username"],
        "display_name": data["display_name"],
        "bio": data["bio"],
        "tiktok_url": f"https://www.tiktok.com/@{data['username']}",
        "follower_count": data["follower_count"],
        "location": data["location"],
        "topic_tags": data["topic_tags"],
        "style_tags": data["style_tags"],
        "language_primary": data.get("language_primary", "th"),
        "thai_caption_ratio": data["thai_caption_ratio"],
        "thai_hashtag_count": data["thai_hashtag_count"],
        "has_thai_bio": data.get("has_thai_bio", True),
        "has_thailand_location": data.get("has_thailand_location", True),
        "recent_posts": posts,
        "source_type": "synthetic",
    }


def main() -> None:
    creators = [_build_creator(c) for c in _CREATORS]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(creators, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(creators)} creators to {OUT}")


if __name__ == "__main__":
    main()
