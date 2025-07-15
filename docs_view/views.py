import os
import re
import markdown
import json
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Create your views here.

# 文档根目录
DOCS_ROOT = os.path.join(settings.BASE_DIR, 'docs')
DOCS_AT_ROOT = os.path.join(settings.BASE_DIR, '@docs')

# 选择存在的文档目录
if os.path.exists(DOCS_AT_ROOT):
    DOCS_ROOT = DOCS_AT_ROOT

# 支持的Markdown文件扩展名
MD_EXTENSIONS = ['.md', '.markdown']

# Markdown扩展设置
MARKDOWN_EXTENSIONS = [
    'markdown.extensions.fenced_code', 
    'markdown.extensions.tables',
    'markdown.extensions.toc',
    'markdown.extensions.codehilite',
    'markdown.extensions.nl2br',
]


def get_file_tree(root_dir):
    """
    递归生成文档目录树
    """
    tree = []
    try:
        items = sorted(os.listdir(root_dir))
        for item in items:
            full_path = os.path.join(root_dir, item)
            rel_path = os.path.relpath(full_path, DOCS_ROOT)
            
            # 忽略隐藏文件和非Markdown文件
            if item.startswith('.'):
                continue
                
            if os.path.isdir(full_path):
                children = get_file_tree(full_path)
                if children:  # 只添加非空目录
                    tree.append({
                        'name': item,
                        'path': rel_path.replace('\\', '/'),
                        'type': 'directory',
                        'children': children
                    })
            elif any(item.endswith(ext) for ext in MD_EXTENSIONS):
                tree.append({
                    'name': item,
                    'path': rel_path.replace('\\', '/'),
                    'type': 'file'
                })
    except Exception as e:
        print(f"Error getting file tree: {e}")
    
    return tree


def get_markdown_content(file_path):
    """
    读取并转换Markdown文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 处理文档中的内部链接
        def replace_internal_links(match):
            link_text = match.group(1)
            link_path = match.group(2)
            
            # 检查是否是内部链接
            if not (link_path.startswith('http://') or link_path.startswith('https://')) and link_path.endswith(tuple(MD_EXTENSIONS)):
                # 获取当前文件的目录
                current_dir = os.path.dirname(file_path)
                
                # 构建链接的目标路径
                target_path = os.path.normpath(os.path.join(current_dir, link_path))
                rel_path = os.path.relpath(target_path, DOCS_ROOT).replace('\\', '/')
                
                # 生成新的链接
                return f'[{link_text}](/doc/{rel_path})'
            
            return match.group(0)
        
        # 替换Markdown中的内部链接
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_internal_links, content)
        
        # 转换Markdown到HTML
        html = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS)
        return html
    except Exception as e:
        return f"<p>Error reading file: {e}</p>"


def doc_list_view(request):
    """
    显示文档列表页面
    """
    context = {
        'title': '文档列表'
    }
    return render(request, 'docs_view/doc_list.html', context)


def doc_view(request, doc_path):
    """
    显示单个文档页面
    """
    try:
        # 确保路径安全，防止目录遍历
        full_path = os.path.normpath(os.path.join(DOCS_ROOT, doc_path))
        if not full_path.startswith(DOCS_ROOT):
            raise Http404("文档不存在")
        
        if not os.path.exists(full_path):
            raise Http404("文档不存在")
        
        if os.path.isdir(full_path):
            # 如果是目录，找出目录下的第一个Markdown文件
            for item in sorted(os.listdir(full_path)):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path) and any(item.endswith(ext) for ext in MD_EXTENSIONS):
                    rel_path = os.path.relpath(item_path, DOCS_ROOT).replace('\\', '/')
                    return doc_view(request, rel_path)
            
            raise Http404("目录中没有Markdown文件")
        
        # 确保是Markdown文件
        if not any(full_path.endswith(ext) for ext in MD_EXTENSIONS):
            raise Http404("不是Markdown文件")
        
        # 获取文件内容
        content = get_markdown_content(full_path)
        
        context = {
            'title': os.path.basename(full_path),
            'content': mark_safe(content),
            'doc_path': doc_path
        }
        return render(request, 'docs_view/doc_view.html', context)
    except Http404:
        raise
    except Exception as e:
        context = {
            'title': '错误',
            'error': str(e)
        }
        return render(request, 'docs_view/error.html', context)


@cache_page(60 * 15)  # 缓存15分钟
def get_docs_tree(request):
    """
    API: 获取文档树结构
    """
    # 尝试从缓存中获取
    tree = cache.get('docs_tree')
    if not tree:
        tree = get_file_tree(DOCS_ROOT)
        # 保存到缓存
        cache.set('docs_tree', tree, 60 * 15)  # 15分钟缓存
    
    return JsonResponse({
        'success': True,
        'code': 2000,
        'message': '获取文档树成功',
        'data': {'tree': tree}
    })


def get_doc_content(request, doc_path):
    """
    API: 获取文档内容
    """
    try:
        # 确保路径安全，防止目录遍历
        full_path = os.path.normpath(os.path.join(DOCS_ROOT, doc_path))
        if not full_path.startswith(DOCS_ROOT):
            return JsonResponse({
                'success': False,
                'code': 4004,
                'message': '文档不存在',
                'data': None
            }, status=404)
        
        if not os.path.exists(full_path):
            return JsonResponse({
                'success': False,
                'code': 4004,
                'message': '文档不存在',
                'data': None
            }, status=404)
        
        if os.path.isdir(full_path):
            return JsonResponse({
                'success': False,
                'code': 4000,
                'message': '请求的路径是目录，不是文件',
                'data': None
            }, status=400)
        
        # 确保是Markdown文件
        if not any(full_path.endswith(ext) for ext in MD_EXTENSIONS):
            return JsonResponse({
                'success': False,
                'code': 4000,
                'message': '不是Markdown文件',
                'data': None
            }, status=400)
        
        # 获取文件内容
        content = get_markdown_content(full_path)
        
        return JsonResponse({
            'success': True,
            'code': 2000,
            'message': '获取文档内容成功',
            'data': {
                'title': os.path.basename(full_path),
                'content': content
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'code': 5000,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }, status=500)
