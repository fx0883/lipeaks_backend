# 前端集成指南 - React

本文档提供 React 的完整集成代码示例。

---

## API Service 封装

```typescript
// services/articleLikeService.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  const tenantId = localStorage.getItem('tenant_id');
  
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId;
  
  return config;
});

// API 方法
export const articleLikeAPI = {
  likeArticle: (articleId: number) => 
    apiClient.post('/api/v1/interactions/article-likes/', { article: articleId }),
  
  unlikeArticle: (articleId: number) => 
    apiClient.delete(`/api/v1/interactions/article-likes/by-article/${articleId}/`),
  
  checkLikeStatus: (articleId: number) => 
    apiClient.get(`/api/v1/interactions/article-likes/check/${articleId}/`),
  
  getMyLikedArticles: (page: number = 1, pageSize: number = 10) => 
    apiClient.get('/api/v1/interactions/article-likes/', { params: { page, page_size: pageSize } }),
  
  getArticleLikers: (articleId: number, page: number = 1) => 
    apiClient.get(`/api/v1/interactions/article-likes/by-article/${articleId}/likers/`, { params: { page } }),
};
```

## Custom Hook

```typescript
// hooks/useArticleLike.ts
import { useState, useEffect, useCallback } from 'react';
import { articleLikeAPI } from '../services/articleLikeService';

export const useArticleLike = (articleId: number, initialCount: number = 0) => {
  const [isLiked, setIsLiked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [likesCount, setLikesCount] = useState(initialCount);
  const [error, setError] = useState<string | null>(null);

  const checkLikeStatus = useCallback(async () => {
    try {
      const response = await articleLikeAPI.checkLikeStatus(articleId);
      setIsLiked(response.data.data.is_liked);
    } catch (err) {
      console.error('Failed to check like status:', err);
    }
  }, [articleId]);

  const toggleLike = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      if (isLiked) {
        await articleLikeAPI.unlikeArticle(articleId);
        setIsLiked(false);
        setLikesCount((prev) => Math.max(0, prev - 1));
      } else {
        await articleLikeAPI.likeArticle(articleId);
        setIsLiked(true);
        setLikesCount((prev) => prev + 1);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '操作失败');
    } finally {
      setIsLoading(false);
    }
  }, [articleId, isLiked, isLoading]);

  useEffect(() => {
    checkLikeStatus();
  }, [checkLikeStatus]);

  return { isLiked, isLoading, likesCount, toggleLike, error };
};
```

## 点赞按钮组件

```tsx
// components/LikeButton.tsx
import React from 'react';
import { useArticleLike } from '../hooks/useArticleLike';
import './LikeButton.css';

interface LikeButtonProps {
  articleId: number;
  initialLikesCount: number;
}

export const LikeButton: React.FC<LikeButtonProps> = ({ articleId, initialLikesCount }) => {
  const { isLiked, isLoading, likesCount, toggleLike, error } = useArticleLike(articleId, initialLikesCount);

  return (
    <div className="like-button-container">
      <button
        className={`like-button ${isLiked ? 'liked' : ''}`}
        onClick={toggleLike}
        disabled={isLoading}
      >
        <span className="like-icon">{isLiked ? '❤️' : '🤍'}</span>
        <span className="like-count">{likesCount}</span>
      </button>
      {error && <div className="like-error">{error}</div>}
    </div>
  );
};
```

## CSS 样式

```css
/* LikeButton.css */
.like-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.like-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.like-button.liked {
  background: #ffe0e0;
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.like-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
```

## 使用示例

```tsx
// 在文章详情页使用
function ArticleDetail({ article }) {
  return (
    <div>
      <h1>{article.title}</h1>
      <LikeButton 
        articleId={article.id} 
        initialLikesCount={article.likes_count} 
      />
    </div>
  );
}
```

---

**更新日期**: 2024-11-19  
**版本**: v1.0
