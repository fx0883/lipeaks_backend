# CMS菜单集成指南

本文档介绍如何将CMS模块的菜单配置集成到系统中。

## 菜单结构

CMS模块的菜单结构如下：

```
CMS (主菜单)
├── 文章管理 (ArticleManagement)
│   ├── 创建文章 (ArticleCreate) - 隐藏菜单项
│   ├── 编辑文章 (ArticleEdit) - 隐藏菜单项
│   └── 文章详情 (ArticleDetail) - 隐藏菜单项
├── 评论管理 (CommentManagement)
│   └── 评论详情 (CommentDetail) - 隐藏菜单项
├── 分类管理 (CategoryManagement)
└── 标签管理 (TagManagement)
```

## 方法一：使用Django管理命令加载菜单

我们提供了一个Django管理命令，用于将CMS菜单数据加载到数据库中。这个命令会自动创建所有必要的菜单项及其层级关系。

### 命令用法

```bash
python manage.py load_provided_cms_menus
```

如果菜单已存在，命令将跳过这些菜单。如果需要更新已存在的菜单，可以使用`--force`参数：

```bash
python manage.py load_provided_cms_menus --force
```

### 命令执行过程

1. 解析内置的菜单JSON数据
2. 检查每个菜单项是否已存在
3. 如果菜单不存在，创建新菜单
4. 如果菜单已存在且使用了`--force`参数，更新现有菜单
5. 递归处理所有子菜单

## 方法二：使用Python脚本通过API添加菜单

我们还提供了一个Python脚本，可以通过API调用添加CMS菜单。这种方法适用于需要远程管理菜单的场景。

### 脚本使用方法

1. 确保已安装必要的Python包：
   ```bash
   pip install requests
   ```

2. 修改脚本中的API URL和令牌：
   ```python
   # API配置
   API_URL = "http://your-api-domain/api/v1/menus/"  # 修改为实际的API URL
   TOKEN = "your_jwt_token_here"  # 修改为实际的JWT令牌
   ```

3. 运行脚本：
   ```bash
   python scripts/load_cms_menus_api.py
   ```

### 获取JWT令牌

要获取JWT令牌，可以通过以下API登录：

```
POST /api/v1/auth/login/
{
  "username": "admin",
  "password": "your_password"
}
```

响应中会包含JWT令牌：

```json
{
  "token": "your_jwt_token_here"
}
```

### 菜单字段映射

前端路由配置与后端菜单模型字段的映射关系如下：

| 前端字段 | 后端字段 | 说明 |
|--------|---------|------|
| path | path | 路由路径 |
| name | name | 路由名称 |
| redirect | redirect | 重定向路径 |
| component | component | 组件路径 |
| meta.title | title | 菜单标题 |
| meta.icon | icon | 菜单图标 |
| meta.showLink | show_link | 是否在菜单中显示 |
| meta.showParent | show_parent | 是否显示父级菜单 |
| meta.keepAlive | keep_alive | 是否缓存路由页面 |
| meta.rank | rank | 菜单排序 |
| meta.activePath | active_path | 激活菜单的路径 |

## 方法三：手动添加菜单

除了使用管理命令或API脚本，您还可以通过以下方式手动添加菜单：

1. 使用Django Admin界面
2. 通过直接API调用
3. 创建自定义数据迁移

### 通过Admin界面添加菜单

1. 登录Django Admin界面
2. 导航到"菜单"模型
3. 点击"添加菜单"按钮
4. 填写菜单信息并保存
5. 为子菜单选择正确的父菜单

### 通过直接API调用添加菜单

以下是使用API添加CMS主菜单的示例：

```
POST /api/v1/menus/
{
  "name": "CMS",
  "code": "cms",
  "path": "/cms",
  "redirect": "/cms/article",
  "title": "menus.cmsManagement",
  "icon": "ri:article-line",
  "show_link": true,
  "rank": 5,
  "parent_id": null
}
```

## 菜单权限分配

创建菜单后，您需要将菜单分配给适当的用户或角色。您可以通过以下方式分配菜单：

1. 使用用户菜单API为管理员分配菜单
2. 使用RBAC角色权限系统关联菜单和角色

### 为管理员分配菜单

```
POST /api/v1/menus/admins/{admin_id}/menus/
{
  "menu_ids": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

## 故障排除

如果在加载菜单过程中遇到问题，请检查：

1. 数据库连接是否正常
2. 菜单表结构是否正确
3. 日志文件中的错误信息
4. 权限设置是否正确

如需更多帮助，请参考其他文档或联系技术支持团队。 