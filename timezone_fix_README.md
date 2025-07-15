# MySQL时区问题解决方案

## 问题描述

在调用活跃用户统计API时出现以下错误：

```
"获取数据出错: Database returned an invalid datetime value. Are time zone definitions for your database installed?"
```

这个错误表明MySQL数据库的时区表未正确配置，导致无法处理带时区的日期时间值。

## 解决方案

我们提供了三种解决方案，按照推荐顺序排列：

### 方案1：修改代码，不依赖数据库时区功能

我们已经修改了`charts/utils.py`中的`get_active_users`函数，使其不再依赖数据库的时区功能，而是在Python代码中处理时区转换。这是最简单的解决方案，无需修改数据库配置。

**优点**：
- 无需修改数据库配置
- 无需重启数据库
- 立即生效

**缺点**：
- 只解决了活跃用户统计API的问题，其他使用时区的功能可能仍然存在问题
- 性能可能略低（但影响很小）

### 方案2：配置MySQL时区设置

使用`fix_mysql_timezone.sql`脚本或`update_mysql_config.py`工具来配置MySQL的时区设置。

#### 使用SQL脚本设置时区

1. 连接到MySQL：
   ```
   mysql -u root -p
   ```

2. 执行SQL脚本：
   ```
   source fix_mysql_timezone.sql
   ```

**注意**：这种方式设置的时区在MySQL重启后会恢复为默认值。

#### 使用配置工具永久设置时区

运行`update_mysql_config.py`脚本，它会自动查找MySQL配置文件并添加时区设置：

```
python update_mysql_config.py
```

然后按照提示重启MySQL服务。

### 方案3：安装MySQL时区表

如果上述方案不起作用，可能需要安装MySQL的时区表：

#### Linux系统

```bash
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql
```

#### Windows系统

1. 下载时区数据文件：https://dev.mysql.com/downloads/timezones.html
2. 导入时区数据：
   ```
   mysql -u root -p mysql < timezone_posix.sql
   ```

## 推荐操作步骤

1. 首先应用方案1，修改代码不依赖数据库时区功能
2. 如果其他功能也有类似问题，应用方案2永久设置MySQL时区
3. 如果问题仍然存在，应用方案3安装MySQL时区表

## 测试验证

修改完成后，请再次调用活跃用户统计API进行验证：

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/admin/charts/active-users/?period=daily' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

如果返回正常数据，则问题已解决。 