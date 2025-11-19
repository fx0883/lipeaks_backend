# 前端集成指南 - Vue 3

本文档提供 Vue 3 Composition API 的完整集成代码示例。

---

## Composable 封装

```typescript
// composables/useArticleLike.ts
import { ref, onMounted } from 'vue';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  const tenantId = localStorage.getItem('tenant_id');
  
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId;
  
  return config;
});

export const useArticleLike = (articleId: number, initialCount: number = 0) => {
  const isLiked = ref(false);
  const isLoading = ref(false);
  const likesCount = ref(initialCount);
  const error = ref<string | null>(null);

  const checkLikeStatus = async () => {
    try {
      const response = await apiClient.get(
        `/api/v1/interactions/article-likes/check/${articleId}/`
      );
      isLiked.value = response.data.data.is_liked;
    } catch (err) {
      console.error('Failed to check like status:', err);
    }
  };

  const toggleLike = async () => {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      if (isLiked.value) {
        await apiClient.delete(
          `/api/v1/interactions/article-likes/by-article/${articleId}/`
        );
        isLiked.value = false;
        likesCount.value = Math.max(0, likesCount.value - 1);
      } else {
        await apiClient.post('/api/v1/interactions/article-likes/', {
          article: articleId,
        });
        isLiked.value = true;
        likesCount.value += 1;
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || '操作失败';
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(() => {
    checkLikeStatus();
  });

  return { isLiked, isLoading, likesCount, error, toggleLike };
};
```

## 点赞按钮组件

```vue
<!-- components/LikeButton.vue -->
<template>
  <div class="like-button-container">
    <button
      :class="['like-button', { liked: isLiked, loading: isLoading }]"
      :disabled="isLoading"
      @click="toggleLike"
    >
      <span class="like-icon">{{ isLiked ? '❤️' : '🤍' }}</span>
      <span class="like-count">{{ likesCount }}</span>
    </button>
    <div v-if="error" class="like-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { useArticleLike } from '../composables/useArticleLike';

interface Props {
  articleId: number;
  initialLikesCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  initialLikesCount: 0,
});

const { isLiked, isLoading, likesCount, error, toggleLike } = useArticleLike(
  props.articleId,
  props.initialLikesCount
);
</script>

<style scoped>
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

.like-error {
  color: #f44336;
  font-size: 12px;
  margin-top: 4px;
}
</style>
```

## 点赞列表组件

```vue
<!-- components/LikedArticlesList.vue -->
<template>
  <div class="liked-articles-list">
    <h2>我点赞的文章</h2>
    
    <div v-if="loading && page === 1" class="loading">加载中...</div>
    
    <div v-else class="articles-grid">
      <div v-for="item in articles" :key="item.id" class="article-card">
        <img :src="item.article_detail.cover_image" :alt="item.article_detail.title" />
        <h3>{{ item.article_detail.title }}</h3>
        <p>{{ item.article_detail.excerpt }}</p>
        <span class="liked-at">
          点赞于 {{ formatDate(item.created_at) }}
        </span>
      </div>
    </div>

    <button v-if="hasMore && !loading" @click="loadMore" class="load-more-btn">
      加载更多
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  const tenantId = localStorage.getItem('tenant_id');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId;
  return config;
});

const articles = ref([]);
const loading = ref(false);
const page = ref(1);
const hasMore = ref(true);

const loadArticles = async (pageNum: number) => {
  try {
    loading.value = true;
    const response = await apiClient.get('/api/v1/interactions/article-likes/', {
      params: { page: pageNum, page_size: 10 }
    });
    
    const newArticles = response.data.data.results;
    articles.value = pageNum === 1 ? newArticles : [...articles.value, ...newArticles];
    hasMore.value = response.data.data.pagination.next !== null;
  } catch (error) {
    console.error('Failed to load liked articles:', error);
  } finally {
    loading.value = false;
  }
};

const loadMore = () => {
  page.value += 1;
  loadArticles(page.value);
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN');
};

onMounted(() => {
  loadArticles(1);
});
</script>

<style scoped>
.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.article-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.3s ease;
}

.article-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.load-more-btn {
  margin: 20px auto;
  display: block;
  padding: 10px 30px;
  border: 1px solid #1976d2;
  background: white;
  color: #1976d2;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

## 使用示例

```vue
<!-- pages/ArticleDetail.vue -->
<template>
  <div class="article-detail">
    <h1>{{ article.title }}</h1>
    <LikeButton 
      :article-id="article.id" 
      :initial-likes-count="article.likes_count" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import LikeButton from '../components/LikeButton.vue';

const article = ref({
  id: 100,
  title: '文章标题',
  likes_count: 42
});
</script>
```

---

**更新日期**: 2024-11-19  
**版本**: v1.0
