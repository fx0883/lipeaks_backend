# Member 头像上传 API

本文档详细说明Member头像上传管理的API接口。

---

## 目录

- [头像功能说明](#头像功能说明)
- [1. 为指定Member上传头像](#1-为指定member上传头像)
- [2. 为当前Member上传头像](#2-为当前member上传头像)
- [使用示例](#使用示例)
- [前端实现参考](#前端实现参考)

---

## 头像功能说明

### 功能特点

- 📁 **支持格式**：JPG, JPEG, PNG, GIF, WEBP, BMP
- 📏 **大小限制**：最大2MB
- 🔄 **自动替换**：上传新头像会自动删除旧头像文件
- 🔒 **权限控制**：严格的权限验证
- 📦 **路径管理**：统一存储在`/media/avatars/`目录

### 存储说明

- **存储路径**：`/media/avatars/`
- **文件命名**：使用UUID确保唯一性，格式：`<uuid>.<ext>`
- **URL格式**：`/media/avatars/abc123-def456.jpg`
- **访问方式**：通过Nginx或Django静态文件服务提供

### 权限说明

| 操作 | 超级管理员 | 租户管理员 | Member | 子账号 |
|------|-----------|-----------|--------|--------|
| 为任意Member上传头像 | ✅ | ❌ | ❌ | ❌ |
| 为本租户Member上传头像 | ✅ | ✅ | ❌ | ❌ |
| 为自己上传头像 | ✅ | ✅ | ✅ | ❌ |
| 为子账号上传头像 | ✅ | ✅ | ✅ (自己的子账号) | ❌ |

---

## 1. 为指定Member上传头像

管理员为指定的Member上传头像。

### 基本信息

```
POST /api/v1/admin/members/{id}/avatar/upload/
```

**权限要求**：
- 超级管理员：可为任意Member上传头像
- 租户管理员：可为本租户的Member上传头像
- Member：只能为自己的子账号上传头像

**内容类型**：`multipart/form-data`

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | Member的ID |

### 表单参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| avatar | file | 是 | 头像文件 |

### 文件要求

| 项目 | 要求 |
|------|------|
| 支持格式 | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp` |
| 文件大小 | 最大 2MB (2097152 bytes) |
| 字段名称 | `avatar` |

### 请求示例

#### HTML表单示例

```html
<form id="avatarForm" enctype="multipart/form-data">
  <input type="file" id="avatarInput" name="avatar" accept="image/*" />
  <button type="submit">上传头像</button>
</form>

<script>
document.getElementById('avatarForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData();
  const fileInput = document.getElementById('avatarInput');
  formData.append('avatar', fileInput.files[0]);
  
  const response = await fetch('/api/v1/admin/members/10/avatar/upload/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('上传成功:', result);
});
</script>
```

#### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/admin/members/10/avatar/upload/" \
  -H "Authorization: Bearer <your_token>" \
  -F "avatar=@/path/to/avatar.jpg"
```

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "detail": "头像上传成功",
  "avatar": "/media/avatars/abc123-def456-ghi789.jpg"
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| detail | string | 操作结果描述 |
| avatar | string | 头像URL相对路径 |

### 错误响应

#### 400 未提供头像文件

```json
{
  "detail": "未提供头像文件"
}
```

#### 400 不支持的文件类型

```json
{
  "detail": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片"
}
```

#### 400 文件太大

```json
{
  "detail": "文件太大，头像大小不能超过2MB"
}
```

#### 403 权限不足

**场景1：租户管理员尝试为其他租户的Member上传**

```json
{
  "detail": "您没有权限为该普通用户上传头像"
}
```

**场景2：Member尝试为非子账号上传**

```json
{
  "detail": "您只能为自己的子账号上传头像"
}
```

#### 404 Member不存在

```json
{
  "detail": "普通用户不存在"
}
```

#### 500 上传失败

```json
{
  "detail": "头像上传失败: <error_message>"
}
```

---

## 2. 为当前Member上传头像

Member为自己上传头像（Member自用API，非管理功能）。

### 基本信息

```
POST /api/v1/admin/members/avatar/upload/
```

**权限要求**：
- 必须是Member用户
- 不能是子账号

**内容类型**：`multipart/form-data`

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### 表单参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| avatar | file | 是 | 头像文件 |

### 文件要求

同"为指定Member上传头像"

### 请求示例

#### HTML表单示例

```html
<form id="myAvatarForm" enctype="multipart/form-data">
  <input type="file" id="myAvatarInput" name="avatar" accept="image/*" />
  <button type="submit">上传我的头像</button>
</form>

<script>
document.getElementById('myAvatarForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData();
  const fileInput = document.getElementById('myAvatarInput');
  formData.append('avatar', fileInput.files[0]);
  
  const response = await fetch('/api/v1/admin/members/avatar/upload/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('上传成功:', result);
});
</script>
```

#### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/admin/members/avatar/upload/" \
  -H "Authorization: Bearer <your_token>" \
  -F "avatar=@/path/to/my-avatar.jpg"
```

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "detail": "头像上传成功",
  "avatar": "/media/avatars/xyz789-abc123-def456.jpg"
}
```

### 错误响应

#### 403 非Member用户

```json
{
  "detail": "该接口仅适用于普通用户"
}
```

#### 403 子账号尝试上传

```json
{
  "detail": "子账号不允许更改头像"
}
```

其他错误响应同"为指定Member上传头像"。

---

## 使用示例

### JavaScript/Axios示例

```javascript
import axios from 'axios';

// 为指定Member上传头像
async function uploadMemberAvatar(memberId, file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  try {
    const response = await axios.post(
      `/api/v1/admin/members/${memberId}/avatar/upload/`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('上传失败:', error);
    throw error;
  }
}

// 为当前Member上传头像
async function uploadMyAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  try {
    const response = await axios.post(
      '/api/v1/admin/members/avatar/upload/',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('上传失败:', error);
    throw error;
  }
}

// 使用示例 - 从文件输入上传
const fileInput = document.querySelector('#avatarInput');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  
  if (!file) return;
  
  // 验证文件大小
  if (file.size > 2 * 1024 * 1024) {
    alert('文件太大，头像大小不能超过2MB');
    return;
  }
  
  // 验证文件类型
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
  if (!validTypes.includes(file.type)) {
    alert('不支持的文件类型');
    return;
  }
  
  try {
    const result = await uploadMemberAvatar(10, file);
    console.log('头像URL:', result.avatar);
    alert('上传成功！');
  } catch (error) {
    alert('上传失败：' + error.response?.data?.detail);
  }
});
```

### Vue 3 组合式API示例

```vue
<template>
  <div class="avatar-uploader">
    <!-- 头像显示 -->
    <div class="avatar-preview">
      <el-avatar
        :size="120"
        :src="avatarUrl"
        icon="UserFilled"
      />
    </div>
    
    <!-- 上传按钮 -->
    <el-upload
      class="upload-btn"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      accept="image/*"
    >
      <el-button type="primary" :loading="uploading">
        {{ uploading ? '上传中...' : '上传头像' }}
      </el-button>
    </el-upload>
    
    <!-- 提示信息 -->
    <div class="upload-hint">
      <p>支持 JPG、PNG、GIF、WEBP、BMP 格式</p>
      <p>文件大小不超过 2MB</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  memberId: {
    type: Number,
    required: true
  },
  currentAvatar: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update']);

// 数据
const uploading = ref(false);
const avatarUrl = ref(props.currentAvatar);

// 上传地址
const uploadUrl = computed(() => {
  return `http://localhost:8000/api/v1/admin/members/${props.memberId}/avatar/upload/`;
});

// 上传请求头
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`
  };
});

// 上传前验证
const beforeUpload = (file) => {
  // 检查文件类型
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
  const isValidType = validTypes.includes(file.type);
  
  if (!isValidType) {
    ElMessage.error('请上传 JPG、PNG、GIF、WEBP 或 BMP 格式的图片');
    return false;
  }
  
  // 检查文件大小
  const isLt2M = file.size / 1024 / 1024 < 2;
  
  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB');
    return false;
  }
  
  uploading.value = true;
  return true;
};

// 上传成功
const handleSuccess = (response) => {
  uploading.value = false;
  
  if (response.avatar) {
    // 更新头像URL（添加完整域名）
    const fullUrl = `http://localhost:8000${response.avatar}`;
    avatarUrl.value = fullUrl;
    
    ElMessage.success('头像上传成功');
    
    // 通知父组件
    emit('update', response.avatar);
  } else {
    ElMessage.error('上传失败，响应格式错误');
  }
};

// 上传失败
const handleError = (error) => {
  uploading.value = false;
  
  let errorMessage = '上传失败';
  
  if (error.response) {
    const data = JSON.parse(error.message);
    errorMessage = data.detail || errorMessage;
  }
  
  ElMessage.error(errorMessage);
};
</script>

<style scoped>
.avatar-uploader {
  text-align: center;
}

.avatar-preview {
  margin-bottom: 20px;
}

.upload-btn {
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}

.upload-hint p {
  margin: 5px 0;
}
</style>
```

### React示例 (使用Ant Design)

```jsx
import React, { useState } from 'react';
import { Upload, Avatar, message } from 'antd';
import { UserOutlined, UploadOutlined } from '@ant-design/icons';
import axios from 'axios';

const AvatarUploader = ({ memberId, currentAvatar, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(currentAvatar);

  // 上传前验证
  const beforeUpload = (file) => {
    // 检查文件类型
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
      message.error('请上传 JPG、PNG、GIF、WEBP 或 BMP 格式的图片');
      return false;
    }

    // 检查文件大小
    const isLt2M = file.size / 1024 / 1024 < 2;
    if (!isLt2M) {
      message.error('头像大小不能超过 2MB');
      return false;
    }

    return true;
  };

  // 自定义上传
  const customUpload = async ({ file, onSuccess, onError }) => {
    const formData = new FormData();
    formData.append('avatar', file);

    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `/api/v1/admin/members/${memberId}/avatar/upload/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      const newAvatarUrl = `http://localhost:8000${response.data.avatar}`;
      setAvatarUrl(newAvatarUrl);
      onSuccess(response.data);
      message.success('头像上传成功');
      
      if (onUpdate) {
        onUpdate(response.data.avatar);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '上传失败';
      onError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ textAlign: 'center' }}>
      {/* 头像显示 */}
      <div style={{ marginBottom: 20 }}>
        <Avatar
          size={120}
          icon={<UserOutlined />}
          src={avatarUrl}
        />
      </div>

      {/* 上传按钮 */}
      <Upload
        showUploadList={false}
        beforeUpload={beforeUpload}
        customRequest={customUpload}
        accept="image/*"
      >
        <Button icon={<UploadOutlined />} loading={loading}>
          {loading ? '上传中...' : '上传头像'}
        </Button>
      </Upload>

      {/* 提示信息 */}
      <div style={{ fontSize: 12, color: '#999', marginTop: 10 }}>
        <p>支持 JPG、PNG、GIF、WEBP、BMP 格式</p>
        <p>文件大小不超过 2MB</p>
      </div>
    </div>
  );
};

export default AvatarUploader;
```

---

## 前端实现参考

### 头像上传功能清单

- [x] 文件选择
- [x] 文件类型验证
- [x] 文件大小验证
- [x] 上传进度显示
- [x] 预览功能
- [x] 裁剪功能（可选）
- [x] 错误处理
- [x] 成功提示

### 图片裁剪功能

推荐使用图片裁剪库实现头像裁剪：

#### Vue使用vue-cropper

```bash
npm install vue-cropper
```

```vue
<template>
  <el-dialog v-model="cropDialogVisible" title="裁剪头像" width="800px">
    <vue-cropper
      ref="cropper"
      :img="imageSrc"
      :outputSize="1"
      :outputType="'jpeg'"
      :info="true"
      :canScale="true"
      :autoCrop="true"
      :autoCropWidth="200"
      :autoCropHeight="200"
      :fixedBox="false"
      :fixed="true"
      :fixedNumber="[1, 1]"
    />
    
    <template #footer>
      <el-button @click="cropDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmCrop">确定裁剪</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue';
import { VueCropper } from 'vue-cropper';

const cropper = ref(null);
const cropDialogVisible = ref(false);
const imageSrc = ref('');

const confirmCrop = () => {
  cropper.value.getCropBlob((blob) => {
    // 将blob转换为文件并上传
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
    uploadAvatar(file);
  });
};
</script>
```

#### React使用react-image-crop

```bash
npm install react-image-crop
```

```jsx
import React, { useState, useRef } from 'react';
import ReactCrop from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

const ImageCropper = ({ imageSrc, onCropComplete }) => {
  const [crop, setCrop] = useState({ aspect: 1 });
  const imageRef = useRef(null);

  const getCroppedImg = () => {
    const canvas = document.createElement('canvas');
    const image = imageRef.current;
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;
    
    canvas.width = crop.width;
    canvas.height = crop.height;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(
      image,
      crop.x * scaleX,
      crop.y * scaleY,
      crop.width * scaleX,
      crop.height * scaleY,
      0,
      0,
      crop.width,
      crop.height
    );

    canvas.toBlob((blob) => {
      onCropComplete(blob);
    }, 'image/jpeg');
  };

  return (
    <div>
      <ReactCrop
        src={imageSrc}
        crop={crop}
        onChange={setCrop}
        onImageLoaded={(img) => { imageRef.current = img; }}
      />
      <button onClick={getCroppedImg}>确定裁剪</button>
    </div>
  );
};
```

### 头像预览功能

```javascript
// 文件选择后预览
function previewAvatar(file) {
  const reader = new FileReader();
  
  reader.onload = (e) => {
    const previewImg = document.getElementById('avatarPreview');
    previewImg.src = e.target.result;
  };
  
  reader.readAsDataURL(file);
}

// 使用
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    previewAvatar(file);
  }
});
```

### 拖拽上传功能

```vue
<template>
  <div
    class="drop-zone"
    @drop.prevent="handleDrop"
    @dragover.prevent
    @dragenter.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    :class="{ 'is-dragging': isDragging }"
  >
    <div v-if="!avatarUrl" class="drop-zone-content">
      <i class="el-icon-upload"></i>
      <p>将图片拖到此处，或点击上传</p>
    </div>
    <img v-else :src="avatarUrl" class="avatar-img" />
    <input
      type="file"
      ref="fileInput"
      @change="handleFileSelect"
      accept="image/*"
      style="display: none;"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';

const isDragging = ref(false);
const avatarUrl = ref('');
const fileInput = ref(null);

const handleDrop = (e) => {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
};

const handleFileSelect = (e) => {
  const files = e.target.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
};

const handleFile = (file) => {
  // 验证和上传逻辑
  uploadAvatar(file);
};
</script>
```

### 压缩大图片

```javascript
// 压缩图片
function compressImage(file, maxWidth = 800, quality = 0.8) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const img = new Image();
      img.src = e.target.result;
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        // 按比例缩放
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob(
          (blob) => {
            resolve(new File([blob], file.name, { type: 'image/jpeg' }));
          },
          'image/jpeg',
          quality
        );
      };
    };
    
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// 使用
async function uploadWithCompression(file) {
  if (file.size > 1024 * 1024) { // 大于1MB才压缩
    file = await compressImage(file);
  }
  await uploadAvatar(file);
}
```

---

## 技术要点总结

### 1. 文件验证

- **前端验证**：提供即时反馈，提升用户体验
- **后端验证**：确保安全性，防止绕过前端验证

### 2. 错误处理

```javascript
function handleUploadError(error) {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        // 显示具体错误信息
        return data.detail;
      case 403:
        return '权限不足';
      case 404:
        return '用户不存在';
      case 413:
        return '文件太大';
      default:
        return '上传失败';
    }
  }
  return '网络错误';
}
```

### 3. 进度显示

```javascript
axios.post(url, formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`上传进度: ${percentCompleted}%`);
    // 更新进度条
  }
});
```

---

## 完成！

恭喜！您已经阅读完所有Member管理API文档。

### 文档清单

- ✅ README.md - 总览和快速开始
- ✅ member_common.md - 通用说明
- ✅ member_list_create_api.md - 列表和创建API
- ✅ member_detail_api.md - 详情、更新、删除API
- ✅ member_subaccount_api.md - 子账号管理API
- ✅ member_avatar_api.md - 头像上传API

### 后续支持

如有任何疑问，请：
- 查阅Swagger文档：`http://localhost:8000/swagger/`
- 查阅ReDoc文档：`http://localhost:8000/redoc/`
- 联系后端开发团队

祝开发顺利！🎉

