# 反馈统计分析 API 文档

## 概述

反馈统计API提供全面的数据分析功能，包括反馈趋势、类型分布、状态统计、热门反馈等。

---

## 获取反馈统计数据

### 基本信息
- **接口**: `GET /api/v1/feedbacks/statistics/`
- **权限**: 仅管理员
- **说明**: 
  - 提供comprehensive的反馈统计数据
  - 支持时间范围过滤
  - 支持按应用过滤
  - 用于数据分析和决策支持

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| software | int | 否 | 按应用ID过滤 | 1 |
| date_from | date | 否 | 开始日期 | 2025-11-01 |
| date_to | date | 否 | 结束日期 | 2025-11-30 |

### 响应字段说明

#### 汇总统计 (summary)
| 字段 | 类型 | 说明 |
|------|------|------|
| total_feedbacks | int | 总反馈数 |
| total_users | int | 提交用户数 |
| total_votes | int | 总投票数 |
| total_replies | int | 总回复数 |
| avg_response_time | float | 平均响应时间（小时） |
| resolution_rate | float | 解决率（%） |

#### 反馈类型分布 (by_type)
按反馈类型统计数量。

#### 状态分布 (by_status)
按当前状态统计数量。

#### 优先级分布 (by_priority)
按优先级统计数量。

#### 热门反馈 (most_voted)
投票最多的前10个反馈。

#### 最新反馈 (recent_feedbacks)
最近创建的10个反馈。

#### 每日趋势 (daily_trend)
按天统计反馈数量。

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "summary": {
            "total_feedbacks": 26,
            "total_users": 5,
            "total_votes": 8,
            "total_replies": 35,
            "avg_response_time": 2.5,
            "resolution_rate": 38.5
        },
        "by_type": [
            {"feedback_type": "bug", "count": 18, "percentage": 69.2},
            {"feedback_type": "feature", "count": 4, "percentage": 15.4},
            {"feedback_type": "improvement", "count": 2, "percentage": 7.7},
            {"feedback_type": "question", "count": 1, "percentage": 3.8},
            {"feedback_type": "other", "count": 1, "percentage": 3.8}
        ],
        "by_status": [
            {"status": "submitted", "count": 24, "percentage": 92.3},
            {"status": "reviewing", "count": 1, "percentage": 3.8},
            {"status": "resolved", "count": 1, "percentage": 3.8}
        ],
        "by_priority": [
            {"priority": "medium", "count": 20, "percentage": 76.9},
            {"priority": "high", "count": 4, "percentage": 15.4},
            {"priority": "low", "count": 1, "percentage": 3.8},
            {"priority": "critical", "count": 1, "percentage": 3.8}
        ],
        "most_voted": [
            {
                "id": 2,
                "title": "登录功能问题",
                "vote_count": 5,
                "status": "submitted",
                "created_at": "2025-10-24T09:39:02Z"
            },
            {
                "id": 1,
                "title": "页面加载缓慢",
                "vote_count": 3,
                "status": "reviewing",
                "created_at": "2025-10-24T08:30:24Z"
            }
        ],
        "recent_feedbacks": [
            {
                "id": 27,
                "title": "Test Feedback for Testing Fixed APIs",
                "description": "Testing all fixed APIs",
                "feedback_type": "bug",
                "priority": "high",
                "status": "submitted",
                "application": null,
                "submitter": {
                    "name": "admin_cms",
                    "email": "admin@example.com"
                },
                "vote_count": 0,
                "reply_count": 0,
                "created_at": "2025-11-23T13:46:47Z",
                "updated_at": "2025-11-23T13:46:47Z"
            }
        ],
        "daily_trend": [
            {"date": "2025-10-24", "count": 2},
            {"date": "2025-10-25", "count": 18},
            {"date": "2025-11-20", "count": 2},
            {"date": "2025-11-21", "count": 3},
            {"date": "2025-11-23", "count": 1}
        ]
    }
}
```

### curl 示例

```bash
# 获取所有统计数据
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool

# 按时间范围过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/?date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool

# 按应用过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/?software=1" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool

# 组合过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/?software=1&date_from=2025-11-01" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool
```

---

## 数据分析场景

### 场景1：生成月度报告

```bash
#!/bin/bash
# monthly_report.sh - 生成月度反馈报告

TOKEN="YOUR_TOKEN"
YEAR=$(date +%Y)
MONTH=$(date +%m)

# 计算月份范围
DATE_FROM="${YEAR}-${MONTH}-01"
DATE_TO=$(date -d "${DATE_FROM} +1 month -1 day" +%Y-%m-%d)

echo "生成 ${YEAR}年${MONTH}月 反馈统计报告"
echo "=================================="

# 获取统计数据
STATS=$(curl -s -X GET \
  "http://localhost:8000/api/v1/feedbacks/statistics/?date_from=${DATE_FROM}&date_to=${DATE_TO}" \
  -H "Authorization: Bearer ${TOKEN}")

# 提取关键指标
TOTAL=$(echo $STATS | jq -r '.data.summary.total_feedbacks')
USERS=$(echo $STATS | jq -r '.data.summary.total_users')
VOTES=$(echo $STATS | jq -r '.data.summary.total_votes')
RESOLUTION=$(echo $STATS | jq -r '.data.summary.resolution_rate')

echo ""
echo "📊 总体概况"
echo "  • 总反馈数: $TOTAL"
echo "  • 活跃用户: $USERS"
echo "  • 总投票数: $VOTES"
echo "  • 解决率: ${RESOLUTION}%"

echo ""
echo "📈 反馈类型分布"
echo $STATS | jq -r '.data.by_type[] | "  • \(.feedback_type): \(.count) (\(.percentage)%)"'

echo ""
echo "📋 状态分布"
echo $STATS | jq -r '.data.by_status[] | "  • \(.status): \(.count) (\(.percentage)%)"'

echo ""
echo "⭐ 热门反馈 (Top 5)"
echo $STATS | jq -r '.data.most_voted[0:5][] | "  • [\(.vote_count)票] \(.title)"'

# 保存完整报告
echo $STATS | jq '.' > "feedback_report_${YEAR}${MONTH}.json"
echo ""
echo "完整报告已保存到: feedback_report_${YEAR}${MONTH}.json"
```

### 场景2：趋势分析

```bash
#!/bin/bash
# trend_analysis.sh - 分析反馈趋势

TOKEN="YOUR_TOKEN"

echo "反馈趋势分析"
echo "============"

# 获取最近30天的数据
DATE_FROM=$(date -d '30 days ago' +%Y-%m-%d)
DATE_TO=$(date +%Y-%m-%d)

STATS=$(curl -s -X GET \
  "http://localhost:8000/api/v1/feedbacks/statistics/?date_from=${DATE_FROM}&date_to=${DATE_TO}" \
  -H "Authorization: Bearer ${TOKEN}")

# 分析每日趋势
echo ""
echo "📈 每日新增反馈趋势"
echo $STATS | jq -r '.data.daily_trend[] | "\(.date): \(.count) 个"'

# 计算平均值
AVG=$(echo $STATS | jq '.data.daily_trend | map(.count) | add / length')
echo ""
echo "日均新增: ${AVG} 个"

# 识别峰值
PEAK=$(echo $STATS | jq -r '.data.daily_trend | max_by(.count) | "\(.date) (\(.count)个)"')
echo "峰值日期: $PEAK"
```

### 场景3：问题优先级分析

```bash
#!/bin/bash
# priority_analysis.sh - 优先级分析

TOKEN="YOUR_TOKEN"

echo "反馈优先级分析"
echo "=============="

STATS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer ${TOKEN}")

echo ""
echo "按优先级统计:"
echo $STATS | jq -r '.data.by_priority[] | "  \(.priority | ascii_upcase): \(.count) (\(.percentage)%)"'

# 计算高优先级占比
HIGH_PRIO=$(echo $STATS | jq '.data.by_priority | map(select(.priority == "critical" or .priority == "high")) | map(.count) | add')
TOTAL=$(echo $STATS | jq '.data.summary.total_feedbacks')
HIGH_PRIO_PERCENT=$(echo "scale=2; $HIGH_PRIO * 100 / $TOTAL" | bc)

echo ""
echo "⚠️  高优先级(Critical + High): $HIGH_PRIO ($HIGH_PRIO_PERCENT%)"

if (( $(echo "$HIGH_PRIO_PERCENT > 30" | bc -l) )); then
  echo "⚠️  警告: 高优先级反馈占比过高，需要优先处理！"
fi
```

### 场景4：用户活跃度分析

```bash
#!/bin/bash
# user_activity.sh - 用户活跃度分析

TOKEN="YOUR_TOKEN"

echo "用户活跃度分析"
echo "=============="

STATS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer ${TOKEN}")

TOTAL_FEEDBACKS=$(echo $STATS | jq -r '.data.summary.total_feedbacks')
TOTAL_USERS=$(echo $STATS | jq -r '.data.summary.total_users')

if [ "$TOTAL_USERS" -gt 0 ]; then
  AVG_PER_USER=$(echo "scale=2; $TOTAL_FEEDBACKS / $TOTAL_USERS" | bc)
  echo "活跃用户数: $TOTAL_USERS"
  echo "总反馈数: $TOTAL_FEEDBACKS"
  echo "人均反馈: $AVG_PER_USER 个"
else
  echo "暂无用户反馈数据"
fi
```

---

## 数据可视化

### 生成CSV报告

```bash
#!/bin/bash
# export_csv.sh - 导出CSV格式统计报告

TOKEN="YOUR_TOKEN"
OUTPUT="feedback_stats_$(date +%Y%m%d).csv"

STATS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer ${TOKEN}")

# 导出类型分布
echo "反馈类型统计" > $OUTPUT
echo "类型,数量,百分比" >> $OUTPUT
echo $STATS | jq -r '.data.by_type[] | "\(.feedback_type),\(.count),\(.percentage)%"' >> $OUTPUT

echo "" >> $OUTPUT
echo "状态分布统计" >> $OUTPUT
echo "状态,数量,百分比" >> $OUTPUT
echo $STATS | jq -r '.data.by_status[] | "\(.status),\(.count),\(.percentage)%"' >> $OUTPUT

echo "" >> $OUTPUT
echo "优先级统计" >> $OUTPUT
echo "优先级,数量,百分比" >> $OUTPUT
echo $STATS | jq -r '.data.by_priority[] | "\(.priority),\(.count),\(.percentage)%"' >> $OUTPUT

echo "" >> $OUTPUT
echo "每日趋势" >> $OUTPUT
echo "日期,数量" >> $OUTPUT
echo $STATS | jq -r '.data.daily_trend[] | "\(.date),\(.count)"' >> $OUTPUT

echo "CSV报告已导出到: $OUTPUT"
```

### 使用Python绘图

```python
# plot_statistics.py - 使用Python绘制统计图表
import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

TOKEN = "YOUR_TOKEN"

# 获取统计数据
response = requests.get(
    'http://localhost:8000/api/v1/feedbacks/statistics/',
    headers={'Authorization': f'Bearer {TOKEN}'}
)
data = response.json()['data']

# 1. 反馈类型饼图
type_data = pd.DataFrame(data['by_type'])
plt.figure(figsize=(10, 6))
plt.pie(type_data['count'], labels=type_data['feedback_type'], autopct='%1.1f%%')
plt.title('反馈类型分布')
plt.savefig('feedback_types.png')

# 2. 每日趋势折线图
trend_data = pd.DataFrame(data['daily_trend'])
trend_data['date'] = pd.to_datetime(trend_data['date'])
plt.figure(figsize=(12, 6))
plt.plot(trend_data['date'], trend_data['count'], marker='o')
plt.xlabel('日期')
plt.ylabel('反馈数')
plt.title('反馈每日趋势')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('feedback_trend.png')

# 3. 状态分布柱状图
status_data = pd.DataFrame(data['by_status'])
plt.figure(figsize=(10, 6))
plt.bar(status_data['status'], status_data['count'])
plt.xlabel('状态')
plt.ylabel('数量')
plt.title('反馈状态分布')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('feedback_status.png')

print("图表已生成!")
print("- feedback_types.png")
print("- feedback_trend.png")
print("- feedback_status.png")
```

---

## 告警规则

### 基于统计数据的告警

```bash
#!/bin/bash
# alerts.sh - 基于统计数据的智能告警

TOKEN="YOUR_TOKEN"

STATS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer ${TOKEN}")

# 1. 检查未处理反馈数量
SUBMITTED=$(echo $STATS | jq '.data.by_status[] | select(.status == "submitted") | .count')
if [ "$SUBMITTED" -gt 50 ]; then
  echo "⚠️  告警: 未处理反馈过多 ($SUBMITTED 个)"
  send_alert "未处理反馈过多"
fi

# 2. 检查关键问题占比
CRITICAL=$(echo $STATS | jq '.data.by_priority[] | select(.priority == "critical") | .count // 0')
if [ "$CRITICAL" -gt 5 ]; then
  echo "🚨 紧急: 严重问题过多 ($CRITICAL 个)"
  send_urgent_alert "严重问题需要立即处理"
fi

# 3. 检查解决率
RESOLUTION=$(echo $STATS | jq -r '.data.summary.resolution_rate')
if (( $(echo "$RESOLUTION < 30" | bc -l) )); then
  echo "⚠️  告警: 解决率过低 (${RESOLUTION}%)"
  send_alert "反馈解决率低于30%"
fi

# 4. 检查响应时间
AVG_RESPONSE=$(echo $STATS | jq -r '.data.summary.avg_response_time // 0')
if (( $(echo "$AVG_RESPONSE > 48" | bc -l) )); then
  echo "⚠️  告警: 平均响应时间过长 (${AVG_RESPONSE}小时)"
  send_alert "响应时间超过48小时"
fi
```

---

## 性能指标

### KPI定义

| 指标 | 目标 | 计算方式 |
|------|------|----------|
| 解决率 | > 80% | (resolved + closed) / total * 100% |
| 平均响应时间 | < 24h | 首次回复时间的平均值 |
| 用户满意度 | > 4.0 | 基于投票的评分 |
| 重复率 | < 5% | duplicate / total * 100% |

### 生成KPI报告

```bash
#!/bin/bash
# kpi_report.sh

TOKEN="YOUR_TOKEN"

STATS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer ${TOKEN}")

echo "KPI 报告"
echo "========"
echo "时间: $(date)"
echo ""

# 解决率
RESOLUTION=$(echo $STATS | jq -r '.data.summary.resolution_rate')
echo "解决率: ${RESOLUTION}% (目标: > 80%)"
if (( $(echo "$RESOLUTION > 80" | bc -l) )); then
  echo "✅ 达标"
else
  echo "❌ 未达标"
fi

echo ""

# 响应时间
AVG_RESPONSE=$(echo $STATS | jq -r '.data.summary.avg_response_time')
echo "平均响应时间: ${AVG_RESPONSE}小时 (目标: < 24小时)"
if (( $(echo "$AVG_RESPONSE < 24" | bc -l) )); then
  echo "✅ 达标"
else
  echo "❌ 未达标"
fi
```

---

## 最佳实践

1. **定期分析**：
   - 每日：查看新增反馈趋势
   - 每周：分析热门问题和优先级分布
   - 每月：生成完整统计报告

2. **数据驱动决策**：
   - 基于统计数据调整产品优先级
   - 识别常见问题并系统化解决
   - 优化客服资源分配

3. **持续改进**：
   - 跟踪KPI变化趋势
   - 设置合理的目标值
   - 定期review和调整策略

4. **自动化**：
   - 使用定时任务自动生成报告
   - 设置智能告警
   - 数据自动归档
