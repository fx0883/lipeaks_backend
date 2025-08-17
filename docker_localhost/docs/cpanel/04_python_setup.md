# 配置Python环境

本文档将指导您在cPanel环境中配置Python环境，包括创建Python应用程序、设置虚拟环境和安装项目依赖。

## 创建Python应用程序

首先，需要在cPanel中创建一个Python应用程序：

1. 在cPanel主界面，找到并点击**"Setup Python App"**或**"Python"**（在"软件"部分）
2. 点击**"Create Application"**或**"创建应用程序"**按钮
3. 填写以下信息：
   - **Python版本**：选择Python 3.9+（推荐3.12或更高版本，根据可用选项）
   - **应用程序根目录**：指定项目目录路径（例如 `/home/username/lipeaks_backend`）
   - **应用程序URL**：输入应用程序的URL（例如 `https://yourdomain.com` 或 `https://yourdomain.com/app`）
   - **应用程序启动文件**：输入 `passenger_wsgi.py`
   - **应用程序入口点**：输入 `application`
4. 点击**"创建"**按钮

## 激活虚拟环境

cPanel会为您的Python应用程序创建一个虚拟环境。您需要激活此虚拟环境以安装依赖和执行命令：

### 使用SSH（推荐）

如果您有SSH访问权限，可以使用以下命令激活虚拟环境：

```bash
# 激活虚拟环境（路径可能因cPanel配置而异）
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 验证Python版本
python --version

# 验证pip版本
pip --version

# 切换到项目目录
cd ~/lipeaks_backend
```

### 使用cPanel终端

如果您没有SSH访问权限，但cPanel提供终端功能：

1. 在cPanel主界面，找到并点击**"Terminal"**或**"终端"**
2. 使用上述命令激活虚拟环境

## 安装项目依赖

激活虚拟环境后，安装项目所需的依赖：

```bash
# 确保pip是最新版本
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 处理依赖安装错误

在cPanel环境中，某些需要编译的包可能会安装失败。以下是一些常见问题的解决方案：

#### 1. mysqlclient安装失败

如果`mysqlclient`安装失败，可以使用纯Python实现的`PyMySQL`代替：

```bash
# 安装PyMySQL
pip install pymysql

# 确保项目已配置使用PyMySQL（在core/__init__.py或settings.py中）
# import pymysql
# pymysql.install_as_MySQLdb()
```

#### 2. 其他编译错误

对于其他需要编译的包，尝试以下方法：

```bash
# 安装wheel以使用预编译包
pip install wheel

# 尝试使用--no-binary选项
pip install --no-binary :all: package_name
```

#### 3. 使用备选包

如果某个包无法安装，查找功能类似的纯Python替代包：

| 原始包 | 替代包 |
|-------|--------|
| mysqlclient | PyMySQL |
| psycopg2 | psycopg2-binary |
| lxml | html5lib |
| Pillow | pillow-simd |

## 验证Python环境

安装依赖后，验证Python环境是否正确配置：

```bash
# 验证Django安装
python -m django --version

# 验证可以导入关键模块
python -c "import django; import pymysql; import dotenv; print('所有模块导入成功')"
```

## 配置Python应用程序设置

根据需要，调整Python应用程序的设置：

### 1. 应用程序内存限制

如果您的应用程序需要更多内存，可以在cPanel中调整Python应用程序的内存限制：

1. 在cPanel主界面，找到并点击**"Setup Python App"**或**"Python"**
2. 找到您的应用程序，点击**"编辑"**
3. 调整内存限制设置（如果可用）
4. 保存更改

### 2. 环境变量

在虚拟环境的激活脚本中添加环境变量：

```bash
# 编辑虚拟环境激活脚本
nano ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 在文件末尾添加环境变量
export DJANGO_SETTINGS_MODULE="core.settings"
export PYTHONPATH="/home/username/lipeaks_backend"
export PYTHONUNBUFFERED=1
```

### 3. 自定义Python路径

如果需要，可以在`passenger_wsgi.py`中自定义Python路径：

```python
VIRTUALENV_PATH = '/home/username/virtualenv/lipeaks_backend/3.12/lib/python3.12/site-packages'
if VIRTUALENV_PATH not in sys.path:
    sys.path.insert(0, VIRTUALENV_PATH)
```

## 创建自定义启动脚本（可选）

为了简化常用操作，可以创建一个自定义启动脚本：

```bash
# 创建启动脚本
cat > ~/start_django.sh << 'EOL'
#!/bin/bash
source ~/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend
exec "$@"
EOL

# 设置执行权限
chmod +x ~/start_django.sh
```

使用此脚本执行Django命令：

```bash
# 执行Django命令
~/start_django.sh python manage.py check
```

## 解决常见Python环境问题

### 1. 模块未找到错误

如果遇到"模块未找到"错误，检查以下几点：

1. 确认依赖已正确安装：
   ```bash
   pip list | grep module_name
   ```

2. 检查Python路径：
   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. 尝试重新安装依赖：
   ```bash
   pip install --force-reinstall module_name
   ```

### 2. 权限错误

如果遇到权限错误，检查文件和目录权限：

```bash
# 检查项目目录权限
ls -la ~/lipeaks_backend

# 如果需要，调整权限
chmod -R u+rwX ~/lipeaks_backend
```

### 3. 内存错误

如果应用程序因内存不足而崩溃，尝试以下方法：

1. 优化代码以减少内存使用
2. 在cPanel中增加Python应用程序的内存限制（如果可用）
3. 联系主机提供商，询问是否可以增加账户的内存限制

## 下一步

完成Python环境配置后，您可以继续[数据库配置与迁移](05_database_setup.md)。 