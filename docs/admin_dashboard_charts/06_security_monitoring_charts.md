# 安全监控图表

## 图表清单

1. **异常登录尝试**：可疑登录行为的地理分布热图
2. **权限变更审计**：用户权限变更操作的趋势图
3. **敏感操作日志**：关键数据修改、删除等操作的统计

## 数据源分析

这些图表的数据主要来源于以下几个方面：

1. **API日志**：
   - `common.APILog`模型中的登录相关记录
   - IP地址、用户代理等信息

2. **操作日志**：
   - `cms.OperationLog`模型中的操作记录
   - 权限变更和敏感操作记录

3. **用户权限变更记录**：
   - 需要实现用户权限变更的审计日志功能
   - 记录权限变更的时间、操作者、变更内容等信息

## API设计

### 1. 异常登录尝试 API

#### 请求

```
GET /api/v1/admin/charts/login-anomalies/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "geo_heatmap",
    "title": "异常登录尝试",
    "description": "可疑登录行为的地理分布",
    "geo_data": [
      {"lat": 40.7128, "lng": -74.0060, "weight": 10, "country": "美国", "city": "纽约", "ip": "203.0.113.1"},
      {"lat": 39.9042, "lng": 116.4074, "weight": 5, "country": "中国", "city": "北京", "ip": "203.0.113.2"},
      {"lat": 51.5074, "lng": -0.1278, "weight": 8, "country": "英国", "city": "伦敦", "ip": "203.0.113.3"}
    ],
    "anomaly_types": [
      {"type": "多地登录", "count": 15},
      {"type": "非常规时间登录", "count": 8},
      {"type": "登录失败次数过多", "count": 12},
      {"type": "未知设备登录", "count": 5}
    ],
    "summary": {
      "total_anomalies": 40,
      "highest_risk_country": "美国",
      "highest_risk_city": "纽约",
      "most_common_anomaly": "多地登录"
    }
  }
}
```

### 2. 权限变更审计 API

#### 请求

```
GET /api/v1/admin/charts/permission-audit/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为daily（日）、weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "stacked_bar",
    "title": "权限变更审计",
    "description": "用户权限变更操作的趋势图",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", "..."],
    "datasets": [
      {
        "label": "角色提升",
        "data": [3, 1, 2, "..."],
        "color": "#F44336"
      },
      {
        "label": "权限添加",
        "data": [5, 4, 3, "..."],
        "color": "#FF9800"
      },
      {
        "label": "权限移除",
        "data": [2, 3, 1, "..."],
        "color": "#2196F3"
      }
    ],
    "summary": {
      "total_changes": 120,
      "role_promotions": 35,
      "permission_additions": 60,
      "permission_removals": 25,
      "most_active_admin": "admin@example.com"
    }
  }
}
```

### 3. 敏感操作日志 API

#### 请求

```
GET /api/v1/admin/charts/sensitive-operations/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为daily（日）、weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "stacked_bar",
    "title": "敏感操作日志",
    "description": "关键数据修改、删除等操作的统计",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", "..."],
    "datasets": [
      {
        "label": "数据删除",
        "data": [2, 0, 1, "..."],
        "color": "#F44336"
      },
      {
        "label": "配置修改",
        "data": [3, 2, 4, "..."],
        "color": "#FF9800"
      },
      {
        "label": "租户操作",
        "data": [1, 0, 2, "..."],
        "color": "#2196F3"
      },
      {
        "label": "用户管理",
        "data": [4, 3, 5, "..."],
        "color": "#4CAF50"
      }
    ],
    "top_operations": [
      {"operation": "删除用户", "count": 15},
      {"operation": "修改系统配置", "count": 12},
      {"operation": "删除租户", "count": 8},
      {"operation": "重置用户密码", "count": 25}
    ],
    "summary": {
      "total_operations": 180,
      "data_deletions": 35,
      "config_changes": 65,
      "tenant_operations": 20,
      "user_management": 60
    }
  }
}
```

## 实现步骤

### 1. 异常登录尝试图表实现

#### 数据查询与处理

1. **登录日志收集**：
   ```python
   def collect_login_anomalies(start_date, end_date):
       # 查询API日志中的登录记录
       login_logs = APILog.objects.filter(
           endpoint__contains="login",
           created_at__range=(start_date, end_date)
       )
       
       # 提取可能异常的登录尝试
       anomalies = []
       for log in login_logs:
           if is_anomalous_login(log):
               anomalies.append(extract_anomaly_data(log))
       
       return anomalies
   ```

2. **异常检测算法**：
   ```python
   def is_anomalous_login(log):
       # 检测多地登录
       if is_multi_location_login(log.user_id, log.ip_address):
           return True
       
       # 检测非常规时间登录
       if is_unusual_time_login(log.user_id, log.created_at):
           return True
       
       # 检测登录失败次数过多
       if is_excessive_failed_login(log.user_id, log.ip_address):
           return True
       
       # 检测未知设备登录
       if is_unknown_device_login(log.user_id, log.user_agent):
           return True
       
       return False
   ```

3. **地理位置解析**：
   ```python
   def extract_anomaly_data(log):
       # 使用IP地址解析地理位置
       geo_data = geolocate_ip(log.ip_address)
       
       return {
           "lat": geo_data["latitude"],
           "lng": geo_data["longitude"],
           "weight": calculate_risk_weight(log),
           "country": geo_data["country"],
           "city": geo_data["city"],
           "ip": log.ip_address,
           "anomaly_type": determine_anomaly_type(log)
       }
   ```

#### API权限控制

```python
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def login_anomalies_chart(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 验证日期格式
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({"code": 400, "message": "无效的日期格式"}, status=400)
    
    # 获取异常登录数据
    anomalies = collect_login_anomalies(start_date, end_date)
    
    # 处理数据并返回图表所需格式
    response_data = format_login_anomalies_response(anomalies)
    
    return Response({"code": 200, "message": "success", "data": response_data})
```

#### 前端实现

1. **使用地图库**：
   ```javascript
   import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
   
   function LoginAnomalyMap({ anomalyData }) {
     return (
       <MapContainer center={[0, 0]} zoom={2} style={{ height: '500px', width: '100%' }}>
         <TileLayer
           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
           attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
         />
         {anomalyData.geo_data.map((point, index) => (
           <CircleMarker
             key={index}
             center={[point.lat, point.lng]}
             radius={Math.sqrt(point.weight) * 3}
             fillOpacity={0.7}
             color="#FF5722"
           >
             <Popup>
               <div>
                 <strong>位置:</strong> {point.city}, {point.country}<br />
                 <strong>IP地址:</strong> {point.ip}<br />
                 <strong>异常类型:</strong> {point.anomaly_type}
               </div>
             </Popup>
           </CircleMarker>
         ))}
       </MapContainer>
     );
   }
   ```

2. **异常类型统计**：
   ```javascript
   import { Pie } from 'react-chartjs-2';
   
   function AnomalyTypesPieChart({ anomalyTypes }) {
     const data = {
       labels: anomalyTypes.map(item => item.type),
       datasets: [
         {
           data: anomalyTypes.map(item => item.count),
           backgroundColor: [
             '#FF5722',
             '#FF9800',
             '#FFC107',
             '#FFEB3B'
           ],
           borderWidth: 1,
         },
       ],
     };
     
     return <Pie data={data} />;
   }
   ```

### 2. 权限变更审计图表实现

#### 数据查询与处理

1. **权限变更记录查询**：
   ```python
   def get_permission_changes(period, start_date, end_date):
       # 根据周期类型确定分组方式
       if period == 'daily':
           trunc_func = TruncDay
       elif period == 'weekly':
           trunc_func = TruncWeek
       else:  # monthly
           trunc_func = TruncMonth
       
       # 查询权限变更记录
       permission_logs = OperationLog.objects.filter(
           operation_type__in=['role_change', 'permission_add', 'permission_remove'],
           created_at__range=(start_date, end_date)
       ).annotate(
           period_date=trunc_func('created_at')
       ).values('period_date', 'operation_type').annotate(
           count=Count('id')
       ).order_by('period_date')
       
       return permission_logs
   ```

2. **数据格式化**：
   ```python
   def format_permission_audit_data(permission_logs, start_date, end_date):
       # 生成日期序列
       date_range = generate_date_range(start_date, end_date)
       
       # 初始化数据集
       role_promotions = [0] * len(date_range)
       permission_additions = [0] * len(date_range)
       permission_removals = [0] * len(date_range)
       
       # 填充数据
       for log in permission_logs:
           index = date_range.index(log['period_date'].strftime('%Y-%m-%d'))
           if log['operation_type'] == 'role_change':
               role_promotions[index] = log['count']
           elif log['operation_type'] == 'permission_add':
               permission_additions[index] = log['count']
           elif log['operation_type'] == 'permission_remove':
               permission_removals[index] = log['count']
       
       return {
           "labels": date_range,
           "datasets": [
               {
                   "label": "角色提升",
                   "data": role_promotions,
                   "color": "#F44336"
               },
               {
                   "label": "权限添加",
                   "data": permission_additions,
                   "color": "#FF9800"
               },
               {
                   "label": "权限移除",
                   "data": permission_removals,
                   "color": "#2196F3"
               }
           ]
       }
   ```

#### API实现

```python
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def permission_audit_chart(request):
    period = request.GET.get('period', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 验证参数
    if period not in ['daily', 'weekly', 'monthly']:
        return Response({"code": 400, "message": "无效的周期参数"}, status=400)
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({"code": 400, "message": "无效的日期格式"}, status=400)
    
    # 获取权限变更数据
    permission_logs = get_permission_changes(period, start_date, end_date)
    
    # 计算摘要数据
    summary = calculate_permission_summary(permission_logs)
    
    # 格式化图表数据
    chart_data = format_permission_audit_data(permission_logs, start_date, end_date)
    
    response_data = {
        "chart_type": "stacked_bar",
        "title": "权限变更审计",
        "description": "用户权限变更操作的趋势图",
        **chart_data,
        "summary": summary
    }
    
    return Response({"code": 200, "message": "success", "data": response_data})
```

#### 前端实现

```javascript
import { Bar } from 'react-chartjs-2';

function PermissionAuditChart({ chartData }) {
  const data = {
    labels: chartData.labels,
    datasets: chartData.datasets.map(dataset => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: dataset.color,
      borderColor: dataset.color,
      borderWidth: 1,
    })),
  };
  
  const options = {
    scales: {
      x: {
        stacked: true,
      },
      y: {
        stacked: true,
        beginAtZero: true,
      },
    },
    plugins: {
      tooltip: {
        callbacks: {
          footer: (tooltipItems) => {
            const item = tooltipItems[0];
            const index = item.dataIndex;
            const total = tooltipItems.reduce((sum, ti) => sum + ti.parsed.y, 0);
            return `总变更: ${total}`;
          },
        },
      },
    },
  };
  
  return <Bar data={data} options={options} />;
}
```

### 3. 敏感操作日志图表实现

#### 数据查询与处理

1. **敏感操作记录查询**：
   ```python
   def get_sensitive_operations(period, start_date, end_date):
       # 根据周期类型确定分组方式
       if period == 'daily':
           trunc_func = TruncDay
       elif period == 'weekly':
           trunc_func = TruncWeek
       else:  # monthly
           trunc_func = TruncMonth
       
       # 查询敏感操作记录
       sensitive_ops = OperationLog.objects.filter(
           operation_type__in=['data_delete', 'config_change', 'tenant_operation', 'user_management'],
           created_at__range=(start_date, end_date)
       ).annotate(
           period_date=trunc_func('created_at')
       ).values('period_date', 'operation_type').annotate(
           count=Count('id')
       ).order_by('period_date')
       
       # 获取排名前列的具体操作
       top_operations = OperationLog.objects.filter(
           created_at__range=(start_date, end_date)
       ).values('operation_detail').annotate(
           count=Count('id')
       ).order_by('-count')[:5]
       
       return sensitive_ops, top_operations
   ```

2. **数据格式化**：
   ```python
   def format_sensitive_operations_data(sensitive_ops, top_operations, start_date, end_date):
       # 生成日期序列
       date_range = generate_date_range(start_date, end_date)
       
       # 初始化数据集
       data_deletions = [0] * len(date_range)
       config_changes = [0] * len(date_range)
       tenant_operations = [0] * len(date_range)
       user_management = [0] * len(date_range)
       
       # 填充数据
       for op in sensitive_ops:
           index = date_range.index(op['period_date'].strftime('%Y-%m-%d'))
           if op['operation_type'] == 'data_delete':
               data_deletions[index] = op['count']
           elif op['operation_type'] == 'config_change':
               config_changes[index] = op['count']
           elif op['operation_type'] == 'tenant_operation':
               tenant_operations[index] = op['count']
           elif op['operation_type'] == 'user_management':
               user_management[index] = op['count']
       
       # 格式化排名前列的操作
       formatted_top_ops = [
           {"operation": op['operation_detail'], "count": op['count']}
           for op in top_operations
       ]
       
       return {
           "labels": date_range,
           "datasets": [
               {
                   "label": "数据删除",
                   "data": data_deletions,
                   "color": "#F44336"
               },
               {
                   "label": "配置修改",
                   "data": config_changes,
                   "color": "#FF9800"
               },
               {
                   "label": "租户操作",
                   "data": tenant_operations,
                   "color": "#2196F3"
               },
               {
                   "label": "用户管理",
                   "data": user_management,
                   "color": "#4CAF50"
               }
           ],
           "top_operations": formatted_top_ops
       }
   ```

#### API实现

```python
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def sensitive_operations_chart(request):
    period = request.GET.get('period', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 验证参数
    if period not in ['daily', 'weekly', 'monthly']:
        return Response({"code": 400, "message": "无效的周期参数"}, status=400)
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({"code": 400, "message": "无效的日期格式"}, status=400)
    
    # 获取敏感操作数据
    sensitive_ops, top_operations = get_sensitive_operations(period, start_date, end_date)
    
    # 计算摘要数据
    summary = calculate_operations_summary(sensitive_ops)
    
    # 格式化图表数据
    chart_data = format_sensitive_operations_data(sensitive_ops, top_operations, start_date, end_date)
    
    response_data = {
        "chart_type": "stacked_bar",
        "title": "敏感操作日志",
        "description": "关键数据修改、删除等操作的统计",
        **chart_data,
        "summary": summary
    }
    
    return Response({"code": 200, "message": "success", "data": response_data})
```

#### 前端实现

1. **堆叠柱状图**：
   ```javascript
   import { Bar } from 'react-chartjs-2';
   
   function SensitiveOperationsChart({ chartData }) {
     const data = {
       labels: chartData.labels,
       datasets: chartData.datasets.map(dataset => ({
         label: dataset.label,
         data: dataset.data,
         backgroundColor: dataset.color,
         borderColor: dataset.color,
         borderWidth: 1,
       })),
     };
     
     const options = {
       scales: {
         x: {
           stacked: true,
         },
         y: {
           stacked: true,
           beginAtZero: true,
         },
       },
     };
     
     return <Bar data={data} options={options} />;
   }
   ```

2. **排名前列的操作**：
   ```javascript
   function TopOperationsList({ topOperations }) {
     return (
       <div className="top-operations">
         <h4>排名前列的敏感操作</h4>
         <ul className="operation-list">
           {topOperations.map((op, index) => (
             <li key={index} className="operation-item">
               <span className="operation-name">{op.operation}</span>
               <span className="operation-count">{op.count}</span>
             </li>
           ))}
         </ul>
       </div>
     );
   }
   ```

## 注意事项

### 1. 数据安全与隐私

1. **数据脱敏**：
   - 在展示IP地址、用户名等敏感信息时进行适当脱敏处理
   - 对于超级管理员以外的角色，应进一步限制可见的敏感信息

2. **访问控制**：
   - 严格限制安全监控图表的访问权限，仅对超级管理员和安全管理员开放
   - 对不同级别的管理员可能需要展示不同粒度的安全信息

3. **数据传输安全**：
   - 确保所有安全相关的API调用使用HTTPS加密传输
   - 考虑对特别敏感的数据使用额外的加密措施

### 2. 性能优化

1. **数据聚合**：
   - 对于大量的日志数据，应在数据库层面进行预聚合
   - 考虑使用定时任务生成安全报告摘要，减少实时查询压力

2. **缓存策略**：
   - 对于变化不频繁的安全数据，可以适当增加缓存时间
   - 为不同的图表设置不同的缓存过期时间，例如：
     ```python
     @cache_page(60 * 15)  # 缓存15分钟
     def login_anomalies_chart(request):
         # 实现代码
     ```

3. **分页加载**：
   - 对于详细的安全日志，采用分页加载方式
   - 提供筛选和搜索功能，帮助管理员快速定位特定的安全事件

### 3. 告警机制

1. **实时告警**：
   - 对于严重的安全异常，如多次失败登录尝试，应实现实时告警机制
   - 可以通过邮件、短信或系统内通知等方式通知管理员

2. **阈值设置**：
   - 允许管理员自定义安全告警的阈值
   - 针对不同类型的安全事件设置不同的告警级别

3. **告警聚合**：
   - 避免频繁的重复告警造成"告警疲劳"
   - 实现告警聚合和抑制机制，确保管理员能关注到真正重要的安全事件

### 4. 可扩展性

1. **支持自定义安全指标**：
   - 设计灵活的架构，允许未来添加新的安全监控指标
   - 提供自定义安全报表功能

2. **与第三方安全工具集成**：
   - 预留接口，支持与常见的安全监控工具集成
   - 考虑支持导出安全数据到SIEM系统

3. **历史数据归档**：
   - 实现安全日志的归档策略，平衡存储成本和合规需求
   - 提供历史安全数据的检索和分析功能 