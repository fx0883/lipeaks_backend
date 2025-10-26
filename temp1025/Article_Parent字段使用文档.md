# Article Parent 字段使用文档

## 📋 需求说明

为 CMS 模块的 Article 模型添加 `parent` 字段，用于存储父文章的 ID，实现文章的层级结构。

**应用场景**：
- 📚 系列文章（如：Python教程 → 第1章、第2章、第3章）
- 📖 章节文章（如：产品手册 → 安装指南 → 环境准备）
- 🏷️ 子文章分类（如：技术博客 → 前端开发 → React 专题）
- 📝 翻译版本（如：原文 → 中文翻译、英文翻译）

---

## ✅ 已完成的修改

### 1. 数据库字段添加

**文件**：`cms/models.py`

**位置**：第41-51行

**新增字段**：
```python
# 父文章关联（自关联，用于实现文章层级结构）
parent = models.ForeignKey(
    'self',
    on_delete=models.CASCADE,
    related_name="children",
    verbose_name=_("父文章"),
    blank=True,
    null=True,
    db_index=True,
    help_text="上级文章，用于创建文章层级结构（如系列文章、章节等）"
)
```

**字段特性**：
- ✅ 自关联外键（指向 Article 自身）
- ✅ 允许为空（`blank=True, null=True`）
- ✅ 级联删除（`on_delete=models.CASCADE`）
- ✅ 反向关系名：`children`（访问子文章）
- ✅ 自动索引（`db_index=True`）

### 2. 数据库索引优化

**位置**：第83-90行

**新增索引**：
```python
indexes = [
    # ... 原有索引
    models.Index(fields=['parent']),  # 父文章索引
    models.Index(fields=['tenant', 'parent']),  # 租户+父文章组合索引
]
```

**索引作用**：
- ✅ 加速根据 parent_id 查询子文章
- ✅ 加速在租户范围内查询文章层级

### 3. 辅助方法

**位置**：第118-170行

**新增方法**：

#### a) `get_ancestors()` - 获取祖先文章
```python
def get_ancestors(self):
    """
    获取所有祖先文章（从当前文章向上追溯到根文章）
    返回：[父文章, 祖父文章, ..., 根文章]
    """
```

**示例**：
```python
article = Article.objects.get(id=5)
ancestors = article.get_ancestors()
# 返回：[第1章, Python教程]（从近到远）
```

#### b) `get_root()` - 获取根文章
```python
def get_root(self):
    """
    获取根文章（最顶层的文章）
    如果没有父文章，返回自己
    """
```

**示例**：
```python
article = Article.objects.get(id=5)  # 第1章 → 第1节
root = article.get_root()
# 返回：Python教程（根文章）
```

#### c) `get_depth()` - 获取层级深度
```python
def get_depth(self):
    """
    获取文章在层级树中的深度
    根文章深度为 0，子文章深度为 1，以此类推
    """
```

**示例**：
```python
root_article.get_depth()  # 返回 0
chapter1.get_depth()      # 返回 1
section1_1.get_depth()    # 返回 2
```

#### d) `is_root()` - 判断是否为根文章
```python
def is_root(self):
    """判断是否为根文章（没有父文章）"""
    return self.parent is None
```

#### e) `is_leaf()` - 判断是否为叶子文章
```python
def is_leaf(self):
    """判断是否为叶子文章（没有子文章）"""
    return not self.children.exists()
```

#### f) `get_siblings()` - 获取兄弟文章
```python
def get_siblings(self, include_self=False):
    """
    获取兄弟文章（同一父文章下的其他文章）
    """
```

**示例**：
```python
chapter1 = Article.objects.get(id=2)
siblings = chapter1.get_siblings()
# 返回：[第2章, 第3章, 第4章]（不包括自己）
```

### 4. 循环引用保护

**位置**：第105-107行

**保护机制**：
```python
# 防止循环引用：不能将自己设置为父文章
if self.parent and self.parent.id == self.id:
    raise ValueError(_("文章不能将自己设置为父文章"))
```

**保护场景**：
- ❌ 文章 A 的 parent = 文章 A（自己引用自己）
- ❌ 文章 A → 文章 B → 文章 A（循环引用）

### 5. 数据库迁移

**迁移文件**：`cms/migrations/0003_add_article_parent_field.py`

**包含操作**：
- ✅ 添加 parent 字段到 Article 表
- ✅ 创建 parent 字段索引
- ✅ 创建 (tenant, parent) 组合索引

**迁移状态**：✅ 已成功应用到数据库

---

## 🎯 使用场景和示例

### 场景1：创建系列文章

**步骤1：创建根文章（系列主文章）**
```python
from cms.models import Article

# 创建系列主文章
series = Article.objects.create(
    title="Python 从入门到精通",
    content="本系列将带你学习 Python 编程...",
    author=user,
    tenant=tenant,
    status='published',
    parent=None  # ✅ 根文章，没有父文章
)
```

**步骤2：创建子文章（章节）**
```python
# 创建第1章
chapter1 = Article.objects.create(
    title="第1章：Python 基础",
    content="本章介绍 Python 基础知识...",
    author=user,
    tenant=tenant,
    status='published',
    parent=series  # ✅ 父文章是系列主文章
)

# 创建第2章
chapter2 = Article.objects.create(
    title="第2章：数据类型",
    content="本章介绍 Python 数据类型...",
    author=user,
    tenant=tenant,
    status='published',
    parent=series
)
```

**步骤3：创建子章节**
```python
# 在第1章下创建小节
section1_1 = Article.objects.create(
    title="1.1 变量和常量",
    content="变量的定义和使用...",
    author=user,
    tenant=tenant,
    status='published',
    parent=chapter1  # ✅ 父文章是第1章
)
```

### 场景2：查询文章层级

**获取某文章的所有子文章**：
```python
series = Article.objects.get(id=1)
children = series.children.all()  # ✅ 使用 related_name='children'
# 返回：[第1章, 第2章, 第3章, ...]
```

**获取某文章的父文章**：
```python
chapter1 = Article.objects.get(id=2)
parent = chapter1.parent  # ✅ 直接访问 parent 字段
# 返回：Python 从入门到精通
```

**获取文章的完整路径**：
```python
section = Article.objects.get(id=5)
ancestors = section.get_ancestors()
# 返回：[第1章, Python教程]

# 构建完整路径
path = [a.title for a in reversed(ancestors)] + [section.title]
# 结果：['Python教程', '第1章', '1.1 变量和常量']
```

**获取同级文章（兄弟节点）**：
```python
chapter1 = Article.objects.get(id=2)
siblings = chapter1.get_siblings()
# 返回：[第2章, 第3章, ...]（不包括自己）
```

### 场景3：过滤查询

**查询所有根文章**：
```python
root_articles = Article.objects.filter(parent__isnull=True, tenant=tenant)
# 返回所有没有父文章的文章
```

**查询某文章的所有子文章（直接子级）**：
```python
parent_id = 1
children = Article.objects.filter(parent_id=parent_id, tenant=tenant)
```

**查询某文章的所有子孙文章（递归）**：
```python
def get_all_descendants(article):
    """递归获取所有子孙文章"""
    descendants = []
    for child in article.children.all():
        descendants.append(child)
        descendants.extend(get_all_descendants(child))
    return descendants

series = Article.objects.get(id=1)
all_descendants = get_all_descendants(series)
# 返回：所有章节、小节、子小节...
```

---

## 🔧 API 集成建议

### 1. 序列化器更新建议

在 `cms/serializers.py` 中添加 parent 字段：

```python
class ArticleSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(
        required=False, 
        allow_null=True,
        help_text="父文章ID"
    )
    parent_title = serializers.CharField(
        source='parent.title',
        read_only=True,
        help_text="父文章标题"
    )
    children_count = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            # ... 原有字段
            'parent_id',
            'parent_title',
            'children_count',
            'depth',
        ]
    
    def get_children_count(self, obj):
        """获取子文章数量"""
        return obj.children.count()
    
    def get_depth(self, obj):
        """获取层级深度"""
        return obj.get_depth()
```

### 2. 视图过滤建议

在视图中添加 parent 过滤：

```python
class ArticleListView(APIView):
    def get(self, request):
        queryset = Article.objects.filter(tenant=request.tenant)
        
        # 根据 parent_id 过滤
        parent_id = request.query_params.get('parent_id')
        if parent_id == 'null' or parent_id == '':
            # 只获取根文章
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            # 获取指定父文章的子文章
            queryset = queryset.filter(parent_id=parent_id)
        
        # ...
```

### 3. API 调用示例

**获取所有根文章**：
```bash
GET /api/v1/cms/articles/?parent_id=null
```

**获取指定文章的子文章**：
```bash
GET /api/v1/cms/articles/?parent_id=1
```

**创建子文章**：
```bash
POST /api/v1/cms/articles/
{
  "title": "第1章：基础知识",
  "content": "...",
  "parent_id": 1,  // ✅ 指定父文章ID
  "author": 1,
  "tenant": 1
}
```

**获取文章详情（包含父子关系）**：
```bash
GET /api/v1/cms/articles/5/
```

**响应示例**：
```json
{
  "id": 5,
  "title": "1.1 变量和常量",
  "parent_id": 2,
  "parent_title": "第1章：Python基础",
  "children_count": 3,
  "depth": 2,
  "ancestors": [
    {"id": 2, "title": "第1章：Python基础"},
    {"id": 1, "title": "Python从入门到精通"}
  ]
}
```

---

## 🏗️ 数据结构示例

### 示例：Python 教程系列

```
Python从入门到精通 (id=1, parent=null, depth=0) 📚 根文章
├── 第1章：Python基础 (id=2, parent=1, depth=1)
│   ├── 1.1 变量和常量 (id=5, parent=2, depth=2)
│   ├── 1.2 数据类型 (id=6, parent=2, depth=2)
│   └── 1.3 运算符 (id=7, parent=2, depth=2)
├── 第2章：控制流程 (id=3, parent=1, depth=1)
│   ├── 2.1 条件语句 (id=8, parent=3, depth=2)
│   └── 2.2 循环语句 (id=9, parent=3, depth=2)
└── 第3章：函数 (id=4, parent=1, depth=1)
    ├── 3.1 函数定义 (id=10, parent=4, depth=2)
    └── 3.2 参数传递 (id=11, parent=4, depth=2)
```

**数据库中的存储**：
```
| id | title              | parent_id |
|----|-------------------|-----------|
| 1  | Python从入门到精通  | NULL      |
| 2  | 第1章：Python基础   | 1         |
| 3  | 第2章：控制流程     | 1         |
| 4  | 第3章：函数        | 1         |
| 5  | 1.1 变量和常量     | 2         |
| 6  | 1.2 数据类型       | 2         |
| 7  | 1.3 运算符         | 2         |
```

---

## 🛠️ 辅助方法使用示例

### 1. 获取祖先链

```python
section = Article.objects.get(id=5)  # 1.1 变量和常量

ancestors = section.get_ancestors()
# 返回：[<Article: 第1章>, <Article: Python教程>]

# 构建面包屑导航
breadcrumb = ' > '.join([a.title for a in reversed(ancestors)] + [section.title])
# 结果："Python教程 > 第1章 > 1.1 变量和常量"
```

### 2. 获取根文章

```python
section = Article.objects.get(id=5)
root = section.get_root()
# 返回：<Article: Python教程>

# 获取系列信息
print(f"本文属于系列：{root.title}")
```

### 3. 获取层级深度

```python
root = Article.objects.get(id=1)
chapter = Article.objects.get(id=2)
section = Article.objects.get(id=5)

print(root.get_depth())     # 输出：0
print(chapter.get_depth())  # 输出：1
print(section.get_depth())  # 输出：2
```

### 4. 判断文章类型

```python
article = Article.objects.get(id=1)

if article.is_root():
    print("这是系列主文章")

if article.is_leaf():
    print("这是叶子文章（没有子章节）")
```

### 5. 获取兄弟文章

```python
chapter1 = Article.objects.get(id=2)  # 第1章

# 获取其他章节（不包括自己）
siblings = chapter1.get_siblings()
# 返回：[第2章, 第3章]

# 包括自己
siblings_with_self = chapter1.get_siblings(include_self=True)
# 返回：[第1章, 第2章, 第3章]
```

### 6. 获取子文章

```python
series = Article.objects.get(id=1)

# 直接子文章
children = series.children.all()
# 返回：[第1章, 第2章, 第3章]

# 已发布的子文章
published_children = series.children.filter(status='published')

# 子文章数量
children_count = series.children.count()
```

---

## 📊 查询优化建议

### 1. 使用 select_related 优化父文章查询

```python
# ✅ 优化：一次查询同时获取文章和父文章
articles = Article.objects.select_related('parent').filter(tenant=tenant)

for article in articles:
    if article.parent:
        print(f"{article.title} <- {article.parent.title}")  # 不会触发额外查询
```

### 2. 使用 prefetch_related 优化子文章查询

```python
# ✅ 优化：一次查询同时获取所有子文章
articles = Article.objects.prefetch_related('children').filter(parent__isnull=True)

for article in articles:
    print(f"{article.title} 有 {article.children.count()} 个子文章")  # 不会触发额外查询
```

### 3. 树形查询示例

```python
# 获取完整的文章树（限制深度避免性能问题）
def get_article_tree(root_article, max_depth=3):
    """递归获取文章树"""
    def build_tree(article, current_depth=0):
        tree_node = {
            'id': article.id,
            'title': article.title,
            'depth': current_depth,
            'children': []
        }
        
        if current_depth < max_depth:
            for child in article.children.filter(status='published'):
                tree_node['children'].append(build_tree(child, current_depth + 1))
        
        return tree_node
    
    return build_tree(root_article)

# 使用示例
series = Article.objects.get(id=1)
tree = get_article_tree(series, max_depth=2)
```

---

## ⚠️ 重要注意事项

### 1. 循环引用检测

**问题**：
```python
# ❌ 危险：可能造成循环引用
article_a.parent = article_b
article_a.save()

article_b.parent = article_a
article_b.save()  # 会导致循环：A → B → A → B → ...
```

**保护机制**：
- ✅ `save()` 方法中检测自己引用自己
- ✅ `get_ancestors()` 方法中检测循环链

**建议**：
- 在更新 parent 时进行额外验证
- 使用管理后台时注意检查
- 可以添加 clean() 方法进行更严格的验证

### 2. 删除行为

**当前设置**：`on_delete=models.CASCADE`

**影响**：
```python
series = Article.objects.get(id=1)
series.delete()  # ❌ 会删除所有子文章（级联删除）
```

**如果需要保留子文章**，可以修改为：
```python
parent = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,  # 删除父文章时，子文章的parent设为NULL
    ...
)
```

### 3. 性能考虑

**深度查询**：
- ⚠️ `get_ancestors()` 需要递归查询，深度过大时性能下降
- 建议限制文章层级深度（如最多3-4层）

**树形结构**：
- ⚠️ 递归获取所有子孙文章时注意限制深度
- 使用缓存优化频繁访问的文章树

---

## 📈 数据库变更详情

### 新增字段

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `parent_id` | INTEGER | NULL | NULL | 父文章ID |

### 新增索引

| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| `cms_article_parent__66bf81_idx` | `parent_id` | 单列索引 | 加速按父文章查询 |
| `cms_article_tenant__c7a433_idx` | `tenant_id, parent_id` | 组合索引 | 租户范围内的层级查询 |

### 外键约束

```sql
ALTER TABLE cms_article 
ADD CONSTRAINT cms_article_parent_id_fk 
FOREIGN KEY (parent_id) REFERENCES cms_article(id) 
ON DELETE CASCADE;
```

---

## 🎉 完成状态

### ✅ 已完成

- [x] 添加 parent 字段到 Article 模型
- [x] 添加数据库索引优化
- [x] 添加 6 个辅助方法
- [x] 添加循环引用保护
- [x] 创建数据库迁移
- [x] 应用迁移到数据库
- [x] 创建使用文档

### 📊 修改统计

- **修改文件**：1个 (`cms/models.py`)
- **新增字段**：1个 (`parent`)
- **新增方法**：6个
- **新增索引**：2个
- **迁移文件**：1个

---

## 🚀 后续建议

### 1. 序列化器更新

建议在 `cms/serializers.py` 中添加 parent 相关字段：
- `parent_id` - 父文章ID
- `parent_title` - 父文章标题
- `children` - 子文章列表
- `children_count` - 子文章数量
- `depth` - 层级深度
- `breadcrumb` - 面包屑路径

### 2. Admin 管理后台更新

建议在 `cms/admin.py` 中添加：
- 在列表页显示层级结构（缩进显示）
- 添加 parent 字段到表单
- 添加子文章内联显示

### 3. 前端展示建议

**树形导航**：
```javascript
// 获取根文章
GET /api/v1/cms/articles/?parent_id=null

// 展开某个文章的子文章
GET /api/v1/cms/articles/?parent_id=1
```

**面包屑导航**：
```javascript
// 从文章详情中获取 ancestors
const breadcrumb = [...ancestors.reverse(), current_article]
  .map(a => a.title)
  .join(' > ')
```

---

**✅ Article parent 字段添加完成！现在可以实现文章的层级结构（系列文章、章节等功能）。** 🎊

