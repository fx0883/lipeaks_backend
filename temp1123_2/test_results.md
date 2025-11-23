# CMS API 测试结果

测试时间: Sun Nov 23 20:19:29 CST 2025

## ✗ 获取文章列表(匿名)
- **方法**: GET
- **端点**: /articles/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✓ 获取文章列表(Admin)
- **方法**: GET
- **端点**: /articles/
- **状态码**: 200

## ✗ 获取文章列表(Member)
- **方法**: GET
- **端点**: /articles/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4100,"message":"Tenant operation failed","data":null,"error_code":"TENANT_ERROR"} 400```

## ✓ 创建文章(Admin)
- **方法**: POST
- **端点**: /articles/
- **状态码**: 201

## ✗ 获取分类列表
- **方法**: GET
- **端点**: /categories/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 创建分类
- **方法**: POST
- **端点**: /categories/
- **状态码**: 400
- **错误**: ```{"success":false,"code":4000,"message":"数据验证失败","data":{"translations":["该字段是必填项。"]},"error_code":"VALIDATION_ERROR"}```

## ✗ 获取分类树
- **方法**: GET
- **端点**: /categories/tree/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 获取标签列表
- **方法**: GET
- **端点**: /tags/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 创建标签
- **方法**: POST
- **端点**: /tags/
- **状态码**: 400
- **错误**: ```{"success":false,"code":4000,"message":"数据验证失败","data":{"slug":["具有 URL别名 的 标签 已存在。"]},"error_code":"VALIDATION_ERROR"}```

## ✗ 获取标签使用统计
- **方法**: GET
- **端点**: /tags/usage-stats/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 获取标签组列表
- **方法**: GET
- **端点**: /tag-groups/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 创建标签组
- **方法**: POST
- **端点**: /tag-groups/
- **状态码**: 400
- **错误**: ```{"success":false,"code":4000,"message":"数据验证失败","data":{"slug":["具有 URL别名 的 标签组 已存在。"]},"error_code":"VALIDATION_ERROR"}```

## ✗ 获取评论列表
- **方法**: GET
- **端点**: /comments/
- **状态码**: 000
- **错误**: ```{"success": false, "code": 4001, "message": "\u672a\u63d0\u4f9b\u79df\u6237ID\uff0c\u65e0\u6cd5\u8bbf\u95eeCMS\u8d44\u6e90", "data": null} 400```

## ✗ 批量处理评论
- **方法**: POST
- **端点**: /comments/batch/
- **状态码**: 400
- **错误**: ```{"success":false,"code":4000,"message":"未提供要处理的评论ID","data":{}}```

## ✗ Member获取文章列表
- **方法**: GET
- **端点**: /member/articles/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4100,"message":"Tenant operation failed","data":null,"error_code":"TENANT_ERROR"} 400```

## ✗ Member创建文章
- **方法**: POST
- **端点**: /member/articles/
- **状态码**: 000
- **错误**: ```{"success":true,"code":2000,"message":"操作成功","data":{"id":10296,"title":"Member测试文章2","content":"Member内容2","content_type":"markdown","excerpt":"Member摘要2","status":"draft","is_featured":false,"is_pinned":false,"allow_comment":true,"visibility":"public","password":null,"cover```

## ✗ Member获取单篇文章
- **方法**: GET
- **端点**: /member/articles/10295/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4100,"message":"Tenant operation failed","data":null,"error_code":"TENANT_ERROR"} 400```

## ✗ Member更新文章(PUT)
- **方法**: PUT
- **端点**: /member/articles/10295/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4003,"message":"您没有执行该操作的权限。","data":null,"error_code":"AUTH_PERMISSION_DENIED"} 403```

## ✗ Member部分更新文章(PATCH)
- **方法**: PATCH
- **端点**: /member/articles/10295/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4003,"message":"您没有执行该操作的权限。","data":null,"error_code":"AUTH_PERMISSION_DENIED"} 403```

## ✗ Member发布文章
- **方法**: POST
- **端点**: /member/articles/10295/publish/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4100,"message":"Tenant operation failed","data":null,"error_code":"TENANT_ERROR"} 400```

## ✗ Member获取文章统计
- **方法**: GET
- **端点**: /member/articles/10295/statistics/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4100,"message":"Tenant operation failed","data":null,"error_code":"TENANT_ERROR"} 400```

## ✗ Member删除文章
- **方法**: DELETE
- **端点**: /member/articles/10295/
- **状态码**: 000
- **错误**: ```{"success":false,"code":4003,"message":"您没有执行该操作的权限。","data":null,"error_code":"AUTH_PERMISSION_DENIED"} 403```


---

## 测试总结
- **总计**: 22
- **通过**: 2
- **失败**: 20
- **成功率**: % - **成功率**: %
