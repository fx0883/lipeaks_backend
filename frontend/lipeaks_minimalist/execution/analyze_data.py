#!/usr/bin/env python3
"""
数据分析脚本
分析打卡记录，生成统计报告

用法:
    python analyze_data.py --input data.json
"""

import json
import argparse
from collections import Counter, defaultdict
from datetime import datetime


def analyze(data: dict) -> dict:
    """分析打卡数据"""
    records = data.get('records', {})
    selected_themes = data.get('selectedThemes', [])
    
    if not records:
        return {"error": "没有找到打卡记录"}
    
    # 按主题统计
    theme_stats = defaultdict(lambda: {"total": 0, "delayed": 0})
    
    # 按日期统计
    daily_stats = defaultdict(int)
    
    for key, record in records.items():
        parts = key.rsplit('-', 3)
        if len(parts) >= 2:
            theme_id = parts[0]
            date = '-'.join(parts[1:])
            
            theme_stats[theme_id]["total"] += 1
            if record.get("delayed"):
                theme_stats[theme_id]["delayed"] += 1
            
            daily_stats[date] += 1
    
    # 计算总体统计
    total_checkins = sum(s["total"] for s in theme_stats.values())
    total_delayed = sum(s["delayed"] for s in theme_stats.values())
    
    # 找出最活跃的日期
    if daily_stats:
        best_day = max(daily_stats.items(), key=lambda x: x[1])
    else:
        best_day = (None, 0)
    
    return {
        "total_checkins": total_checkins,
        "total_delayed": total_delayed,
        "delay_rate": round(total_delayed / total_checkins * 100, 1) if total_checkins > 0 else 0,
        "themes_count": len(theme_stats),
        "best_day": best_day[0],
        "best_day_count": best_day[1],
        "theme_breakdown": dict(theme_stats),
        "daily_breakdown": dict(daily_stats)
    }


def print_report(stats: dict) -> None:
    """打印分析报告"""
    print("\n" + "="*50)
    print("           21天自律打卡 数据分析报告")
    print("="*50 + "\n")
    
    if "error" in stats:
        print(f"⚠️ {stats['error']}")
        return
    
    print(f"📊 总计打卡次数: {stats['total_checkins']}")
    print(f"⏰ 拖延次数: {stats['total_delayed']} ({stats['delay_rate']}%)")
    print(f"🎯 参与主题数: {stats['themes_count']}")
    print(f"🏆 最佳日期: {stats['best_day']} ({stats['best_day_count']}次)")
    
    print("\n--- 按主题统计 ---")
    for theme_id, data in stats['theme_breakdown'].items():
        print(f"  主题 {theme_id}: {data['total']}次 (拖延 {data['delayed']}次)")
    
    print("\n" + "="*50)


def main():
    parser = argparse.ArgumentParser(description='分析打卡数据')
    parser.add_argument('--input', required=True, help='输入 JSON 文件路径')
    parser.add_argument('--output', default=None, help='输出报告文件路径')
    
    args = parser.parse_args()
    
    # 读取数据
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 分析
    stats = analyze(data)
    
    # 打印报告
    print_report(stats)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 报告已保存到 {args.output}")


if __name__ == '__main__':
    main()
