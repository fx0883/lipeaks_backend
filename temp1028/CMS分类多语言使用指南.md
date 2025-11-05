# CMS分类多语言使用指南

> **版本**: 1.0  
> **更新日期**: 2025-11-03  
> **适用范围**: 管理端 + 前端

---

## 📋 目录

1. [功能概述](#功能概述)
2. [管理后台使用](#管理后台使用)
3. [前端API调用](#前端api调用)
4. [常见场景](#常见场景)
5. [故障排查](#故障排查)

---

## 功能概述

### 支持的语言

| 语言代码 | 语言名称 | 说明 |
|---------|---------|------|
| `zh-hans` | 简体中文 | 默认语言，回退语言 |
| `en` | English | 英文 |
| `zh-hant` | 繁体中文 | 繁体中文 |

### 可翻译字段

分类模型中以下字段支持多语言：

- ✅ **name** - 分类名称
- ✅ **description** - 分类描述  
- ✅ **seo_title** - SEO标题
- ✅ **seo_description** - SEO描述

### 不可翻译字段（共享字段）

- ❌ **slug** - URL标识（全局唯一）
- ❌ **parent** - 父分类
- ❌ **cover_image** - 封面图
- ❌ **is_active** - 是否激活
- ❌ **is_pinned** - 是否置顶
- ❌ **sort_order** - 排序值

---

## 管理后台使用

### 1. 访问分类管理

登录Django Admin后台：

```
http://your-domain.com/admin/cms/category/
```

### 2. 创建多语言分类

#### 步骤：

1. 点击"Add Category"按钮
2. 在顶部看到语言切换标签：`简体中文 | English | 繁体中文`
3. 填写共享字段（slug、parent、cover_image等）
4. 切换到每个语言标签，填写对应语言的内容

#### 示例：创建"技术"分类

**共享信息**（只需填一次）：
- Slug: `tech`
- Sort order: `10`
- Is active: ✅
- Is pinned: ✅

**简体中文标签**：
- Name: `技术`
- Description: `技术相关的文章分类`
- SEO Title: `技术分类`
- SEO Description: `探索最新的技术资讯和教程`

**English标签**：
- Name: `Technology`
- Description: `Technology related articles`
- SEO Title: `Technology Category`
- SEO Description: `Explore the latest tech news`

**繁体中文标签**：
- Name: `技術`
- Description: `技術相關的文章分類`
- SEO Title: `技術分類`
- SEO Description: `探索最新的技術資訊和教程`

### 3. 编辑现有分类

1. 在列表页点击分类名称进入编辑页
2. 看到当前语言的内容
3. 点击语言标签切换到其他语言
4. 修改对应语言的字段
5. 点击"Save"保存所有语言的更改

### 4. 查看翻译状态

在列表页中：
- ✅ 绿色标记：该语言已翻译
- ⚠️ 黄色标记：该语言部分翻译
- ❌ 红色标记：该语言未翻译

### 5. 批量操作

Admin后台支持批量选择分类进行以下操作：
- 激活/停用
- 置顶/取消置顶
- 删除（如无子分类和文章关联）

**注意**：批量操作不会影响翻译内容。

---

## 前端API调用

### 1. 获取特定语言的分类列表

#### 请求示例（获取英文分类）：

```javascript
// JavaScript/TypeScript
const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
  headers: {
    'X-Tenant-ID': '1',
    'Accept-Language': 'en'  // 关键：指定语言
  }
});

const categories = await response.json();
console.log(categories[0].name);  // 输出: "Technology"
```

```python
# Python
import requests

response = requests.get(
    'http://your-domain.com/api/v1/cms/categories/',
    headers={
        'X-Tenant-ID': '1',
        'Accept-Language': 'en'
    }
)
categories = response.json()
print(categories[0]['name'])  # 输出: "Technology"
```

```swift
// Swift (iOS)
var request = URLRequest(url: URL(string: "http://your-domain.com/api/v1/cms/categories/")!)
request.addValue("1", forHTTPHeaderField: "X-Tenant-ID")
request.addValue("en", forHTTPHeaderField: "Accept-Language")

URLSession.shared.dataTask(with: request) { data, response, error in
    // 处理响应
}.resume()
```

#### 响应示例：

```json
[
  {
    "id": 1,
    "slug": "tech",
    "name": "Technology",  // 根据Accept-Language返回英文
    "description": "Technology related articles",
    "cover_image": "https://example.com/tech.jpg",
    "is_active": true,
    "translations": {  // 包含所有语言
      "zh-hans": {
        "name": "技术",
        "description": "技术相关的文章分类"
      },
      "en": {
        "name": "Technology",
        "description": "Technology related articles"
      }
    }
  }
]
```

### 2. 创建多语言分类

```javascript
const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'X-Tenant-ID': '1',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    slug: 'programming',
    translations: {
      'zh-hans': {
        name: '编程',
        description: '编程相关内容',
        seo_title: '编程教程',
        seo_description: '学习编程技术'
      },
      'en': {
        name: 'Programming',
        description: 'Programming related content',
        seo_title: 'Programming Tutorials',
        seo_description: 'Learn programming skills'
      },
      'zh-hant': {
        name: '編程',
        description: '編程相關內容',
        seo_title: '編程教程',
        seo_description: '學習編程技術'
      }
    },
    is_active: true,
    sort_order: 10
  })
});
```

### 3. 更新特定语言的翻译

```javascript
// 只更新英文翻译
const response = await fetch('http://your-domain.com/api/v1/cms/categories/1/', {
  method: 'PATCH',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'X-Tenant-ID': '1',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    translations: {
      'en': {
        name: 'Updated Tech Category',
        description: 'Updated description'
      }
    }
  })
});
```

### 4. 前端语言切换实现

#### Vue 3 示例：

```vue
<template>
  <div>
    <!-- 语言切换器 -->
    <select v-model="currentLanguage" @change="fetchCategories">
      <option value="zh-hans">简体中文</option>
      <option value="en">English</option>
      <option value="zh-hant">繁体中文</option>
    </select>

    <!-- 分类列表 -->
    <div v-for="category in categories" :key="category.id">
      <h3>{{ category.name }}</h3>
      <p>{{ category.description }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const currentLanguage = ref('zh-hans');
const categories = ref([]);

const fetchCategories = async () => {
  const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
    headers: {
      'X-Tenant-ID': '1',
      'Accept-Language': currentLanguage.value
    }
  });
  categories.value = await response.json();
};

onMounted(() => {
  fetchCategories();
});
</script>
```

#### React 示例：

```jsx
import React, { useState, useEffect } from 'react';

function CategoryList() {
  const [language, setLanguage] = useState('zh-hans');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchCategories();
  }, [language]);

  const fetchCategories = async () => {
    const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
      headers: {
        'X-Tenant-ID': '1',
        'Accept-Language': language
      }
    });
    const data = await response.json();
    setCategories(data);
  };

  return (
    <div>
      <select value={language} onChange={(e) => setLanguage(e.target.value)}>
        <option value="zh-hans">简体中文</option>
        <option value="en">English</option>
        <option value="zh-hant">繁体中文</option>
      </select>

      {categories.map(category => (
        <div key={category.id}>
          <h3>{category.name}</h3>
          <p>{category.description}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## 常见场景

### 场景1：网站支持中英文切换

**需求**：用户可以在网站顶部切换语言，分类名称随之改变。

**实现**：
1. 前端维护当前语言状态
2. 切换语言时更新`Accept-Language`请求头
3. 重新获取分类数据

```javascript
// 全局语言状态管理（Pinia/Vuex）
const languageStore = {
  state: {
    currentLang: 'zh-hans'
  },
  actions: {
    setLanguage(lang) {
      this.currentLang = lang;
      // 重新获取所有需要多语言的数据
      this.refreshAllData();
    }
  }
};
```

### 场景2：管理后台翻译工作流

**需求**：内容团队先创建中文内容，翻译团队后续添加英文翻译。

**步骤**：
1. 内容编辑创建分类，只填写简体中文
2. 保存后分类立即可用（显示中文）
3. 翻译团队进入编辑页，切换到English标签
4. 填写英文翻译并保存
5. 前端英文用户现在可以看到英文版本

### 场景3：渐进式多语言支持

**需求**：网站先上线中文版，后续逐步添加英文支持。

**实现**：
1. 初期只创建中文翻译
2. 所有API调用不设置`Accept-Language`或设为`zh-hans`
3. 准备上线英文版时：
   - 管理员补充英文翻译
   - 前端添加语言切换器
   - API调用根据用户选择设置`Accept-Language`

### 场景4：SEO优化

**需求**：不同语言的页面有不同的SEO设置。

**实现**：
1. 为每种语言填写专门的`seo_title`和`seo_description`
2. 前端根据当前语言从API获取对应SEO字段
3. 动态设置页面`<title>`和`<meta name="description">`

```javascript
// 前端SEO设置
const updateSEO = (category, language) => {
  document.title = category.seo_title || category.name;
  
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    metaDesc.setAttribute('content', category.seo_description || category.description);
  }
};
```

---

## 故障排查

### 问题1：获取分类时返回的name是null

**原因**：该分类在请求的语言中没有翻译。

**解决方案**：
1. 检查数据库中是否有对应语言的翻译记录
2. 在Admin后台补充翻译
3. 或者依赖回退机制（会显示简体中文）

### 问题2：创建分类时translations字段报错

**错误信息**：
```json
{
  "translations": ["This field is required"]
}
```

**原因**：创建分类时至少需要提供一种语言的翻译。

**解决方案**：
```javascript
// 至少提供默认语言
{
  translations: {
    'zh-hans': {
      name: '分类名称',
      description: '分类描述'
    }
  }
}
```

### 问题3：Admin后台看不到语言切换标签

**原因**：
1. django-parler未正确安装
2. CategoryAdmin未继承TranslatableAdmin

**检查步骤**：
```bash
# 1. 检查是否安装
pip list | grep parler

# 2. 检查settings.py
# 确保'parler'在INSTALLED_APPS中

# 3. 检查admin.py
# 确保CategoryAdmin继承TranslatableAdmin
```

### 问题4：某个语言的内容不显示

**排查步骤**：

1. 检查Accept-Language请求头是否正确
```bash
curl -H "Accept-Language: en" \
     -H "X-Tenant-ID: 1" \
     http://your-domain.com/api/v1/cms/categories/1/
```

2. 检查translations对象中是否有该语言的数据
```json
{
  "translations": {
    "zh-hans": {...},
    "en": null  // 英文翻译缺失
  }
}
```

3. 在Admin后台补充缺失的翻译

### 问题5：更新分类后某个语言的翻译消失了

**原因**：使用PUT方法时覆盖了整个translations对象。

**解决方案**：
- 使用PATCH方法只更新特定语言
- 或者PUT时包含所有语言的完整数据

```javascript
// ✅ 推荐：使用PATCH
fetch('/api/v1/cms/categories/1/', {
  method: 'PATCH',
  body: JSON.stringify({
    translations: {
      'en': { name: 'New Name' }  // 只更新英文
    }
  })
});

// ⚠️ 使用PUT需要包含所有语言
fetch('/api/v1/cms/categories/1/', {
  method: 'PUT',
  body: JSON.stringify({
    slug: 'tech',
    translations: {
      'zh-hans': {...},  // 必须包含
      'en': {...},       // 必须包含
      'zh-hant': {...}   // 必须包含
    },
    // 其他所有字段...
  })
});
```

---

## 数据库迁移注意事项

### 初次启用多语言

执行以下命令：

```bash
# 1. 安装依赖
pip install django-parler==2.3 django-parler-rest==2.2

# 2. 生成迁移
python manage.py makemigrations cms

# 3. 执行迁移
python manage.py migrate cms

# 4. （可选）为现有分类创建默认翻译
python manage.py shell
```

```python
# 在Django shell中
from cms.models import Category
from django.conf import settings

# 为所有现有分类创建简体中文翻译
for category in Category.objects.all():
    category.set_current_language('zh-hans')
    # name, description等字段会自动迁移
    category.save()
```

---

## 技术支持

### 相关文档

- [分类管理API文档](./分类管理API.md)
- [Django Parler官方文档](https://django-parler.readthedocs.io/)
- [Django Parler REST文档](https://github.com/django-parler/django-parler-rest)

### 常见问题

如遇到问题，请按以下顺序排查：
1. 检查本文档的"故障排查"部分
2. 查看Django日志输出
3. 使用浏览器开发者工具检查API请求和响应
4. 联系后端团队

---

**文档维护**: Backend Development Team  
**最后更新**: 2025-11-03

