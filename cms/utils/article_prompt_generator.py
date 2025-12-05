"""
文章提示词生成器 V2
专门为技术类文章生成多样化风格的封面图片提示词
每篇文章根据ID哈希生成独特的视觉风格
"""
import re
import hashlib
from typing import Dict, Optional


class ArticlePromptGenerator:
    """文章提示词生成器 - 多样化风格，每篇文章独特"""
    
    # 8种不同的视觉风格布局
    VISUAL_LAYOUTS = [
        {
            "style": "laptop centered with floating icons",
            "description": "Laptop computer in center, various tech icons floating around symmetrically"
        },
        {
            "style": "isometric 3D composition",
            "description": "Isometric view with 3D elements, geometric shapes in perspective"
        },
        {
            "style": "abstract geometric shapes",
            "description": "Abstract modern design with geometric patterns and tech symbols integrated"
        },
        {
            "style": "workflow diagram",
            "description": "Technical flowchart style with icons connected by lines and arrows"
        },
        {
            "style": "split screen dual tone",
            "description": "Bold split screen design with contrasting sections and icons"
        },
        {
            "style": "circular radial layout",
            "description": "Circular arrangement with icons placed radially around center"
        },
        {
            "style": "layered depth composition",
            "description": "Multiple layers creating depth with shadows and overlapping elements"
        },
        {
            "style": "minimal single focus",
            "description": "Single large central icon or symbol, ultra minimalist approach"
        }
    ]
    
    # 技术主题图标库
    TECH_ICONS = {
        "video": ["play button", "film reel", "video camera", "timeline", "video file", "clapperboard"],
        "compress": ["compression arrows", "zip folder", "archive box", "gauge meter", "size indicator"],
        "file": ["document stack", "folder", "filing cabinet", "paper sheets", "storage box"],
        "optimize": ["speed gauge", "upward arrows", "performance chart", "efficiency icon", "checkmark"],
        "image": ["photo frame", "image gallery", "picture icon", "camera lens", "image stack"],
        "audio": ["sound waves", "equalizer bars", "speaker", "headphones", "microphone"],
        "quality": ["star rating", "quality badge", "certification seal", "premium icon"],
        "software": ["application window", "code brackets", "software interface", "app icon"],
        "storage": ["cloud", "hard drive", "server", "database", "storage unit"],
        "security": ["lock", "shield", "key", "fingerprint", "padlock"],
        "network": ["wifi signal", "connection nodes", "network graph", "globe"],
        "data": ["bar chart", "pie chart", "data points", "graph lines", "statistics"]
    }
    
    # 配色方案（12种）
    COLOR_SCHEMES = [
        {"name": "blue_mono", "colors": ["black", "white", "gray", "blue accent"]},
        {"name": "orange_pop", "colors": ["black", "white", "gray", "orange accent"]},
        {"name": "green_fresh", "colors": ["black", "white", "gray", "green accent"]},
        {"name": "purple_tech", "colors": ["black", "white", "gray", "purple accent"]},
        {"name": "teal_modern", "colors": ["black", "white", "gray", "teal accent"]},
        {"name": "red_bold", "colors": ["black", "white", "gray", "red accent"]},
        {"name": "yellow_bright", "colors": ["black", "white", "gray", "yellow accent"]},
        {"name": "pink_soft", "colors": ["black", "white", "gray", "pink accent"]},
        {"name": "multi_vibrant", "colors": ["black", "white", "multiple color accents"]},
        {"name": "gradient_blue", "colors": ["white", "blue gradient", "dark accents"]},
        {"name": "minimal_bw", "colors": ["pure black", "pure white", "no colors"]},
        {"name": "warm_earth", "colors": ["beige", "brown", "cream", "warm accents"]}
    ]
    
    def __init__(self):
        pass
    
    def _get_deterministic_index(self, text: str, max_value: int) -> int:
        """基于文本生成确定性索引（用于选择风格）"""
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        return hash_int % max_value
    
    def detect_keywords(self, title: str, excerpt: str = None) -> list:
        """检测文章关键词，返回匹配的主题列表"""
        text = (title + " " + (excerpt or "")).lower()
        matched_themes = []
        
        for theme, icons in self.TECH_ICONS.items():
            if theme in text:
                matched_themes.append(theme)
        
        # 如果没有匹配，返回通用主题
        if not matched_themes:
            matched_themes = ["file", "software"]
        
        return matched_themes[:2]  # 最多2个主题
    
    def generate_prompt(self, title: str, excerpt: str = None, article_id: int = None) -> Dict[str, str]:
        """
        为文章生成独特的图片提示词
        使用article_id确保每篇文章风格不同
        """
        clean_title = self._clean_text(title)
        clean_excerpt = self._clean_text(excerpt) if excerpt else ""
        
        # 使用文章ID选择风格（确保相同文章始终得到相同风格）
        seed = f"{article_id}_{clean_title}" if article_id else clean_title
        
        # 选择视觉布局
        layout_index = self._get_deterministic_index(seed, len(self.VISUAL_LAYOUTS))
        layout = self.VISUAL_LAYOUTS[layout_index]
        
        # 选择配色方案
        color_index = self._get_deterministic_index(seed + "_color", len(self.COLOR_SCHEMES))
        color_scheme = self.COLOR_SCHEMES[color_index]
        
        # 检测主题并选择图标
        themes = self.detect_keywords(title, excerpt)
        selected_icons = []
        for theme in themes:
            if theme in self.TECH_ICONS:
                icons = self.TECH_ICONS[theme]
                # 使用哈希选择该主题的特定图标
                icon_index = self._get_deterministic_index(seed + theme, len(icons))
                selected_icons.append(icons[icon_index])
        
        # 如果没有图标，使用默认
        if not selected_icons:
            selected_icons = ["tech symbol", "digital icon"]
        
        # 构建clip_l提示词（Doodle Art风格）
        clip_l_elements = [
            layout["style"],
            ", ".join(selected_icons),
            ", ".join(color_scheme["colors"]),
            "doodle art style",
            "hand-drawn sketch",
            "casual playful illustration",
            "imperfect organic lines",
            "whimsical naive drawing",
            "selective color accents",
            "loose sketchy lines"
        ]
        
        clip_l_prompt = ", ".join(clip_l_elements)
        
        # 构建t5xxl提示词（详细叙述 - Doodle Art风格）
        t5xxl_prompt = f"Create a hand-drawn doodle art cover image for article: '{clean_title}'. "
        
        if clean_excerpt:
            t5xxl_prompt += f"About: {clean_excerpt[:80]}. "
        
        t5xxl_prompt += f"Visual composition: {layout['description']}. "
        t5xxl_prompt += f"Main elements: {', '.join(selected_icons)} drawn in playful sketch style. "
        t5xxl_prompt += f"Color approach: primarily black hand-drawn lines with selective color accents in {', '.join(color_scheme['colors'])}. "
        t5xxl_prompt += f"Drawing style: casual, whimsical, hand-sketched with imperfect organic lines. "
        t5xxl_prompt += f"The lines should look hand-drawn, not perfect or geometric. "
        t5xxl_prompt += f"Add playful details like small decorative elements, squiggly lines, or doodle embellishments. "
        t5xxl_prompt += f"Use naive illustration approach with simple, charming character. "
        t5xxl_prompt += f"Background should be clean white or very light with minimal decoration. "
        t5xxl_prompt += f"Overall feel: friendly, approachable, creative doodle art for tech blog. "
        t5xxl_prompt += f"Perfect for 382x256 pixels article cover. "
        t5xxl_prompt += f"No text, no typography, only hand-drawn visual elements."
        
        return {
            "clip_l": clip_l_prompt,
            "t5xxl": t5xxl_prompt,
            "main_prompt": clip_l_prompt,
            "guidance_prompt": t5xxl_prompt,
            "style": f"{layout['style']} - {color_scheme['name']}",
            "layout": layout["style"],
            "colors": color_scheme["name"]
        }
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        clean = re.sub(r'[^\w\s]', ' ', text)
        clean = ' '.join(clean.split())
        return clean[:150]
