#!/usr/bin/env python3
"""
Update category names for tenant 3 based on actual image content.
Supports 6 languages: zh-hans, en, zh-hant, ja, ko, fr
"""
import pymysql

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'multi_tenant_db_dev',
    'charset': 'utf8mb4'
}

# Category name mappings with translations
# Format: category_id: {lang_code: name}
CATEGORY_NAMES = {
    10: {
        'zh-hans': '萌趣涂鸦',
        'zh-hant': '萌趣塗鴉',
        'en': 'Cute Doodles',
        'ja': 'かわいい落書き',
        'ko': '귀여운 낙서',
        'fr': 'Gribouillages Mignons'
    },
    11: {
        'zh-hans': '禅绕动物',
        'zh-hant': '禪繞動物',
        'en': 'Zentangle Animals',
        'ja': 'ゼンタングル動物',
        'ko': '젠탱글 동물',
        'fr': 'Animaux Zentangle'
    },
    12: {
        'zh-hans': '二次元少女',
        'zh-hant': '二次元少女',
        'en': 'Anime Girls',
        'ja': 'アニメ少女',
        'ko': '애니메이션 소녀',
        'fr': 'Filles Anime'
    },
    13: {
        'zh-hans': '欢乐卡通',
        'zh-hant': '歡樂卡通',
        'en': 'Fun Cartoons',
        'ja': '楽しいアニメ',
        'ko': '즐거운 만화',
        'fr': 'Dessins Animés'
    },
    14: {
        'zh-hans': '蝶舞翩翩',
        'zh-hant': '蝶舞翩翩',
        'en': 'Dancing Butterflies',
        'ja': '舞う蝶々',
        'ko': '춤추는 나비',
        'fr': 'Papillons Dansants'
    },
    # 15 - 保持原名 曼陀罗图案
    16: {
        'zh-hans': '星际探索',
        'zh-hant': '星際探索',
        'en': 'Space Adventure',
        'ja': '宇宙探検',
        'ko': '우주 탐험',
        'fr': 'Aventure Spatiale'
    },
    17: {
        'zh-hans': '缤纷节日',
        'zh-hant': '繽紛節日',
        'en': 'Festive Joy',
        'ja': 'お祭り',
        'ko': '축제',
        'fr': 'Fêtes Joyeuses'
    },
    18: {
        'zh-hans': '鸟语花香',
        'zh-hant': '鳥語花香',
        'en': 'Birds & Blooms',
        'ja': '鳥と花',
        'ko': '새와 꽃',
        'fr': 'Oiseaux et Fleurs'
    },
    19: {
        'zh-hans': '闺蜜时光',
        'zh-hant': '閨蜜時光',
        'en': 'Bestie Moments',
        'ja': '親友タイム',
        'ko': '베프 타임',
        'fr': 'Moments Entre Amies'
    },
    20: {
        'zh-hans': '甜美女孩',
        'zh-hant': '甜美女孩',
        'en': 'Sweet Girls',
        'ja': 'スイートガール',
        'ko': '스위트 걸',
        'fr': 'Filles Douces'
    },
    21: {
        'zh-hans': '精灵仙子',
        'zh-hant': '精靈仙子',
        'en': 'Fairies & Elves',
        'ja': '妖精',
        'ko': '요정',
        'fr': 'Fées et Elfes'
    },
    22: {
        'zh-hans': '璀璨星空',
        'zh-hant': '璀璨星空',
        'en': 'Starry Night',
        'ja': '星空',
        'ko': '별이 빛나는 밤',
        'fr': 'Nuit Étoilée'
    },
    23: {
        'zh-hans': '埃及风情',
        'zh-hant': '埃及風情',
        'en': 'Egyptian Beauty',
        'ja': 'エジプトの美',
        'ko': '이집트 아름다움',
        'fr': 'Beauté Égyptienne'
    },
    24: {
        'zh-hans': '法老传奇',
        'zh-hant': '法老傳奇',
        'en': 'Pharaoh Legend',
        'ja': 'ファラオ伝説',
        'ko': '파라오 전설',
        'fr': 'Légende du Pharaon'
    },
    25: {
        'zh-hans': '国风美人',
        'zh-hant': '國風美人',
        'en': 'Chinese Beauty',
        'ja': '中国美人',
        'ko': '중국 미인',
        'fr': 'Beauté Chinoise'
    },
    26: {
        'zh-hans': '冬日物语',
        'zh-hant': '冬日物語',
        'en': 'Winter Tales',
        'ja': '冬物語',
        'ko': '겨울 이야기',
        'fr': 'Contes d\'Hiver'
    },
    27: {
        'zh-hans': '天使恋人',
        'zh-hant': '天使戀人',
        'en': 'Angel Lovers',
        'ja': '天使の恋人',
        'ko': '천사 연인',
        'fr': 'Amoureux Angéliques'
    },
    # 28 - 保持原名 曼陀罗花卉
    29: {
        'zh-hans': '温馨家居',
        'zh-hant': '溫馨家居',
        'en': 'Cozy Home',
        'ja': '居心地の良い家',
        'ko': '아늑한 집',
        'fr': 'Maison Douillette'
    },
    30: {
        'zh-hans': '美味时刻',
        'zh-hant': '美味時刻',
        'en': 'Yummy Treats',
        'ja': 'おいしいおやつ',
        'ko': '맛있는 간식',
        'fr': 'Délices Gourmands'
    },
    31: {
        'zh-hans': '复古时光',
        'zh-hant': '復古時光',
        'en': 'Vintage Vibes',
        'ja': 'ヴィンテージ',
        'ko': '빈티지',
        'fr': 'Ambiance Rétro'
    },
    32: {
        'zh-hans': '华夏风韵',
        'zh-hant': '華夏風韻',
        'en': 'Chinese Culture',
        'ja': '中国文化',
        'ko': '중국 문화',
        'fr': 'Culture Chinoise'
    },
    33: {
        'zh-hans': '艺术名画',
        'zh-hant': '藝術名畫',
        'en': 'Famous Art',
        'ja': '名画',
        'ko': '명화',
        'fr': 'Art Célèbre'
    },
    34: {
        'zh-hans': '凯蒂猫',
        'zh-hant': '凱蒂貓',
        'en': 'Hello Kitty',
        'ja': 'ハローキティ',
        'ko': '헬로키티',
        'fr': 'Hello Kitty'
    },
    35: {
        'zh-hans': '洛丽塔',
        'zh-hant': '洛麗塔',
        'en': 'Lolita Style',
        'ja': 'ロリータ',
        'ko': '로리타',
        'fr': 'Style Lolita'
    },
    # 36 喜羊羊 - 保持
    # 37 海底总动员 - 保持
    # 38 小美人鱼 - 保持
    39: {
        'zh-hans': '翠儿与猫',
        'zh-hant': '翠兒與貓',
        'en': 'Tweety & Friends',
        'ja': 'トゥイーティー',
        'ko': '트위티',
        'fr': 'Tweety et Amis'
    },
    # 40 愤怒的小鸟 - 保持
    41: {
        'zh-hans': '爱探险的朵拉',
        'zh-hant': '愛探險的朵拉',
        'en': 'Dora the Explorer',
        'ja': 'ドーラといっしょに大冒険',
        'ko': '도라 더 익스플로러',
        'fr': 'Dora l\'Exploratrice'
    },
    # 42 灰姑娘 - 保持
    43: {
        'zh-hans': '狮子王',
        'zh-hant': '獅子王',
        'en': 'The Lion King',
        'ja': 'ライオンキング',
        'ko': '라이온 킹',
        'fr': 'Le Roi Lion'
    },
    # 44 猫和老鼠 - 保持
    # 45 小熊维尼 - 保持
    # 46 美少女战士 - 保持
    # 47 飞屋环游记 - 保持
    48: {
        'zh-hans': '翱翔蓝天',
        'zh-hant': '翱翔藍天',
        'en': 'Flying High',
        'ja': '大空へ',
        'ko': '창공을 날다',
        'fr': 'Voler Haut'
    },
    49: {
        'zh-hans': '花团锦簇',
        'zh-hant': '花團錦簇',
        'en': 'Floral Beauty',
        'ja': '花の美しさ',
        'ko': '꽃의 아름다움',
        'fr': 'Beauté Florale'
    },
}

def update_category_names():
    """Update category names in database for all languages"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    updated_count = 0
    
    try:
        for category_id, translations in CATEGORY_NAMES.items():
            for lang_code, name in translations.items():
                # Check if translation exists
                check_sql = """
                    SELECT id FROM cms_category_translation 
                    WHERE master_id = %s AND language_code = %s
                """
                cursor.execute(check_sql, (category_id, lang_code))
                result = cursor.fetchone()
                
                if result:
                    # Update existing translation
                    update_sql = """
                        UPDATE cms_category_translation 
                        SET name = %s
                        WHERE master_id = %s AND language_code = %s
                    """
                    cursor.execute(update_sql, (name, category_id, lang_code))
                    print(f"✓ Updated ID {category_id} [{lang_code}]: {name}")
                else:
                    # Insert new translation (copy description from zh-hans if exists)
                    insert_sql = """
                        INSERT INTO cms_category_translation 
                        (master_id, language_code, name, description)
                        VALUES (%s, %s, %s, NULL)
                    """
                    cursor.execute(insert_sql, (category_id, lang_code, name))
                    print(f"+ Inserted ID {category_id} [{lang_code}]: {name}")
                
                updated_count += 1
        
        conn.commit()
        print(f"\n{'='*50}")
        print(f"✓ Successfully updated {updated_count} translations")
        print(f"✓ Categories updated: {len(CATEGORY_NAMES)}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def show_preview():
    """Show current category names before update"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("Current category names (zh-hans):")
    print("-" * 50)
    
    sql = """
        SELECT c.id, ct.name 
        FROM cms_category c
        LEFT JOIN cms_category_translation ct ON c.id = ct.master_id AND ct.language_code = 'zh-hans'
        WHERE c.tenant_id = 3 AND c.is_deleted = 0
        ORDER BY c.id
    """
    cursor.execute(sql)
    
    for row in cursor.fetchall():
        cat_id, name = row
        new_name = CATEGORY_NAMES.get(cat_id, {}).get('zh-hans', '(保持)')
        if cat_id in CATEGORY_NAMES:
            print(f"ID {cat_id}: {name} → {new_name}")
        else:
            print(f"ID {cat_id}: {name} (保持)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        show_preview()
    else:
        print("Updating category names for tenant 3...")
        print("=" * 50)
        update_category_names()
        print("\n✓ Complete!")
