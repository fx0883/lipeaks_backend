# 域名配置与应用启动

本文档将指导您在cPanel环境中配置域名和子域名，启动Django应用程序，以及验证应用程序是否正常运行。

## 域名配置

### 主域名配置

如果您计划在主域名上运行Django应用程序：

1. 在cPanel主界面，找到并点击**"域名"**或**"域"**
2. 确认您的主域名已正确设置，并指向`public_html`目录
3. 如果需要，点击**"管理"**或**"编辑"**按钮进行调整

### 子域名配置

如果您计划使用子域名运行Django应用程序（推荐）：

1. 在cPanel主界面，找到并点击**"子域名"**
2. 点击**"创建"**按钮
3. 填写以下信息：
   - **子域名**：输入所需的子域名（例如 `api` 或 `app`）
   - **域名**：从下拉菜单中选择主域名
   - **文档根目录**：指定子域名的根目录（例如 `public_html` 或 `public_html/app`）
4. 点击**"创建"**按钮

### 域名指向项目目录

如果您希望域名直接指向Django项目目录，而不是`public_html`：

1. 在cPanel主界面，找到并点击**"域名指向"**或**"域重定向"**
2. 点击**"添加域名"**按钮
3. 填写以下信息：
   - **域名**：输入域名或子域名
   - **类型**：选择**"指向目录"**
   - **目录**：输入Django项目目录的路径（例如 `/home/username/lipeaks_backend`）
4. 点击**"添加"**按钮

## 配置DNS记录

确保您的域名DNS记录正确指向cPanel服务器：

1. 在cPanel主界面，找到并点击**"区域编辑器"**或**"DNS区域编辑器"**
2. 选择您的域名
3. 确认A记录指向您的服务器IP地址
4. 如果使用子域名，确保子域名也有正确的A记录

如果您的DNS由其他提供商管理，请在其控制面板中进行相应设置。

## 配置SSL证书（HTTPS）

为您的域名配置SSL证书，启用HTTPS：

1. 在cPanel主界面，找到并点击**"SSL/TLS"**或**"SSL/TLS状态"**
2. 找到您的域名，点击**"安装证书"**按钮
3. 如果可用，选择**"Let's Encrypt"**作为证书提供商
4. 选择要保护的域名和子域名
5. 点击**"安装证书"**按钮
6. 等待证书安装完成

### 强制使用HTTPS

配置Django和Web服务器强制使用HTTPS：

1. 在Django的`settings.py`中添加以下设置：

```python
# 安全设置
SECURE_SSL_REDIRECT = True  # 将HTTP请求重定向到HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True  # 仅通过HTTPS发送会话cookie
CSRF_COOKIE_SECURE = True  # 仅通过HTTPS发送CSRF cookie
```

2. 在`public_html/.htaccess`文件中添加以下规则：

```apache
# 强制使用HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

## 启动Django应用程序

在cPanel环境中，Passenger会自动管理Django应用程序的启动和停止。您需要确保Python应用程序已正确配置：

1. 在cPanel主界面，找到并点击**"Setup Python App"**或**"Python"**
2. 确认您的Python应用程序配置正确：
   - **Python版本**：应为3.9+（推荐3.12或更高版本）
   - **应用程序根目录**：应指向Django项目目录
   - **应用程序启动文件**：应为`passenger_wsgi.py`
   - **应用程序入口点**：应为`application`
3. 如果需要，点击**"编辑"**按钮进行调整
4. 点击**"重启"**按钮重启应用程序

## 验证应用程序是否正常运行

### 1. 检查网站可访问性

在浏览器中访问您的域名或子域名，确认网站可以正常访问。

### 2. 检查Django管理界面

访问Django管理界面（通常是 `https://yourdomain.com/admin` 或 `https://api.yourdomain.com/admin`），确认可以正常登录。

### 3. 检查API端点

如果您的项目包含API，测试一些API端点，确认它们正常工作。例如：

```bash
# 使用curl测试API
curl -X GET https://yourdomain.com/api/v1/schema/ -H "Accept: application/json"
```

### 4. 检查日志文件

检查应用程序日志文件，查找可能的错误：

```bash
# 查看最近的日志
tail -n 100 ~/logs/debug.log
tail -n 100 ~/logs/error.log
```

## 配置应用程序监控

### 1. 创建简单的健康检查脚本

创建一个脚本来定期检查应用程序状态：

```bash
# 创建健康检查脚本
cat > ~/health_check.sh << 'EOL'
#!/bin/bash

# 设置变量
SITE_URL="https://yourdomain.com"
LOG_FILE=~/health_check.log
ADMIN_EMAIL="your.email@example.com"

# 检查网站可访问性
check_site() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)
    if [ $HTTP_CODE -eq 200 ]; then
        echo "$(date): 网站正常运行 (HTTP $HTTP_CODE)" >> $LOG_FILE
        return 0
    else
        echo "$(date): 网站返回错误码 HTTP $HTTP_CODE" >> $LOG_FILE
        return 1
    fi
}

# 检查API可用性
check_api() {
    API_URL="$SITE_URL/api/v1/schema/"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    if [ $HTTP_CODE -eq 200 ]; then
        echo "$(date): API正常运行 (HTTP $HTTP_CODE)" >> $LOG_FILE
        return 0
    else
        echo "$(date): API返回错误码 HTTP $HTTP_CODE" >> $LOG_FILE
        return 1
    fi
}

# 检查数据库连接
check_db() {
    cd ~/lipeaks_backend
    source ~/virtualenv/lipeaks_backend/3.12/bin/activate
    DB_CHECK=$(python -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('OK')" 2>&1)
    if [ "$DB_CHECK" = "OK" ]; then
        echo "$(date): 数据库连接正常" >> $LOG_FILE
        return 0
    else
        echo "$(date): 数据库连接失败: $DB_CHECK" >> $LOG_FILE
        return 1
    fi
}

# 执行所有检查
run_checks() {
    SITE_OK=0
    API_OK=0
    DB_OK=0
    
    check_site
    SITE_OK=$?
    
    check_api
    API_OK=$?
    
    check_db
    DB_OK=$?
    
    # 如果任何检查失败，发送电子邮件通知
    if [ $SITE_OK -ne 0 ] || [ $API_OK -ne 0 ] || [ $DB_OK -ne 0 ]; then
        echo "$(date): 检测到问题，发送通知..." >> $LOG_FILE
        mail -s "网站健康检查警报: $SITE_URL" $ADMIN_EMAIL << EOF
网站健康检查发现问题:

网站状态: $([ $SITE_OK -eq 0 ] && echo "正常" || echo "异常")
API状态: $([ $API_OK -eq 0 ] && echo "正常" || echo "异常")
数据库状态: $([ $DB_OK -eq 0 ] && echo "正常" || echo "异常")

请检查服务器日志获取更多信息。
EOF
    fi
}

# 运行检查
run_checks
EOL

# 设置执行权限
chmod +x ~/health_check.sh
```

### 2. 设置定期健康检查

```bash
# 在cPanel中设置cron作业，每10分钟执行一次健康检查
(crontab -l 2>/dev/null; echo "*/10 * * * * ~/health_check.sh") | crontab -
```

## 配置错误页面

为常见HTTP错误创建自定义错误页面：

1. 在项目的`templates`目录中创建错误页面模板：

```bash
# 创建错误页面目录
mkdir -p ~/lipeaks_backend/templates/errors

# 创建404错误页面
cat > ~/lipeaks_backend/templates/errors/404.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>页面未找到 - 404</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f8f9fa;
        }
        .error-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #dc3545;
        }
        .home-link {
            margin-top: 30px;
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404 - 页面未找到</h1>
        <p>抱歉，您请求的页面不存在。</p>
        <p>请检查URL是否正确，或返回首页。</p>
        <a href="/" class="home-link">返回首页</a>
    </div>
</body>
</html>
EOL

# 创建500错误页面
cat > ~/lipeaks_backend/templates/errors/500.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>服务器错误 - 500</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f8f9fa;
        }
        .error-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #dc3545;
        }
        .home-link {
            margin-top: 30px;
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>500 - 服务器错误</h1>
        <p>抱歉，服务器遇到了一个错误。</p>
        <p>我们的技术团队已经收到通知，正在努力解决问题。</p>
        <a href="/" class="home-link">返回首页</a>
    </div>
</body>
</html>
EOL
```

2. 在`settings.py`中配置错误页面：

```python
# 错误页面设置
TEMPLATES = [
    {
        # ... 其他设置 ...
        'OPTIONS': {
            'context_processors': [
                # ... 其他处理器 ...
            ],
        },
    },
]

# 设置自定义错误页面
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
```

3. 在`core/views.py`中添加错误处理视图：

```python
from django.shortcuts import render

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)
```

## 下一步

完成域名配置与应用启动后，您可以继续[性能优化与安全配置](08_optimization_security.md)。 