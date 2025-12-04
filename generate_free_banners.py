#!/usr/bin/env python3
"""
Generate free artistic banner images and update database
Using abstract patterns with smooth gradients
Size: 670 x 360 px
"""
from PIL import Image, ImageDraw, ImageFilter
import os, random, math
import pymysql

# Output
TARGET_W, TARGET_H = 670, 360
OUTPUT_DIR = "/Users/fengxuan/Documents/Github/lipeaks_backend/media/category_image"

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': '123456',
    'database': 'multi_tenant_db_dev',
    'charset': 'utf8mb4'
}

# Color themes for each category
THEMES = {
    10: {"colors": [(135,206,235), (255,182,193), (255,255,255)], "style": "clouds"},  # Dumbo - 天空云朵
    11: {"colors": [(0,191,255), (255,215,0), (0,100,200)], "style": "waves"},  # Goldfish - 水波
    12: {"colors": [(255,105,180), (255,20,147), (255,255,255)], "style": "sparkle"},  # Fashion - 闪烁
    13: {"colors": [(255,0,0), (0,255,0), (255,215,0)], "style": "blocks"},  # Mario - 方块
    14: {"colors": [(148,0,211), (255,215,0), (75,0,130)], "style": "mandala"},  # Mandala Animal
    15: {"colors": [(138,43,226), (255,255,255), (75,0,130)], "style": "mandala"},  # Mandala Pattern
    16: {"colors": [(255,99,71), (30,144,255), (255,215,0)], "style": "confetti"},  # Toys - 彩纸
    17: {"colors": [(220,20,60), (0,100,0), (255,255,255)], "style": "snow"},  # Christmas - 雪花
    18: {"colors": [(135,206,250), (255,255,255), (255,215,0)], "style": "feathers"},  # Birds - 羽毛
    19: {"colors": [(255,218,185), (255,160,122), (205,133,63)], "style": "portrait"},  # Portrait - 剪影
    20: {"colors": [(255,182,193), (255,105,180), (255,255,255)], "style": "hearts"},  # Girls - 爱心
    21: {"colors": [(148,0,211), (255,215,0), (25,25,112)], "style": "stars"},  # Aladdin - 星星
    22: {"colors": [(255,20,147), (255,105,180), (255,182,193)], "style": "hearts"},  # Hearts
    23: {"colors": [(255,182,193), (255,255,255), (220,20,60)], "style": "sakura"},  # Japanese - 樱花
    24: {"colors": [(70,130,180), (192,192,192), (255,0,0)], "style": "speed"},  # Cars - 速度线
    25: {"colors": [(139,0,0), (255,215,0), (0,0,0)], "style": "pattern"},  # Ancient - 古典纹样
    26: {"colors": [(255,192,203), (147,112,219), (255,255,255)], "style": "sparkle"},  # Anime Girl
    27: {"colors": [(255,105,180), (255,20,147), (255,255,255)], "style": "hearts"},  # Couple
    28: {"colors": [(186,104,200), (255,255,255), (156,39,176)], "style": "mandala"},  # Mandala Flower
    29: {"colors": [(135,206,235), (144,238,144), (255,255,255)], "style": "landscape"},  # Anime Scene
    30: {"colors": [(255,140,0), (255,69,0), (255,215,0)], "style": "circles"},  # Food - 圆盘
    31: {"colors": [(255,127,80), (64,224,208), (147,112,219)], "style": "paint"},  # Creative - 涂鸦
    32: {"colors": [(75,0,130), (255,215,0), (255,255,255)], "style": "waves"},  # Music - 音波
    33: {"colors": [(255,182,193), (144,238,144), (255,255,255)], "style": "lotus"},  # Lotus
    34: {"colors": [(255,182,193), (230,230,250), (255,105,180)], "style": "sparkle"},  # Anime Girl
    35: {"colors": [(135,206,235), (144,238,144), (255,255,255)], "style": "landscape"},  # Scenery
    36: {"colors": [(255,255,255), (144,238,144), (255,228,225)], "style": "clouds"},  # Sheep
    37: {"colors": [(0,191,255), (0,139,139), (127,255,212)], "style": "waves"},  # Ocean
    38: {"colors": [(127,255,212), (255,105,180), (138,43,226)], "style": "scales"},  # Mermaid
    39: {"colors": [(255,255,0), (255,215,0), (255,165,0)], "style": "circles"},  # Tweety
    40: {"colors": [(255,0,0), (255,140,0), (139,0,0)], "style": "angry"},  # Angry Birds
    41: {"colors": [(255,165,0), (255,99,71), (255,215,0)], "style": "adventure"},  # Dora
    42: {"colors": [(135,206,250), (255,255,255), (192,192,192)], "style": "sparkle"},  # Cinderella
    43: {"colors": [(255,165,0), (139,69,19), (255,215,0)], "style": "sun"},  # Lion
    44: {"colors": [(128,128,128), (139,69,19), (255,255,255)], "style": "chase"},  # Tom & Jerry
    45: {"colors": [(255,215,0), (255,140,0), (139,69,19)], "style": "honey"},  # Pooh
    46: {"colors": [(255,182,193), (255,215,0), (147,112,219)], "style": "moon"},  # Sailor Moon
    47: {"colors": [(135,206,250), (255,255,0), (255,182,193)], "style": "balloons"},  # Up
    48: {"colors": [(70,130,180), (192,192,192), (0,0,139)], "style": "speed"},  # Jet
    49: {"colors": [(255,182,193), (255,105,180), (144,238,144)], "style": "flowers"},  # Flowers
}

def gradient_background(draw, w, h, color1, color2):
    """Create vertical gradient"""
    for y in range(h):
        r = int(color1[0] + (color2[0] - color1[0]) * y / h)
        g = int(color1[1] + (color2[1] - color1[1]) * y / h)
        b = int(color1[2] + (color2[2] - color1[2]) * y / h)
        draw.rectangle([0, y, w, y+1], fill=(r, g, b))

def draw_soft_circle(draw, x, y, r, color, alpha=255):
    """Draw soft circle with transparency"""
    for i in range(r, 0, -2):
        a = int(alpha * (i / r) ** 0.5)
        c = (*color, a) if len(color) == 3 else color
        draw.ellipse([x-i, y-i, x+i, y+i], fill=c)

def generate_style(img, draw, style, colors):
    """Generate different artistic styles"""
    w, h = img.size
    
    # Gradient background
    gradient_background(draw, w, h, colors[0], colors[1])
    
    if style == "clouds":
        # Soft cloud shapes
        for _ in range(8):
            x, y = random.randint(50, w-50), random.randint(30, h-30)
            r = random.randint(40, 80)
            draw_soft_circle(draw, x, y, r, colors[2], 80)
            
    elif style == "waves":
        # Wave patterns
        for i in range(3):
            points = []
            for x in range(0, w+20, 20):
                y = h//2 + i*60 - 60 + math.sin(x*0.02) * 30
                points.append((x, y))
            points.extend([(w, h), (0, h)])
            draw.polygon(points, fill=(*colors[2], 100))
            
    elif style == "sparkle":
        # Sparkles and stars
        for _ in range(30):
            x, y = random.randint(20, w-20), random.randint(20, h-20)
            size = random.randint(5, 15)
            draw.polygon([(x, y-size), (x+size//3, y-size//3), (x+size, y),
                         (x+size//3, y+size//3), (x, y+size), (x-size//3, y+size//3),
                         (x-size, y), (x-size//3, y-size//3)], fill=colors[2])
                         
    elif style == "blocks":
        # Mario-style blocks
        block_size = 40
        for i in range(0, w, block_size*2):
            for j in range(0, h, block_size*2):
                if random.random() > 0.5:
                    c = colors[2] if random.random() > 0.5 else colors[1]
                    draw.rectangle([i, j, i+block_size, j+block_size], fill=c)
                    
    elif style == "mandala":
        # Circular mandala pattern
        cx, cy = w//2, h//2
        for ring in range(8, 0, -1):
            r = ring * 20
            num = ring * 6
            for i in range(num):
                angle = i * 2 * math.pi / num
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                draw.ellipse([x-10, y-10, x+10, y+10], fill=colors[2])
                
    elif style == "confetti":
        # Scattered confetti
        for _ in range(50):
            x, y = random.randint(0, w), random.randint(0, h)
            shape = random.choice(['rect', 'circle', 'triangle'])
            c = random.choice(colors)
            size = random.randint(10, 30)
            if shape == 'rect':
                angle = random.randint(0, 360)
                draw.rectangle([x, y, x+size, y+size//2], fill=c)
            elif shape == 'circle':
                draw.ellipse([x, y, x+size, y+size], fill=c)
                
    elif style == "snow":
        # Snowflakes
        for _ in range(20):
            x, y = random.randint(20, w-20), random.randint(20, h-20)
            size = random.randint(10, 25)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x2 = x + size * math.cos(rad)
                y2 = y + size * math.sin(rad)
                draw.line([(x, y), (x2, y2)], fill=colors[2], width=2)
                
    elif style == "hearts":
        # Heart shapes
        for _ in range(15):
            x, y = random.randint(30, w-30), random.randint(30, h-30)
            size = random.randint(20, 40)
            # Simple heart using circles and triangle
            draw.ellipse([x-size//2, y-size//2, x, y], fill=colors[2])
            draw.ellipse([x, y-size//2, x+size//2, y], fill=colors[2])
            draw.polygon([(x-size//2, y-size//4), (x+size//2, y-size//4), (x, y+size//2)], fill=colors[2])
            
    elif style == "sakura":
        # Cherry blossoms
        for _ in range(12):
            x, y = random.randint(30, w-30), random.randint(30, h-30)
            size = random.randint(20, 35)
            # Five petals
            for i in range(5):
                angle = i * 72 - 90
                rad = math.radians(angle)
                px = x + size * 0.5 * math.cos(rad)
                py = y + size * 0.5 * math.sin(rad)
                draw.ellipse([px-size//3, py-size//3, px+size//3, py+size//3], fill=colors[2])
            draw.ellipse([x-8, y-8, x+8, y+8], fill=colors[1])
            
    elif style == "landscape":
        # Mountains and sun
        # Mountains
        draw.polygon([(0, h), (w//3, h//3), (w//2, h)], fill=(*colors[1], 150))
        draw.polygon([(w//4, h), (w//2, h//2), (3*w//4, h)], fill=(*colors[1], 120))
        draw.polygon([(w//2, h), (3*w//4, h//3), (w, h)], fill=(*colors[1], 100))
        # Sun
        draw.ellipse([w-100, 30, w-30, 100], fill=colors[2])
        
    elif style == "flowers":
        # Flower pattern
        for _ in range(10):
            x, y = random.randint(40, w-40), random.randint(40, h-40)
            size = random.randint(25, 45)
            # Petals
            for i in range(6):
                angle = i * 60
                rad = math.radians(angle)
                px = x + size * 0.6 * math.cos(rad)
                py = y + size * 0.6 * math.sin(rad)
                draw.ellipse([px-size//3, py-size//3, px+size//3, py+size//3], fill=colors[2])
            # Center
            draw.ellipse([x-size//4, y-size//4, x+size//4, y+size//4], fill=colors[1])
            
    else:
        # Default - organic shapes
        for _ in range(20):
            x, y = random.randint(0, w), random.randint(0, h)
            r = random.randint(30, 80)
            c = random.choice(colors)
            draw_soft_circle(draw, x, y, r, c, random.randint(50, 120))

def create_banner(category_id):
    """Create banner for a category"""
    theme = THEMES.get(category_id, {"colors": [(200,200,200), (150,150,150), (255,255,255)], "style": "default"})
    
    # Create image with RGBA for transparency
    img = Image.new('RGBA', (TARGET_W, TARGET_H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Generate pattern
    generate_style(img, draw, theme["style"], theme["colors"])
    
    # Apply soft filter for smoother look
    img = img.filter(ImageFilter.SMOOTH)
    
    # Convert to RGB for saving
    final = Image.new('RGB', (TARGET_W, TARGET_H), (255, 255, 255))
    final.paste(img, (0, 0))
    
    # Save
    output_path = os.path.join(OUTPUT_DIR, f"{category_id}.png")
    final.save(output_path, "PNG", quality=95)
    print(f"✓ Generated: {category_id}.png")
    return output_path

def update_database():
    """Update database with image paths"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Update each category
        for category_id in THEMES.keys():
            image_path = f"/media/category_image/{category_id}.png"
            
            # Update category cover_image
            sql = """
                UPDATE cms_category 
                SET cover_image = %s,
                    updated_at = NOW()
                WHERE id = %s AND tenant_id = 3
            """
            cursor.execute(sql, (image_path, category_id))
            
        conn.commit()
        print(f"\n✓ Database updated: {len(THEMES)} categories")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Database error: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Generating {len(THEMES)} artistic banners...")
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 50)
    
    # Generate all images
    for category_id in THEMES.keys():
        create_banner(category_id)
    
    print("-" * 50)
    print("All images generated!")
    
    # Update database
    print("\nUpdating database...")
    update_database()
    
    print("\n✓ Complete!")

if __name__ == "__main__":
    main()
