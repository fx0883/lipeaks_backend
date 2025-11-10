# 5. 分类标签 API 集成指南

## 🎯 概述

分类标签系统提供完整的文章分类管理功能，包括分类(Category)、标签(Tag)和标签分组(TagGroup)。支持层级分类、标签云展示等高级功能。

## 📋 API 列表

### 分类管理 (Categories)
| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取分类列表](#获取分类列表) | GET | `/cms/categories/` | 获取所有分类，支持树形结构 |
| [获取分类详情](#获取分类详情) | GET | `/cms/categories/{id}/` | 获取单个分类信息 |
| [创建分类](#创建分类) | POST | `/cms/categories/` | 创建新分类 |
| [更新分类](#更新分类) | PUT/PATCH | `/cms/categories/{id}/` | 更新分类信息 |
| [删除分类](#删除分类) | DELETE | `/cms/categories/{id}/` | 删除分类 |
| [获取分类树](#获取分类树) | GET | `/cms/categories/tree/` | 获取完整的分类树结构 |

### 标签管理 (Tags)
| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取标签列表](#获取标签列表) | GET | `/cms/tags/` | 获取所有标签 |
| [获取标签详情](#获取标签详情) | GET | `/cms/tags/{id}/` | 获取单个标签信息 |
| [创建标签](#创建标签) | POST | `/cms/tags/` | 创建新标签 |
| [更新标签](#更新标签) | PUT/PATCH | `/cms/tags/{id}/` | 更新标签信息 |
| [删除标签](#删除标签) | DELETE | `/cms/tags/{id}/` | 删除标签 |

### 标签分组管理 (Tag Groups)
| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取标签分组列表](#获取标签分组列表) | GET | `/cms/tag-groups/` | 获取所有标签分组 |
| [获取标签分组详情](#获取标签分组详情) | GET | `/cms/tag-groups/{id}/` | 获取单个标签分组信息 |
| [创建标签分组](#创建标签分组) | POST | `/cms/tag-groups/` | 创建新标签分组 |
| [更新标签分组](#更新标签分组) | PUT/PATCH | `/cms/tag-groups/{id}/` | 更新标签分组信息 |
| [删除标签分组](#删除标签分组) | DELETE | `/cms/tag-groups/{id}/` | 删除标签分组 |

---

## 获取分类列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/categories/`
- **权限要求**: 无需认证，公开访问
- **功能说明**: 获取所有分类列表，支持分页和搜索

### 请求头（可选）
```bash
X-Tenant-ID: {tenant_id}  # 按租户过滤（可选）
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |
| search | string | 否 | 按名称或描述搜索 | "前端" | 最长50字符 |
| parent | integer | 否 | 按父分类ID过滤 | 5 | 有效的分类ID |
| level | integer | 否 | 按层级过滤（1-3） | 2 | 1-3之间的整数 |
| is_active | boolean | 否 | 是否只返回激活的分类 | true | true/false |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/categories/?page=1&page_size=10&is_active=true" \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取分类列表
```javascript
const getCategories = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20,
    is_active: params.isActive !== false ? 'true' : 'false',
    search: params.search || '',
    parent: params.parent || '',
    level: params.level || ''
  });

  // 过滤空参数
  for (const [key, value] of queryParams.entries()) {
    if (!value) {
      queryParams.delete(key);
    }
  }

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/categories/?${queryParams}`, {
      method: 'GET',
      headers: {
        'X-Tenant-ID': '1'  // 可选，用于按租户过滤
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('分类列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取分类列表失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {
      "id": 5,
      "slug": "how-to-841",
      "parent": null,
      "cover_image": null,
      "created_at": "2025-10-09T10:14:15.921164Z",
      "updated_at": "2025-10-09T10:14:15.921207Z",
      "sort_order": 0,
      "tenant": 1,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "How To 841",
          "description": "How To 841分类",
          "seo_title": null,
          "seo_description": null
        }
      },
      "name": "How To 841",
      "description": "How To 841分类",
      "seo_title": "",
      "seo_description": ""
    },
    {
      "id": 6,
      "slug": "review-064",
      "parent": null,
      "cover_image": null,
      "created_at": "2025-10-10T14:14:50.667579Z",
      "updated_at": "2025-10-10T14:14:50.667612Z",
      "sort_order": 0,
      "tenant": 1,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "Review 064",
          "description": "Review 064分类",
          "seo_title": null,
          "seo_description": null
        }
      },
      "name": "Review 064",
      "description": "Review 064分类",
      "seo_title": "",
      "seo_description": ""
    },
    {
      "id": 7,
      "slug": "tutorial-565",
      "parent": null,
      "cover_image": null,
      "created_at": "2025-10-10T14:15:03.832678Z",
      "updated_at": "2025-10-10T14:15:03.832719Z",
      "sort_order": 0,
      "tenant": 1,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "Tutorial 565",
          "description": "Tutorial 565分类",
          "seo_title": null,
          "seo_description": null
        }
      },
      "name": "Tutorial 565",
      "description": "Tutorial 565分类",
      "seo_title": "",
      "seo_description": ""
    },
    {
      "id": 8,
      "slug": "update-150",
      "parent": null,
      "cover_image": null,
      "created_at": "2025-10-10T14:15:13.995358Z",
      "updated_at": "2025-10-10T14:15:13.995379Z",
      "sort_order": 0,
      "tenant": 1,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "Update 150",
          "description": "Update 150分类",
          "seo_title": null,
          "seo_description": null
        }
      },
      "name": "Update 150",
      "description": "Update 150分类",
      "seo_title": "",
      "seo_description": ""
    },
    {
      "id": 9,
      "slug": "news-571",
      "parent": null,
      "cover_image": null,
      "created_at": "2025-10-10T14:15:26.736819Z",
      "updated_at": "2025-10-10T14:15:26.736868Z",
      "sort_order": 0,
      "tenant": 1,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "News 571",
          "description": "News 571分类",
          "seo_title": null,
          "seo_description": null
        }
      },
      "name": "News 571",
      "description": "News 571分类",
      "seo_title": "",
      "seo_description": ""
    }
  ]
}
```

---

## 获取分类树

### 接口信息
- **接口地址**: `GET /api/v1/cms/categories/tree/`
- **权限要求**: 无需认证，公开访问
- **功能说明**: 获取完整的分类树结构，包含所有层级的分类

### 请求头（可选）
```bash
X-Tenant-ID: {tenant_id}  # 按租户过滤（可选）
```

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/categories/tree/" \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取分类树
```javascript
const getCategoryTree = async () => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/cms/categories/tree/', {
      method: 'GET',
      headers: {
        'X-Tenant-ID': '1'  // 可选
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('分类树:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取分类树失败:', error);
    throw error;
  }
};

// 使用示例 - 渲染分类树菜单
const renderCategoryTree = async () => {
  try {
    const treeData = await getCategoryTree();

    const renderNode = (node, level = 0) => {
      const indent = '  '.repeat(level);
      let html = `${indent}<div class="category-item" data-id="${node.id}" data-level="${node.level}">`;
      html += `${indent}  <span class="category-icon">${node.icon || '📁'}</span>`;
      html += `${indent}  <span class="category-name">${node.name}</span>`;
      html += `${indent}  <span class="category-count">(${node.article_count})</span>`;
      html += `${indent}</div>`;

      if (node.children && node.children.length > 0) {
        html += `${indent}<div class="category-children">`;
        node.children.forEach(child => {
          html += renderNode(child, level + 1);
        });
        html += `${indent}</div>`;
      }

      return html;
    };

    const treeHtml = treeData.map(node => renderNode(node)).join('');
    document.getElementById('category-tree').innerHTML = treeHtml;

  } catch (error) {
    console.error('渲染分类树失败:', error);
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {
      "id": 5,
      "name": "How To 841",
      "slug": "how-to-841",
      "description": "How To 841分类",
      "is_active": true,
      "sort_order": 0,
      "children": []
    },
    {
      "id": 6,
      "name": "Review 064",
      "slug": "review-064",
      "description": "Review 064分类",
      "is_active": true,
      "sort_order": 0,
      "children": []
    },
    {
      "id": 7,
      "name": "Tutorial 565",
      "slug": "tutorial-565",
      "description": "Tutorial 565分类",
      "is_active": true,
      "sort_order": 0,
      "children": []
    },
    {
      "id": 8,
      "name": "Update 150",
      "slug": "update-150",
      "description": "Update 150分类",
      "is_active": true,
      "sort_order": 0,
      "children": []
    },
    {
      "id": 9,
      "name": "News 571",
      "slug": "news-571",
      "description": "News 571分类",
      "is_active": true,
      "sort_order": 0,
      "children": []
    }
  ]
}

---

## 创建分类

### 接口信息
- **接口地址**: `POST /api/v1/cms/categories/`
- **权限要求**: 需要管理员权限
- **功能说明**: 创建新的文章分类

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}  # 可选，用于指定租户
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| name | string | 是 | 分类名称 | "人工智能" | 1-50字符，租户内唯一 |
| slug | string | 否 | URL别名 | "ai" | 字母、数字、下划线，租户内唯一 |
| description | string | 否 | 分类描述 | "人工智能相关技术文章" | 最长255字符 |
| parent | integer | 否 | 父分类ID | 1 | 有效的父分类ID，不能循环引用 |
| order | integer | 否 | 显示顺序 | 1 | 0-999，默认0 |
| is_active | boolean | 否 | 是否激活 | true | true/false，默认true |
| icon | string | 否 | 图标 | "🤖" | emoji字符，最长10字符 |
| color | string | 否 | 主题色 | "#ff6b6b" | 十六进制颜色值 |
| meta_title | string | 否 | SEO标题 | "人工智能 - 技术博客" | 最长60字符 |
| meta_description | string | 否 | SEO描述 | "探索人工智能最新技术和应用" | 最长160字符 |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/cms/categories/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "人工智能",
    "slug": "ai",
    "description": "人工智能相关技术文章",
    "parent": null,
    "order": 3,
    "is_active": true,
    "icon": "🤖",
    "color": "#ff6b6b",
    "meta_title": "人工智能 - 技术博客",
    "meta_description": "探索人工智能最新技术和应用"
  }'
```

#### JavaScript 创建分类
```javascript
const createCategory = async (categoryData) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/cms/categories/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify(categoryData)
    });

    const result = await response.json();

    if (result.success) {
      console.log('分类创建成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('创建分类失败:', error);
    throw error;
  }
};

// 使用示例
const newCategory = {
  name: '人工智能',
  slug: 'ai',
  description: '人工智能相关技术文章',
  parent: null,
  order: 3,
  is_active: true,
  icon: '🤖',
  color: '#ff6b6b',
  meta_title: '人工智能 - 技术博客',
  meta_description: '探索人工智能最新技术和应用'
};

const createdCategory = await createCategory(newCategory);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "分类创建成功",
  "data": {
    "id": 6,
    "name": "人工智能",
    "slug": "ai",
    "description": "人工智能相关技术文章",
    "parent": null,
    "level": 1,
    "order": 3,
    "is_active": true,
    "icon": "🤖",
    "color": "#ff6b6b",
    "article_count": 0,
    "meta_title": "人工智能 - 技术博客",
    "meta_description": "探索人工智能最新技术和应用",
    "created_at": "2024-01-20T14:30:00Z",
    "updated_at": "2024-01-20T14:30:00Z",
    "full_path": "人工智能",
    "children": []
  }
}
```

---

## 获取标签列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/tags/`
- **权限要求**: 无需认证，公开访问
- **功能说明**: 获取所有标签列表，支持分页和搜索

### 请求头（可选）
```bash
X-Tenant-ID: {tenant_id}  # 按租户过滤（可选）
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |
| search | string | 否 | 按名称搜索 | "Vue" | 最长50字符 |
| group_id | integer | 否 | 按标签分组ID过滤 | 2 | 有效的分组ID |
| is_active | boolean | 否 | 是否只返回激活的标签 | true | true/false |
| ordering | string | 否 | 排序方式 | "article_count" | name/article_count/created_at |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/tags/?page=1&page_size=20&ordering=-article_count" \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取标签列表
```javascript
const getTags = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20,
    search: params.search || '',
    group_id: params.groupId || '',
    is_active: params.isActive !== false ? 'true' : 'false',
    ordering: params.ordering || 'article_count'
  });

  // 过滤空参数
  for (const [key, value] of queryParams.entries()) {
    if (!value) {
      queryParams.delete(key);
    }
  }

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/tags/?${queryParams}`, {
      method: 'GET',
      headers: {
        'X-Tenant-ID': '1'  // 可选
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('标签列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取标签列表失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 1,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "name": "hello",
        "slug": "hello-235",
        "description": "",
        "group": null,
        "group_name": null,
        "created_at": "2025-10-08T12:58:55.756408Z",
        "updated_at": "2025-10-08T12:58:55.756457Z",
        "color": "#409EFF",
        "is_active": true,
        "tenant": 1
      }
    ]
  }
}

---

## 创建标签

### 接口信息
- **接口地址**: `POST /api/v1/cms/tags/`
- **权限要求**: 需要管理员权限
- **功能说明**: 创建新的文章标签

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}  # 可选，用于指定租户
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| name | string | 是 | 标签名称 | "机器学习" | 1-30字符，租户内唯一 |
| slug | string | 否 | URL别名 | "machine-learning" | 字母、数字、下划线，租户内唯一 |
| description | string | 否 | 标签描述 | "机器学习算法和技术" | 最长255字符 |
| color | string | 否 | 主题色 | "#ff6b6b" | 十六进制颜色值 |
| group | integer | 否 | 所属标签分组ID | 2 | 有效的分组ID |
| is_active | boolean | 否 | 是否激活 | true | true/false，默认true |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/cms/tags/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "机器学习",
    "slug": "machine-learning",
    "description": "机器学习算法和技术",
    "color": "#ff6b6b",
    "group": 2,
    "is_active": true
  }'
```

#### JavaScript 创建标签
```javascript
const createTag = async (tagData) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/cms/tags/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify(tagData)
    });

    const result = await response.json();

    if (result.success) {
      console.log('标签创建成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('创建标签失败:', error);
    throw error;
  }
};

// 使用示例
const newTag = {
  name: '机器学习',
  slug: 'machine-learning',
  description: '机器学习算法和技术',
  color: '#ff6b6b',
  group: 2,
  is_active: true
};

const createdTag = await createTag(newTag);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "标签创建成功",
  "data": {
    "id": 10,
    "name": "机器学习",
    "slug": "machine-learning",
    "description": "机器学习算法和技术",
    "color": "#ff6b6b",
    "is_active": true,
    "article_count": 0,
    "group": {
      "id": 2,
      "name": "AI技术",
      "slug": "ai-tech"
    },
    "created_at": "2024-01-20T14:30:00Z",
    "updated_at": "2024-01-20T14:30:00Z"
  }
}
```

---

## 获取标签分组列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/tag-groups/`
- **权限要求**: 无需认证，公开访问
- **功能说明**: 获取所有标签分组列表

### 请求头（可选）
```bash
X-Tenant-ID: {tenant_id}  # 按租户过滤（可选）
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |
| search | string | 否 | 按名称搜索 | "前端" | 最长50字符 |
| is_active | boolean | 否 | 是否只返回激活的分组 | true | true/false |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/tag-groups/?page=1&page_size=10" \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取标签分组列表
```javascript
const getTagGroups = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20,
    search: params.search || '',
    is_active: params.isActive !== false ? 'true' : 'false'
  });

  // 过滤空参数
  for (const [key, value] of queryParams.entries()) {
    if (!value) {
      queryParams.delete(key);
    }
  }

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/tag-groups/?${queryParams}`, {
      method: 'GET',
      headers: {
        'X-Tenant-ID': '1'  // 可选
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('标签分组列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取标签分组列表失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "前端框架",
        "slug": "frontend-frameworks",
        "description": "前端开发框架相关标签",
        "color": "#007bff",
        "icon": "🖥️",
        "order": 1,
        "is_active": true,
        "tag_count": 8,
        "created_at": "2024-01-01T08:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": 2,
        "name": "AI技术",
        "slug": "ai-tech",
        "description": "人工智能相关技术标签",
        "color": "#ff6b6b",
        "icon": "🤖",
        "order": 2,
        "is_active": true,
        "tag_count": 5,
        "created_at": "2024-01-01T08:15:00Z",
        "updated_at": "2024-01-15T11:00:00Z"
      }
    ]
  }
}
```

---

## 🔧 前端集成最佳实践

### 1. 分类树组件
```javascript
class CategoryTree {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      maxLevel: 3,
      showCount: true,
      showIcons: true,
      collapsible: true,
      ...options
    };

    this.treeData = null;
    this.expandedNodes = new Set();

    this.init();
  }

  async init() {
    await this.loadTreeData();
    this.render();
    this.bindEvents();
  }

  async loadTreeData() {
    try {
      const response = await fetch('/api/v1/cms/categories/tree/', {
        headers: {
          'X-Tenant-ID': '1'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.treeData = result.data;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('加载分类树失败:', error);
      this.showError('加载失败，请重试');
    }
  }

  render() {
    if (!this.treeData) return;

    const html = this.renderNode(this.treeData);
    this.container.innerHTML = `<ul class="category-tree">${html}</ul>`;
  }

  renderNode(nodes, level = 0) {
    return nodes.map(node => {
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = this.expandedNodes.has(node.id);
      const indentClass = `level-${Math.min(level, this.options.maxLevel - 1)}`;

      let html = `<li class="category-node ${indentClass}" data-id="${node.id}">`;

      // 展开/折叠按钮
      if (hasChildren && this.options.collapsible) {
        const expandedClass = isExpanded ? 'expanded' : 'collapsed';
        html += `<span class="toggle-btn ${expandedClass}" data-id="${node.id}">▶</span>`;
      } else {
        html += '<span class="toggle-spacer"></span>';
      }

      // 图标
      if (this.options.showIcons && node.icon) {
        html += `<span class="category-icon">${node.icon}</span>`;
      }

      // 名称
      html += `<span class="category-name">${node.name}</span>`;

      // 文章数量
      if (this.options.showCount) {
        html += `<span class="category-count">(${node.article_count})</span>`;
      }

      // 子节点
      if (hasChildren && (!this.options.collapsible || isExpanded)) {
        html += '<ul class="category-children">';
        html += this.renderNode(node.children, level + 1);
        html += '</ul>';
      }

      html += '</li>';
      return html;
    }).join('');
  }

  bindEvents() {
    // 展开/折叠事件
    this.container.addEventListener('click', (e) => {
      if (e.target.classList.contains('toggle-btn')) {
        const nodeId = parseInt(e.target.dataset.id);
        this.toggleNode(nodeId);
      }
    });

    // 分类点击事件
    this.container.addEventListener('click', (e) => {
      if (e.target.classList.contains('category-name')) {
        const nodeId = parseInt(e.target.closest('.category-node').dataset.id);
        this.onCategoryClick(nodeId);
      }
    });
  }

  toggleNode(nodeId) {
    if (this.expandedNodes.has(nodeId)) {
      this.expandedNodes.delete(nodeId);
    } else {
      this.expandedNodes.add(nodeId);
    }
    this.render();
  }

  onCategoryClick(categoryId) {
    // 触发自定义事件
    const event = new CustomEvent('categorySelect', {
      detail: { categoryId }
    });
    this.container.dispatchEvent(event);
  }

  showError(message) {
    this.container.innerHTML = `<div class="error">${message}</div>`;
  }

  // 展开所有节点
  expandAll() {
    const collectIds = (nodes) => {
      nodes.forEach(node => {
        this.expandedNodes.add(node.id);
        if (node.children) {
          collectIds(node.children);
        }
      });
    };

    if (this.treeData) {
      collectIds(this.treeData);
      this.render();
    }
  }

  // 折叠所有节点
  collapseAll() {
    this.expandedNodes.clear();
    this.render();
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const treeContainer = document.getElementById('category-tree');
  const categoryTree = new CategoryTree(treeContainer, {
    maxLevel: 3,
    showCount: true,
    showIcons: true,
    collapsible: true
  });

  // 监听分类选择事件
  treeContainer.addEventListener('categorySelect', (e) => {
    const categoryId = e.detail.categoryId;
    console.log('选择了分类:', categoryId);
    // 加载该分类的文章
    loadArticlesByCategory(categoryId);
  });
});
```

### 2. 标签云组件
```javascript
class TagCloud {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      maxTags: 50,
      minFontSize: 12,
      maxFontSize: 24,
      sortBy: 'article_count', // name, article_count, created_at
      showCount: true,
      clickable: true,
      ...options
    };

    this.tags = [];
    this.init();
  }

  async init() {
    await this.loadTags();
    this.render();
    this.bindEvents();
  }

  async loadTags() {
    try {
      const response = await fetch(`/api/v1/cms/tags/?page_size=${this.options.maxTags}&ordering=-${this.options.sortBy}`, {
        headers: {
          'X-Tenant-ID': '1'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.tags = result.data.results;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('加载标签失败:', error);
      this.showError('加载失败，请重试');
    }
  }

  render() {
    if (!this.tags.length) return;

    // 计算字体大小
    const counts = this.tags.map(tag => tag.article_count);
    const minCount = Math.min(...counts);
    const maxCount = Math.max(...counts);

    const html = this.tags.map(tag => {
      const fontSize = this.calculateFontSize(tag.article_count, minCount, maxCount);
      const style = `font-size: ${fontSize}px; color: ${tag.color || '#666'};`;

      let tagHtml = `<span class="tag-item" data-id="${tag.id}" style="${style}">`;
      tagHtml += tag.name;

      if (this.options.showCount) {
        tagHtml += ` <span class="tag-count">(${tag.article_count})</span>`;
      }

      tagHtml += '</span>';

      return tagHtml;
    }).join('');

    this.container.innerHTML = `<div class="tag-cloud">${html}</div>`;
  }

  calculateFontSize(count, minCount, maxCount) {
    if (minCount === maxCount) {
      return this.options.minFontSize;
    }

    const ratio = (count - minCount) / (maxCount - minCount);
    const fontSize = this.options.minFontSize +
      (this.options.maxFontSize - this.options.minFontSize) * ratio;

    return Math.round(fontSize);
  }

  bindEvents() {
    if (!this.options.clickable) return;

    this.container.addEventListener('click', (e) => {
      if (e.target.classList.contains('tag-item') ||
          e.target.closest('.tag-item')) {
        const tagItem = e.target.closest('.tag-item');
        const tagId = parseInt(tagItem.dataset.id);

        this.onTagClick(tagId);
      }
    });
  }

  onTagClick(tagId) {
    // 触发自定义事件
    const event = new CustomEvent('tagSelect', {
      detail: { tagId }
    });
    this.container.dispatchEvent(event);
  }

  showError(message) {
    this.container.innerHTML = `<div class="error">${message}</div>`;
  }

  // 刷新标签云
  async refresh() {
    await this.loadTags();
    this.render();
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const cloudContainer = document.getElementById('tag-cloud');
  const tagCloud = new TagCloud(cloudContainer, {
    maxTags: 30,
    minFontSize: 14,
    maxFontSize: 28,
    sortBy: 'article_count',
    showCount: true,
    clickable: true
  });

  // 监听标签选择事件
  cloudContainer.addEventListener('tagSelect', (e) => {
    const tagId = e.detail.tagId;
    console.log('选择了标签:', tagId);
    // 加载该标签的文章
    loadArticlesByTag(tagId);
  });
});
```

### 3. 分类选择器组件
```javascript
class CategorySelector {
  constructor(selectElement, options = {}) {
    this.select = selectElement;
    this.options = {
      placeholder: '请选择分类',
      allowClear: true,
      showTree: true,
      maxLevel: 3,
      ...options
    };

    this.categories = [];
    this.init();
  }

  async init() {
    await this.loadCategories();
    this.render();
    this.bindEvents();
  }

  async loadCategories() {
    try {
      const response = await fetch('/api/v1/cms/categories/tree/', {
        headers: {
          'X-Tenant-ID': '1'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.categories = result.data;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  }

  render() {
    let html = `<option value="">${this.options.placeholder}</option>`;

    if (this.options.showTree) {
      html += this.renderTreeOptions(this.categories);
    } else {
      html += this.renderFlatOptions(this.categories);
    }

    this.select.innerHTML = html;
  }

  renderTreeOptions(nodes, level = 0) {
    let html = '';

    nodes.forEach(node => {
      const indent = '　'.repeat(level); // 全角空格
      html += `<option value="${node.id}">${indent}${node.icon || ''} ${node.name}</option>`;

      if (node.children && node.children.length > 0 && level < this.options.maxLevel - 1) {
        html += this.renderTreeOptions(node.children, level + 1);
      }
    });

    return html;
  }

  renderFlatOptions(nodes) {
    let html = '';

    const flatten = (nodes) => {
      nodes.forEach(node => {
        html += `<option value="${node.id}">${node.icon || ''} ${node.full_path}</option>`;
        if (node.children) {
          flatten(node.children);
        }
      });
    };

    flatten(nodes);
    return html;
  }

  bindEvents() {
    this.select.addEventListener('change', (e) => {
      const categoryId = e.target.value;
      this.onCategoryChange(categoryId);
    });
  }

  onCategoryChange(categoryId) {
    // 触发自定义事件
    const event = new CustomEvent('categoryChange', {
      detail: { categoryId }
    });
    this.select.dispatchEvent(event);
  }

  // 获取选中的分类信息
  getSelectedCategory() {
    const selectedId = this.select.value;
    if (!selectedId) return null;

    // 在树形结构中查找选中的分类
    const findCategory = (nodes) => {
      for (const node of nodes) {
        if (node.id.toString() === selectedId) {
          return node;
        }
        if (node.children) {
          const found = findCategory(node.children);
          if (found) return found;
        }
      }
      return null;
    };

    return findCategory(this.categories);
  }

  // 设置选中的分类
  setSelectedCategory(categoryId) {
    this.select.value = categoryId;
  }

  // 清空选择
  clearSelection() {
    this.select.value = '';
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const categorySelect = document.getElementById('category-select');
  const selector = new CategorySelector(categorySelect, {
    placeholder: '请选择文章分类',
    allowClear: true,
    showTree: true,
    maxLevel: 3
  });

  // 监听分类变化事件
  categorySelect.addEventListener('categoryChange', (e) => {
    const categoryId = e.detail.categoryId;
    console.log('选择了分类:', categoryId);

    const category = selector.getSelectedCategory();
    if (category) {
      console.log('分类信息:', category);
    }
  });
});
```
