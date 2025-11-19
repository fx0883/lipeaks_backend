#!/bin/bash

# 测试图片上传并生成缩略图API
# 使用方法: ./test_api_upload.sh YOUR_JWT_TOKEN

if [ -z "$1" ]; then
    echo "错误: 请提供JWT令牌"
    echo "使用方法: ./test_api_upload.sh YOUR_JWT_TOKEN"
    exit 1
fi

JWT_TOKEN="$1"
IMAGE_PATH="users/tests/vedio_s.png"

if [ ! -f "$IMAGE_PATH" ]; then
    echo "错误: 测试图片不存在: $IMAGE_PATH"
    exit 1
fi

echo "=========================================="
echo "测试图片上传并生成缩略图API"
echo "=========================================="
echo "图片路径: $IMAGE_PATH"
echo "文件大小: $(ls -lh $IMAGE_PATH | awk '{print $5}')"
echo ""

curl -X 'POST' \
  'http://localhost:8000/api/v1/common/upload-image-with-thumbnail/' \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H 'Content-Type: multipart/form-data' \
  -F "file=@$IMAGE_PATH" \
  -F 'folder=test_uploads' \
  -w "\n\nHTTP状态码: %{http_code}\n" \
  | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
