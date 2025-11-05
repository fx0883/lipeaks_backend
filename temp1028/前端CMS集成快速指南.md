# 前端CMS集成快速指南

> **版本**: 1.0  
> **更新日期**: 2025-11-03  
> **适用对象**: 前端开发者（Web/iOS/Android）

---

## 🎯 本文档目标

帮助前端开发者快速集成以下新功能：
1. ✅ CMS文章管理（含层级结构）
2. ✅ 分类管理（含多语言）
3. ✅ 语言切换功能
4. ✅ 系列文章导航

**预计阅读时间**: 15分钟  
**预计集成时间**: 2-4小时

---

## 📋 前置要求

在开始前，确保你已经：
- ✅ 完成基础认证集成（登录、Token管理）
- ✅ 配置了HTTP客户端（能自动添加X-Tenant-ID和Authorization头）
- ✅ 了解项目的基本API调用方式

如未完成，请先阅读：[04_通用集成指南.md](./04_通用集成指南.md)

---

## 🚀 5分钟快速开始

### 步骤1：获取分类列表（中文）

```javascript
const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
  headers: {
    'X-Tenant-ID': '1',
    'Accept-Language': 'zh-hans'  // 获取中文分类
  }
});

const categories = await response.json();
console.log(categories);
// [{ id: 1, name: "技术", slug: "tech", ... }]
```

### 步骤2：获取文章列表

```javascript
const response = await fetch('http://your-domain.com/api/v1/cms/articles/?status=published', {
  headers: {
    'X-Tenant-ID': '1'
  }
});

const articles = await response.json();
console.log(articles.results);
// [{ id: 1, title: "文章标题", excerpt: "摘要", ... }]
```

### 步骤3：按分类过滤文章

```javascript
const categoryId = 14;
const response = await fetch(
  `http://your-domain.com/api/v1/cms/articles/?status=published&category_id=${categoryId}`,
  {
    headers: { 'X-Tenant-ID': '1' }
  }
);

const articles = await response.json();
// 返回该分类下的所有已发布文章
```

### 步骤4：切换语言

```javascript
// 用户选择英文
const language = 'en';

// 重新获取分类（英文）
const response = await fetch('http://your-domain.com/api/v1/cms/categories/', {
  headers: {
    'X-Tenant-ID': '1',
    'Accept-Language': language  // 改为'en'
  }
});

const categories = await response.json();
console.log(categories);
// [{ id: 1, name: "Technology", slug: "tech", ... }]
```

✅ **恭喜！基础集成完成！**

---

## 📱 完整功能集成

### 功能1：多语言博客首页

#### 需求
- 显示分类导航（支持中英文切换）
- 显示文章列表
- 用户可切换语言

#### 实现（Vue 3）

```vue
<template>
  <div class="blog-home">
    <!-- 语言切换器 -->
    <div class="language-switcher">
      <button 
        v-for="lang in languages" 
        :key="lang.code"
        :class="{ active: currentLang === lang.code }"
        @click="switchLanguage(lang.code)"
      >
        {{ lang.label }}
      </button>
    </div>

    <!-- 分类导航 -->
    <nav class="category-nav">
      <a 
        v-for="cat in categories" 
        :key="cat.id"
        @click="selectCategory(cat.id)"
        :class="{ active: selectedCategoryId === cat.id }"
      >
        {{ cat.name }}
      </a>
    </nav>

    <!-- 文章列表 -->
    <div class="articles">
      <article v-for="article in articles" :key="article.id">
        <h2>{{ article.title }}</h2>
        <p>{{ article.excerpt }}</p>
        <div class="meta">
          <span v-for="cat in article.categories" :key="cat.id">
            {{ cat.name }}
          </span>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const languages = [
  { code: 'zh-hans', label: '简体中文' },
  { code: 'en', label: 'English' },
  { code: 'zh-hant', label: '繁體中文' },
  { code: 'ja', label: '日本語' },
  { code: 'ko', label: '한국어' },
  { code: 'fr', label: 'Français' }
];

const currentLang = ref('zh-hans');
const categories = ref([]);
const articles = ref([]);
const selectedCategoryId = ref(null);

// 切换语言
const switchLanguage = async (lang) => {
  currentLang.value = lang;
  await Promise.all([
    loadCategories(),
    loadArticles()
  ]);
};

// 加载分类
const loadCategories = async () => {
  const res = await fetch('/api/v1/cms/categories/', {
    headers: {
      'X-Tenant-ID': '1',
      'Accept-Language': currentLang.value
    }
  });
  categories.value = await res.json();
};

// 加载文章
const loadArticles = async () => {
  let url = '/api/v1/cms/articles/?status=published';
  if (selectedCategoryId.value) {
    url += `&category_id=${selectedCategoryId.value}`;
  }
  
  const res = await fetch(url, {
    headers: { 'X-Tenant-ID': '1' }
  });
  const data = await res.json();
  articles.value = data.results;
};

// 选择分类
const selectCategory = (id) => {
  selectedCategoryId.value = id;
  loadArticles();
};

onMounted(() => {
  loadCategories();
  loadArticles();
});
</script>
```

#### 实现（React）

```jsx
import React, { useState, useEffect } from 'react';

function BlogHome() {
  const [currentLang, setCurrentLang] = useState('zh-hans');
  const [categories, setCategories] = useState([]);
  const [articles, setArticles] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  const languages = [
    { code: 'zh-hans', label: '简体中文' },
    { code: 'en', label: 'English' },
    { code: 'zh-hant', label: '繁體中文' }
  ];

  // 加载分类
  const loadCategories = async () => {
    const res = await fetch('/api/v1/cms/categories/', {
      headers: {
        'X-Tenant-ID': '1',
        'Accept-Language': currentLang
      }
    });
    const data = await res.json();
    setCategories(data);
  };

  // 加载文章
  const loadArticles = async () => {
    let url = '/api/v1/cms/articles/?status=published';
    if (selectedCategoryId) {
      url += `&category_id=${selectedCategoryId}`;
    }
    
    const res = await fetch(url, {
      headers: { 'X-Tenant-ID': '1' }
    });
    const data = await res.json();
    setArticles(data.results);
  };

  // 切换语言
  const switchLanguage = (lang) => {
    setCurrentLang(lang);
  };

  useEffect(() => {
    loadCategories();
  }, [currentLang]);

  useEffect(() => {
    loadArticles();
  }, [selectedCategoryId]);

  return (
    <div className="blog-home">
      {/* 语言切换器 */}
      <div className="language-switcher">
        {languages.map(lang => (
          <button
            key={lang.code}
            className={currentLang === lang.code ? 'active' : ''}
            onClick={() => switchLanguage(lang.code)}
          >
            {lang.label}
          </button>
        ))}
      </div>

      {/* 分类导航 */}
      <nav className="category-nav">
        {categories.map(cat => (
          <a
            key={cat.id}
            className={selectedCategoryId === cat.id ? 'active' : ''}
            onClick={() => setSelectedCategoryId(cat.id)}
          >
            {cat.name}
          </a>
        ))}
      </nav>

      {/* 文章列表 */}
      <div className="articles">
        {articles.map(article => (
          <article key={article.id}>
            <h2>{article.title}</h2>
            <p>{article.excerpt}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export default BlogHome;
```

---

### 功能2：系列文章导航

#### 需求
- 显示面包屑导航
- 显示子文章列表
- 支持层级跳转

#### 实现示例

```javascript
// 1. 获取文章详情（包含层级信息）
const getArticleDetail = async (articleId) => {
  const res = await fetch(`/api/v1/cms/articles/${articleId}/`, {
    headers: { 'X-Tenant-ID': '1' }
  });
  const article = await res.json();
  
  return {
    ...article,
    // breadcrumb: [{ id: 1, title: "系列名", slug: "..." }, ...]
    // children: [{ id: 2, title: "第1章", ... }, ...]
    // parent_info: { id: 0, title: "父文章", slug: "..." }
  };
};

// 2. 渲染面包屑
const renderBreadcrumb = (breadcrumb) => {
  return breadcrumb.map(item => 
    `<a href="/articles/${item.slug}">${item.title}</a>`
  ).join(' > ');
};

// 3. 渲染子文章导航
const renderChildren = (children) => {
  return children.map(child => `
    <div class="child-article">
      <a href="/articles/${child.slug}">${child.title}</a>
      <p>${child.excerpt}</p>
    </div>
  `).join('');
};

// 4. 获取同一系列的其他文章
const getSiblingArticles = async (parentId) => {
  const res = await fetch(
    `/api/v1/cms/articles/?parent_id=${parentId}&status=published`,
    { headers: { 'X-Tenant-ID': '1' } }
  );
  const data = await res.json();
  return data.results;
};
```

#### 完整页面示例（Vue 3）

```vue
<template>
  <div class="article-detail">
    <!-- 面包屑导航 -->
    <nav class="breadcrumb">
      <a 
        v-for="(item, index) in article.breadcrumb" 
        :key="item.id"
        @click="gotoArticle(item.slug)"
      >
        {{ item.title }}
        <span v-if="index < article.breadcrumb.length - 1"> > </span>
      </a>
    </nav>

    <!-- 文章内容 -->
    <article>
      <h1>{{ article.title }}</h1>
      <div v-html="article.content"></div>
    </article>

    <!-- 如果有子文章，显示目录 -->
    <div v-if="article.children_count > 0" class="toc">
      <h3>本系列文章</h3>
      <ul>
        <li v-for="child in article.children" :key="child.id">
          <a @click="gotoArticle(child.slug)">{{ child.title }}</a>
        </li>
      </ul>
    </div>

    <!-- 上一篇/下一篇 -->
    <div class="navigation" v-if="article.parent">
      <button @click="loadSiblings">查看本系列所有文章</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const article = ref({});

const loadArticle = async () => {
  const res = await fetch(`/api/v1/cms/articles/${route.params.id}/`, {
    headers: { 'X-Tenant-ID': '1' }
  });
  article.value = await res.json();
};

const gotoArticle = (slug) => {
  router.push(`/articles/${slug}`);
};

const loadSiblings = async () => {
  if (!article.value.parent) return;
  
  const res = await fetch(
    `/api/v1/cms/articles/?parent_id=${article.value.parent}`,
    { headers: { 'X-Tenant-ID': '1' } }
  );
  const data = await res.json();
  // 显示同级文章列表
};

onMounted(loadArticle);
</script>
```

---

### 功能3：管理后台翻译界面（Web）

#### 需求
- 管理员可以编辑多语言内容
- 显示所有语言的翻译状态
- 支持创建和更新翻译

#### 实现示例

```vue
<template>
  <div class="category-editor">
    <!-- 语言标签 -->
    <div class="language-tabs">
      <button
        v-for="lang in languages"
        :key="lang.code"
        :class="{ active: currentLang === lang.code }"
        @click="currentLang = lang.code"
      >
        {{ lang.label }}
        <span v-if="hasTranslation(lang.code)" class="badge">✓</span>
      </button>
    </div>

    <!-- 共享字段（所有语言通用） -->
    <div class="shared-fields">
      <h3>共享信息</h3>
      <input v-model="category.slug" placeholder="Slug" />
      <input v-model="category.sort_order" type="number" placeholder="排序" />
      <label>
        <input type="checkbox" v-model="category.is_active" />
        激活
      </label>
    </div>

    <!-- 当前语言的翻译字段 -->
    <div class="translation-fields">
      <h3>{{ getCurrentLanguageName() }} 翻译</h3>
      <input 
        v-model="category.translations[currentLang].name"
        placeholder="分类名称"
      />
      <textarea 
        v-model="category.translations[currentLang].description"
        placeholder="分类描述"
      ></textarea>
      <input 
        v-model="category.translations[currentLang].seo_title"
        placeholder="SEO标题"
      />
      <textarea 
        v-model="category.translations[currentLang].seo_description"
        placeholder="SEO描述"
      ></textarea>
    </div>

    <!-- 保存按钮 -->
    <button @click="saveCategory">保存所有语言</button>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';

const languages = [
  { code: 'zh-hans', label: '简体中文' },
  { code: 'en', label: 'English' },
  { code: 'zh-hant', label: '繁體中文' },
  { code: 'ja', label: '日本語' },
  { code: 'ko', label: '한국어' },
  { code: 'fr', label: 'Français' }
];

const currentLang = ref('zh-hans');

const category = reactive({
  slug: '',
  sort_order: 0,
  is_active: true,
  translations: {
    'zh-hans': { name: '', description: '', seo_title: '', seo_description: '' },
    'en': { name: '', description: '', seo_title: '', seo_description: '' },
    'zh-hant': { name: '', description: '', seo_title: '', seo_description: '' }
  }
});

const hasTranslation = (langCode) => {
  const trans = category.translations[langCode];
  return trans && trans.name && trans.name.trim() !== '';
};

const getCurrentLanguageName = () => {
  return languages.find(l => l.code === currentLang.value)?.label;
};

const saveCategory = async () => {
  const response = await fetch('/api/v1/cms/categories/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'X-Tenant-ID': '1',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(category)
  });
  
  if (response.ok) {
    alert('保存成功！');
  } else {
    const error = await response.json();
    alert('保存失败：' + JSON.stringify(error));
  }
};
</script>
```

---

## 🌐 多语言集成详解

### 1. HTTP客户端配置

#### Axios配置（推荐）

```javascript
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://your-domain.com/api/v1',
  headers: {
    'X-Tenant-ID': '1'
  }
});

// 添加语言拦截器
api.interceptors.request.use(config => {
  // 从store或localStorage获取当前语言
  const currentLanguage = localStorage.getItem('language') || 'zh-hans';
  config.headers['Accept-Language'] = currentLanguage;
  return config;
});

// 使用示例
const categories = await api.get('/cms/categories/');
// 自动带上Accept-Language头
```

#### Fetch封装

```javascript
// utils/api.js
export const apiRequest = async (url, options = {}) => {
  const currentLanguage = localStorage.getItem('language') || 'zh-hans';
  
  const defaultHeaders = {
    'X-Tenant-ID': '1',
    'Accept-Language': currentLanguage,
    ...options.headers
  };
  
  const response = await fetch(`http://your-domain.com/api/v1${url}`, {
    ...options,
    headers: defaultHeaders
  });
  
  return response.json();
};

// 使用
const categories = await apiRequest('/cms/categories/');
```

### 2. 语言状态管理

#### Pinia Store（Vue）

```javascript
// stores/language.js
import { defineStore } from 'pinia';

export const useLanguageStore = defineStore('language', {
  state: () => ({
    currentLanguage: localStorage.getItem('language') || 'zh-hans',
    supportedLanguages: [
      { code: 'zh-hans', label: '简体中文', shortLabel: '简' },
      { code: 'en', label: 'English', shortLabel: 'EN' },
      { code: 'zh-hant', label: '繁體中文', shortLabel: '繁' }
    ]
  }),
  
  actions: {
    setLanguage(langCode) {
      this.currentLanguage = langCode;
      localStorage.setItem('language', langCode);
      // 触发全局数据刷新
      window.dispatchEvent(new Event('language-changed'));
    },
    
    getLanguageLabel(code) {
      return this.supportedLanguages.find(l => l.code === code)?.label;
    }
  }
});

// 使用
import { useLanguageStore } from '@/stores/language';
const langStore = useLanguageStore();
langStore.setLanguage('en');
```

#### Redux Store（React）

```javascript
// languageSlice.js
import { createSlice } from '@reduxjs/toolkit';

const languageSlice = createSlice({
  name: 'language',
  initialState: {
    current: localStorage.getItem('language') || 'zh-hans',
    supported: [
      { code: 'zh-hans', label: '简体中文' },
      { code: 'en', label: 'English' },
      { code: 'zh-hant', label: '繁體中文' }
    ]
  },
  reducers: {
    setLanguage: (state, action) => {
      state.current = action.payload;
      localStorage.setItem('language', action.payload);
    }
  }
});

export const { setLanguage } = languageSlice.actions;
export default languageSlice.reducer;
```

### 3. iOS集成（Swift）

```swift
// LanguageManager.swift
class LanguageManager {
    static let shared = LanguageManager()
    
    private let supportedLanguages = [
        ("zh-hans", "简体中文"),
        ("en", "English"),
        ("zh-hant", "繁體中文")
    ]
    
    var currentLanguage: String {
        get {
            UserDefaults.standard.string(forKey: "app_language") ?? "zh-hans"
        }
        set {
            UserDefaults.standard.set(newValue, forKey: "app_language")
            NotificationCenter.default.post(name: .languageChanged, object: nil)
        }
    }
    
    func fetchCategories() async throws -> [Category] {
        var request = URLRequest(url: URL(string: "http://your-domain.com/api/v1/cms/categories/")!)
        request.addValue("1", forHTTPHeaderField: "X-Tenant-ID")
        request.addValue(currentLanguage, forHTTPHeaderField: "Accept-Language")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode([Category].self, from: data)
    }
}

// 使用
let categories = try await LanguageManager.shared.fetchCategories()
```

---

## 🔥 高级功能

### 1. 智能语言检测

```javascript
// 自动检测用户浏览器语言
const detectUserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage;
  
  // 浏览器语言映射
  const langMap = {
    'zh-CN': 'zh-hans',
    'zh-SG': 'zh-hans',
    'zh-TW': 'zh-hant',
    'zh-HK': 'zh-hant',
    'en': 'en',
    'en-US': 'en',
    'en-GB': 'en'
  };
  
  return langMap[browserLang] || 'zh-hans';
};

// 初始化时自动设置语言
const initLanguage = () => {
  const savedLang = localStorage.getItem('language');
  if (!savedLang) {
    const detectedLang = detectUserLanguage();
    localStorage.setItem('language', detectedLang);
    return detectedLang;
  }
  return savedLang;
};
```

### 2. 翻译缓存策略

```javascript
// 缓存翻译数据，避免重复请求
class TranslationCache {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5分钟过期
  }
  
  getCacheKey(url, lang) {
    return `${url}:${lang}`;
  }
  
  get(url, lang) {
    const key = this.getCacheKey(url, lang);
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    // 检查是否过期
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  set(url, lang, data) {
    const key = this.getCacheKey(url, lang);
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  clear() {
    this.cache.clear();
  }
}

// 使用
const cache = new TranslationCache();

const fetchWithCache = async (url, lang) => {
  // 先查缓存
  const cached = cache.get(url, lang);
  if (cached) return cached;
  
  // 请求API
  const data = await fetch(url, {
    headers: {
      'X-Tenant-ID': '1',
      'Accept-Language': lang
    }
  }).then(r => r.json());
  
  // 存入缓存
  cache.set(url, lang, data);
  
  return data;
};
```

### 3. SEO优化（多语言）

```javascript
// 根据当前语言动态设置页面SEO
const updatePageSEO = (category, language) => {
  // 获取对应语言的翻译
  const translation = category.translations?.[language] || {
    name: category.name,
    seo_title: category.seo_title,
    seo_description: category.seo_description
  };
  
  // 更新页面标题
  document.title = translation.seo_title || translation.name;
  
  // 更新meta description
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    metaDesc.setAttribute('content', translation.seo_description || translation.description);
  }
  
  // 添加语言标签
  const htmlTag = document.documentElement;
  htmlTag.setAttribute('lang', language);
};

// 使用
const category = await fetchCategory(id, currentLanguage);
updatePageSEO(category, currentLanguage);
```

---

## 📊 完整集成检查清单

### 基础集成

- [ ] 能够获取分类列表
- [ ] 能够获取文章列表
- [ ] 能够按分类过滤文章
- [ ] 能够获取文章详情

### 多语言集成

- [ ] 配置了Accept-Language请求头
- [ ] 实现了语言切换器UI
- [ ] 切换语言后能正确刷新数据
- [ ] 分类名称随语言切换
- [ ] 处理了语言回退（请求的语言无翻译时）

### 层级结构集成

- [ ] 能够使用parent_id过滤子文章
- [ ] 能够使用has_parent过滤根/子文章
- [ ] 显示面包屑导航
- [ ] 显示子文章列表
- [ ] 实现系列文章导航

### 性能优化

- [ ] 实现了翻译数据缓存
- [ ] 使用分页加载
- [ ] 图片懒加载
- [ ] 请求去重

### SEO优化

- [ ] 动态设置页面title
- [ ] 动态设置meta description
- [ ] 设置正确的lang属性
- [ ] 多语言URL结构（如 /en/categories/）

---

## 🐛 常见问题

### Q1: Accept-Language不生效？

**检查项**：
1. 请求头拼写是否正确（Accept-Language，注意大小写）
2. 语言代码是否正确（zh-hans不是zh-cn）
3. 服务器是否正确配置了PARLER_LANGUAGES

**测试方法**：
```bash
curl -H "Accept-Language: en" \
     -H "X-Tenant-ID: 1" \
     http://localhost:8000/api/v1/cms/categories/ | jq
```

### Q2: 切换语言后分类名称没变化？

**原因**：
- 该分类没有对应语言的翻译
- 系统回退到默认语言（简体中文）

**解决方案**：
1. 在Admin后台为该分类添加翻译
2. 或者在前端处理回退显示

### Q3: 如何知道哪些语言已翻译？

**方法1：检查translations对象**
```javascript
const checkTranslations = (category) => {
  const translations = category.translations || {};
  return {
    'zh-hans': !!translations['zh-hans']?.name,
    'en': !!translations['en']?.name,
    'zh-hant': !!translations['zh-hant']?.name
  };
};

// 使用
const status = checkTranslations(category);
if (!status.en) {
  console.log('该分类缺少英文翻译');
}
```

**方法2：对比name字段**
```javascript
// 请求所有语言的翻译
const categoryZh = await fetchCategory(id, 'zh-hans');
const categoryEn = await fetchCategory(id, 'en');

if (categoryZh.name === categoryEn.name) {
  console.log('英文翻译缺失，显示的是回退语言');
}
```

### Q4: parent_id和has_parent可以同时使用吗？

**回答**：不建议同时使用，会产生冲突。

**正确用法**：
- ✅ `parent_id=14` - 获取父文章ID为14的子文章
- ✅ `has_parent=true` - 获取所有有父文章的文章
- ❌ `parent_id=14&has_parent=false` - 逻辑矛盾

### Q5: 如何实现文章目录导航？

**示例**：
```javascript
// 获取系列文章的完整结构
const getSeriesStructure = async (rootArticleId) => {
  // 1. 获取根文章
  const root = await fetchArticle(rootArticleId);
  
  // 2. 获取所有子文章
  const childrenRes = await fetch(
    `/api/v1/cms/articles/?parent_id=${rootArticleId}&status=published`,
    { headers: { 'X-Tenant-ID': '1' } }
  );
  const children = (await childrenRes.json()).results;
  
  // 3. 构建目录结构
  return {
    title: root.title,
    slug: root.slug,
    chapters: children.map(child => ({
      id: child.id,
      title: child.title,
      slug: child.slug,
      excerpt: child.excerpt
    }))
  };
};

// 渲染目录
const series = await getSeriesStructure(1);
console.log(`${series.title} - 共${series.chapters.length}章`);
series.chapters.forEach((ch, i) => {
  console.log(`第${i+1}章: ${ch.title}`);
});
```

---

## 📚 相关文档链接

### 详细API文档
- [文章管理API.md](./文章管理API.md) - 完整的文章接口文档
- [分类管理API.md](./分类管理API.md) - 完整的分类接口文档（含多语言）

### 使用指南
- [CMS分类多语言使用指南.md](./CMS分类多语言使用指南.md) - 多语言详细说明

### 管理后台
- [Django_Admin分类翻译管理手册.md](./Django_Admin分类翻译管理手册.md) - Admin使用手册

---

## 🎓 最佳实践

### 1. 语言切换UX设计

**推荐方式**：
```
[ 简 | EN | 繁 ]  ← 紧凑型，适合移动端
[ 简体中文 | English | 繁體中文 ]  ← 完整型，适合桌面端
```

**位置建议**：
- 网站头部右上角
- 用户菜单中
- 设置页面

**切换效果**：
- 平滑过渡（避免闪烁）
- 立即生效
- 保存用户选择

### 2. 回退显示策略

当翻译缺失时的UI处理：

```javascript
const getCategoryName = (category, lang) => {
  // 优先使用请求的语言
  if (category.translations?.[lang]?.name) {
    return category.translations[lang].name;
  }
  
  // 回退到默认语言
  if (category.name) {
    return category.name;
  }
  
  // 最后回退到slug
  return category.slug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};
```

### 3. 加载状态处理

```vue
<template>
  <div>
    <div v-if="loading" class="loading">
      加载中...
    </div>
    
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-else>
      <!-- 正常内容 -->
    </div>
  </div>
</template>
```

### 4. 错误处理

```javascript
const loadCategories = async (lang) => {
  try {
    const res = await fetch('/api/v1/cms/categories/', {
      headers: {
        'X-Tenant-ID': '1',
        'Accept-Language': lang
      }
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error('加载分类失败:', error);
    // 显示用户友好的错误提示
    showError('加载分类失败，请稍后重试');
    return [];
  }
};
```

---

## 🎯 实际应用示例

### 示例1：技术博客分类导航

```javascript
// 创建分类导航组件
const CategoryNav = {
  data() {
    return {
      categories: [],
      currentLang: 'zh-hans'
    };
  },
  
  methods: {
    async loadCategories() {
      const res = await fetch('/api/v1/cms/categories/', {
        headers: {
          'X-Tenant-ID': '1',
          'Accept-Language': this.currentLang
        }
      });
      this.categories = await res.json();
    }
  },
  
  template: `
    <nav class="category-nav">
      <a v-for="cat in categories" :key="cat.id" :href="'/category/' + cat.slug">
        {{ cat.name }}
      </a>
    </nav>
  `
};
```

### 示例2：课程系列页面

```javascript
// 显示课程系列和章节
const CoursePage = {
  data() {
    return {
      course: null,
      chapters: []
    };
  },
  
  async mounted() {
    // 获取课程（根文章）
    this.course = await this.fetchArticle(this.$route.params.id);
    
    // 获取所有章节（子文章）
    const res = await fetch(
      `/api/v1/cms/articles/?parent_id=${this.course.id}&status=published`,
      { headers: { 'X-Tenant-ID': '1' } }
    );
    this.chapters = (await res.json()).results;
  },
  
  template: `
    <div class="course-page">
      <h1>{{ course.title }}</h1>
      <div class="chapters">
        <div v-for="(chapter, i) in chapters" :key="chapter.id" class="chapter">
          <a :href="'/articles/' + chapter.slug">
            第{{ i + 1 }}章：{{ chapter.title }}
          </a>
        </div>
      </div>
    </div>
  `
};
```

---

## 📞 获取帮助

### 文档查询顺序

```
1. 本文档（前端CMS集成快速指南）
   ↓ 没解决
2. CMS分类多语言使用指南.md
   ↓ 没解决
3. 文章管理API.md / 分类管理API.md
   ↓ 没解决
4. 00_API文档索引.md
   ↓ 还没解决
5. 联系后端团队
```

### 常见联系场景

| 问题类型 | 推荐做法 |
|---------|---------|
| API参数不明确 | 查阅对应API文档 |
| 多语言不生效 | 查看本文档Q&A |
| 返回数据格式问题 | 使用Postman测试API |
| 翻译内容缺失 | 联系内容团队补充 |
| 技术故障 | 联系后端团队 |

---

**文档维护**: Backend Development Team  
**最后更新**: 2025-11-03

**Happy Coding! 🚀**

