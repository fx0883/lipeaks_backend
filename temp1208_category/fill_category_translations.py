"""
为租户1的所有分类填充多语言翻译

分类名称翻译表：
- How To: 使用指南 / ハウツー / 사용법 / Comment faire
- Review: 评测 / レビュー / 리뷰 / Avis
- Tutorial: 教程 / チュートリアル / 튜토리얼 / Tutoriel
- Update: 更新动态 / アップデート / 업데이트 / Mise à jour
- News: 新闻资讯 / ニュース / 뉴스 / Actualités
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cms.models import Category

# 分类多语言翻译映射
CATEGORY_TRANSLATIONS = {
    'How To': {
        'zh-hans': {'name': '使用指南', 'description': '产品使用方法和操作技巧'},
        'zh-hant': {'name': '使用指南', 'description': '產品使用方法和操作技巧'},
        'en': {'name': 'How To', 'description': 'Product usage and tips'},
        'ja': {'name': 'ハウツー', 'description': '製品の使い方とヒント'},
        'ko': {'name': '사용법', 'description': '제품 사용법 및 팁'},
        'fr': {'name': 'Comment faire', 'description': 'Utilisation du produit et astuces'},
    },
    'Review': {
        'zh-hans': {'name': '评测', 'description': '产品详细评测和分析'},
        'zh-hant': {'name': '評測', 'description': '產品詳細評測和分析'},
        'en': {'name': 'Review', 'description': 'Detailed product reviews and analysis'},
        'ja': {'name': 'レビュー', 'description': '製品の詳細レビューと分析'},
        'ko': {'name': '리뷰', 'description': '상세 제품 리뷰 및 분석'},
        'fr': {'name': 'Avis', 'description': 'Avis et analyses détaillés des produits'},
    },
    'Tutorial': {
        'zh-hans': {'name': '教程', 'description': '详细的学习教程'},
        'zh-hant': {'name': '教程', 'description': '詳細的學習教程'},
        'en': {'name': 'Tutorial', 'description': 'Detailed learning tutorials'},
        'ja': {'name': 'チュートリアル', 'description': '詳細な学習チュートリアル'},
        'ko': {'name': '튜토리얼', 'description': '상세 학습 튜토리얼'},
        'fr': {'name': 'Tutoriel', 'description': 'Tutoriels d\'apprentissage détaillés'},
    },
    'Update': {
        'zh-hans': {'name': '更新动态', 'description': '最新更新和版本信息'},
        'zh-hant': {'name': '更新動態', 'description': '最新更新和版本資訊'},
        'en': {'name': 'Update', 'description': 'Latest updates and version info'},
        'ja': {'name': 'アップデート', 'description': '最新のアップデートとバージョン情報'},
        'ko': {'name': '업데이트', 'description': '최신 업데이트 및 버전 정보'},
        'fr': {'name': 'Mise à jour', 'description': 'Dernières mises à jour et informations de version'},
    },
    'News': {
        'zh-hans': {'name': '新闻资讯', 'description': '行业新闻和最新动态'},
        'zh-hant': {'name': '新聞資訊', 'description': '行業新聞和最新動態'},
        'en': {'name': 'News', 'description': 'Industry news and latest updates'},
        'ja': {'name': 'ニュース', 'description': '業界ニュースと最新情報'},
        'ko': {'name': '뉴스', 'description': '업계 뉴스 및 최신 소식'},
        'fr': {'name': 'Actualités', 'description': 'Actualités du secteur et dernières nouvelles'},
    },
}

def fill_translations():
    """为租户1的所有分类填充多语言翻译"""
    tenant_id = 1
    categories = Category.objects.filter(tenant_id=tenant_id)
    
    print(f"找到 {categories.count()} 个分类")
    
    for category in categories:
        # 获取当前英文名（作为key）
        en_name = category.safe_translation_getter('name', language_code='en') or \
                  category.safe_translation_getter('name', any_language=True)
        
        if en_name in CATEGORY_TRANSLATIONS:
            translations = CATEGORY_TRANSLATIONS[en_name]
            print(f"\n更新分类 ID={category.id}: {en_name}")
            
            for lang_code, fields in translations.items():
                category.set_current_language(lang_code)
                category.name = fields['name']
                category.description = fields['description']
                print(f"  - {lang_code}: {fields['name']}")
            
            category.save()
            print(f"  ✅ 已保存")
        else:
            print(f"\n⚠️ 分类 ID={category.id} ({en_name}) 没有预定义的翻译")

if __name__ == '__main__':
    fill_translations()
    print("\n完成！")
