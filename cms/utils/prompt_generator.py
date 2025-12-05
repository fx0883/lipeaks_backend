"""
提示词生成器（专为涂色书应用优化）
将分类名称转换为高质量的图像生成提示词
"""
import re
from typing import Dict, Optional


class PromptGenerator:
    """提示词生成器 - 为涂色书40个分类生成具体的视觉元素"""
    
    # 分类到具体视觉元素的映射
    CATEGORY_VISUALS = {
        # 迪士尼/卡通角色
        "小飞象": {
            "objects": ["cute elephant with big ears flying", "circus tent", "magical feather"],
            "scene": "colorful circus performance in sky",
            "colors": ["soft gray", "baby blue", "pink"],
            "style": "Disney animation style, cute whimsical"
        },
        "超级马里奥": {
            "objects": ["Mario character jumping", "mushrooms", "question blocks"],
            "scene": "Mushroom Kingdom with pipes",
            "colors": ["red", "blue", "yellow"],
            "style": "Nintendo game colorful"
        },
        "玩具总动员": {
            "objects": ["Woody cowboy toy", "Buzz Lightyear", "toy box"],
            "scene": "playful toy room",
            "colors": ["yellow", "blue", "red"],
            "style": "Pixar animation friendly fun"
        },
        "喜羊羊": {
            "objects": ["cute cartoon sheep", "meadow", "smiling face"],
            "scene": "peaceful grassland blue sky",
            "colors": ["white", "pink", "green"],
            "style": "Chinese cartoon cute friendly"
        },
        "海底总动员": {
            "objects": ["clownfish Nemo", "coral reef", "bubbles"],
            "scene": "colorful underwater ocean",
            "colors": ["orange", "ocean blue", "coral pink"],
            "style": "Pixar underwater vibrant"
        },
        "小美人鱼": {
            "objects": ["mermaid flowing hair", "seashells", "underwater castle"],
            "scene": "magical underwater kingdom",
            "colors": ["seafoam green", "purple", "gold"],
            "style": "Disney fairy tale magical"
        },
        "灰姑娘": {
            "objects": ["princess ball gown", "glass slipper", "castle"],
            "scene": "fairy tale ballroom",
            "colors": ["light blue", "silver", "gold"],
            "style": "Disney princess elegant"
        },
        "阿拉丁": {
            "objects": ["magic lamp", "flying carpet", "Arabian palace"],
            "scene": "Arabian night stars",
            "colors": ["gold", "purple", "turquoise"],
            "style": "Arabian nights exotic magical"
        },
        "小熊维尼": {
            "objects": ["Winnie Pooh bear", "honey pot", "forest"],
            "scene": "cozy forest trees flowers",
            "colors": ["honey yellow", "red", "brown"],
            "style": "Disney classic warm friendly"
        },
        "朵拉": {
            "objects": ["Dora explorer", "backpack", "jungle path"],
            "scene": "adventure tropical jungle",
            "colors": ["pink", "orange", "green"],
            "style": "children cartoon educational"
        },
        "猫和老鼠": {
            "objects": ["Tom cat", "Jerry mouse", "cheese"],
            "scene": "cartoon house interior",
            "colors": ["gray", "brown", "yellow"],
            "style": "classic cartoon playful"
        },
        "愤怒的小鸟": {
            "objects": ["angry birds", "slingshot", "structures"],
            "scene": "game level obstacles",
            "colors": ["red", "yellow", "blue"],
            "style": "mobile game bold simple"
        },
        "崔弟": {
            "objects": ["Tweety yellow bird", "cage", "feathers"],
            "scene": "cartoon living room",
            "colors": ["bright yellow", "blue", "pink"],
            "style": "Looney Tunes cute"
        },
        "飞屋环游记": {
            "objects": ["house balloons", "clouds", "adventure"],
            "scene": "flying in colorful balloons",
            "colors": ["rainbow", "blue sky", "brown"],
            "style": "Pixar heartwarming"
        },
        "美少女战士": {
            "objects": ["sailor warrior", "moon staff", "stars"],
            "scene": "magical girl sparkles",
            "colors": ["pink", "blue", "purple"],
            "style": "anime magical girl"
        },
        
        # 动物类
        "金鱼": {
            "objects": ["goldfish swimming", "aquatic plants", "bubbles"],
            "scene": "peaceful aquarium clear water",
            "colors": ["golden orange", "aqua blue", "green"],
            "style": "coloring book nature"
        },
        "鸟类": {
            "objects": ["colorful birds", "tree branches", "flowers"],
            "scene": "garden blooming flowers",
            "colors": ["red", "blue", "yellow"],
            "style": "nature illustration"
        },
        "狮子": {
            "objects": ["majestic lion", "savanna grass", "sun"],
            "scene": "African savanna sunset",
            "colors": ["golden yellow", "orange", "brown"],
            "style": "wildlife powerful noble"
        },
        
        # 人物类
        "时尚女孩": {
            "objects": ["fashionable girl", "trendy clothes", "accessories"],
            "scene": "fashion boutique",
            "colors": ["pink", "purple", "gold"],
            "style": "fashion illustration chic"
        },
        "女孩": {
            "objects": ["cute girl", "flowers", "butterflies"],
            "scene": "garden decorations",
            "colors": ["soft pink", "lavender", "peach"],
            "style": "cute gentle sweet"
        },
        "人物肖像": {
            "objects": ["portrait face", "detailed hair", "pattern"],
            "scene": "artistic portrait",
            "colors": ["skin tones", "soft background"],
            "style": "portrait art detailed"
        },
        "情侣": {
            "objects": ["couple together", "hearts", "roses"],
            "scene": "romantic flowers hearts",
            "colors": ["red", "pink", "purple"],
            "style": "romantic sweet tender"
        },
        "动漫少女": {
            "objects": ["anime girl", "big eyes", "flowing hair"],
            "scene": "anime sparkles",
            "colors": ["pink", "blue", "pastel"],
            "style": "Japanese anime shoujo"
        },
        "动漫女孩": {
            "objects": ["anime girl", "school uniform", "cherry blossoms"],
            "scene": "school park",
            "colors": ["pink", "blue", "white"],
            "style": "anime cute expressive"
        },
        
        # 曼陀罗图案
        "曼陀罗动物": {
            "objects": ["animal mandala patterns", "geometric shapes"],
            "scene": "decorative mandala art",
            "colors": ["rainbow", "gold", "purple"],
            "style": "mandala intricate meditation"
        },
        "曼陀罗图案": {
            "objects": ["circular mandala", "symmetrical designs", "sacred geometry"],
            "scene": "centered mandala",
            "colors": ["vibrant", "gold", "purple"],
            "style": "traditional mandala symmetrical"
        },
        "曼陀罗花卉": {
            "objects": ["floral mandala", "lotus flowers", "petals circles"],
            "scene": "circular floral mandala",
            "colors": ["pink", "purple", "gold"],
            "style": "floral mandala nature"
        },
        
        # 风景和场景
        "动漫场景": {
            "objects": ["anime landscape", "cherry blossoms", "sunset"],
            "scene": "beautiful anime scenery",
            "colors": ["pink", "orange", "blue"],
            "style": "anime background atmospheric"
        },
        "二次元风景": {
            "objects": ["anime fantasy landscape", "clouds", "mountains"],
            "scene": "fantasy anime world",
            "colors": ["pastel", "blue sky", "pink"],
            "style": "anime fantasy dreamy"
        },
        "古风": {
            "objects": ["Chinese elements", "pavilion", "lanterns"],
            "scene": "classical Chinese garden",
            "colors": ["red", "gold", "jade green"],
            "style": "Chinese traditional elegant"
        },
        "日式风格": {
            "objects": ["Japanese elements", "torii gate", "koi fish"],
            "scene": "Japanese garden temple",
            "colors": ["red", "white", "gold"],
            "style": "Japanese art zen"
        },
        
        # 节日和主题
        "圣诞节": {
            "objects": ["Christmas tree", "Santa Claus", "presents"],
            "scene": "festive Christmas",
            "colors": ["red", "green", "gold"],
            "style": "Christmas festive joyful"
        },
        "爱心": {
            "objects": ["heart shapes", "roses", "ribbons"],
            "scene": "romantic love theme",
            "colors": ["red", "pink", "white"],
            "style": "love sweet romantic"
        },
        
        # 花卉和自然
        "荷花": {
            "objects": ["lotus flowers", "lily pads", "dragonflies"],
            "scene": "peaceful pond blooming",
            "colors": ["pink", "white", "green"],
            "style": "Chinese flower elegant"
        },
        "花卉": {
            "objects": ["various flowers", "roses", "tulips"],
            "scene": "garden blooming flowers",
            "colors": ["red", "pink", "yellow"],
            "style": "floral botanical detailed"
        },
        
        # 食物和物品
        "美食": {
            "objects": ["delicious food", "cakes", "desserts"],
            "scene": "appetizing food display",
            "colors": ["warm browns", "cream", "red"],
            "style": "food illustration cute"
        },
        "汽车": {
            "objects": ["cool cars", "racing cars", "wheels"],
            "scene": "race track street",
            "colors": ["red", "blue", "black"],
            "style": "vehicle dynamic detailed"
        },
        "战斗机": {
            "objects": ["fighter jets", "clouds", "sky"],
            "scene": "aerial combat",
            "colors": ["silver", "blue", "gray"],
            "style": "military aircraft powerful"
        },
        
        # 艺术和创意
        "音乐": {
            "objects": ["musical notes", "instruments", "guitar"],
            "scene": "concert music studio",
            "colors": ["purple", "gold", "black"],
            "style": "music art rhythmic"
        },
        "创意插画": {
            "objects": ["artistic elements", "paint brushes", "canvas"],
            "scene": "art studio creative",
            "colors": ["rainbow", "vibrant mix"],
            "style": "creative imaginative colorful"
        }
    }
    
    # 默认视觉元素
    DEFAULT_VISUALS = {
        "objects": ["abstract shapes", "gradient orbs", "light rays"],
        "scene": "minimalist abstract background",
        "colors": ["blue", "purple", "teal"],
        "style": "modern abstract professional"
    }
    
    def __init__(self, default_style: str = "modern"):
        self.default_style = default_style
        
    def get_visual_elements(self, category_name: str) -> Dict:
        """获取分类的视觉元素"""
        for key, visuals in self.CATEGORY_VISUALS.items():
            if key in category_name:
                return visuals
        return self.DEFAULT_VISUALS
    
    def generate_prompt(self, category_name: str, 
                       style: Optional[str] = None,
                       custom_elements: Optional[list] = None) -> Dict[str, str]:
        """生成图片提示词（为Flux模型优化）"""
        clean_name = self._clean_category_name(category_name)
        visuals = self.get_visual_elements(category_name)
        
        # 构建clip_l提示词（关键词风格）
        clip_l_elements = []
        if visuals["objects"]:
            clip_l_elements.extend(visuals["objects"])
        clip_l_elements.append(visuals["scene"])
        clip_l_elements.append(", ".join(visuals["colors"]))
        clip_l_elements.append(visuals["style"])
        clip_l_elements.extend(["high quality", "detailed", "8k"])
        
        clip_l_prompt = ", ".join(clip_l_elements)
        
        # 构建t5xxl提示词（叙述风格）
        t5xxl_prompt = f"Create a stunning cover image for '{clean_name}' category. "
        t5xxl_prompt += f"The scene shows {' and '.join(visuals['objects'])} "
        t5xxl_prompt += f"in {visuals['scene']}. "
        t5xxl_prompt += f"Use colors: {', '.join(visuals['colors'])}. "
        t5xxl_prompt += f"Style: {visuals['style']}. "
        t5xxl_prompt += f"Perfect for coloring book at 670x360 pixels."
        
        return {
            "clip_l": clip_l_prompt,
            "t5xxl": t5xxl_prompt,
            "main_prompt": clip_l_prompt,
            "guidance_prompt": t5xxl_prompt,
            "style": visuals["style"]
        }
        
    def _clean_category_name(self, name: str) -> str:
        """清理分类名称"""
        clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', name)
        clean = ' '.join(clean.split())
        return clean
