#!/usr/bin/env python3
"""
数据导出脚本
将 localStorage 数据导出为 JSON 或 CSV 格式

用法:
    python export_data.py --format json --output data.json
    python export_data.py --format csv --output data.csv
"""

import json
import csv
import argparse
from pathlib import Path
from datetime import datetime


def export_to_json(data: dict, output_path: str) -> None:
    """导出为 JSON 格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已导出到 {output_path}")


def export_to_csv(data: dict, output_path: str) -> None:
    """导出为 CSV 格式"""
    records = data.get('records', {})
    
    if not records:
        print("⚠️ 没有找到打卡记录")
        return
    
    # 提取所有记录
    rows = []
    for key, record in records.items():
        theme_id, date = key.rsplit('-', 1)
        rows.append({
            'theme_id': theme_id,
            'date': date,
            **record
        })
    
    # 写入 CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ 已导出 {len(rows)} 条记录到 {output_path}")


def main():
    parser = argparse.ArgumentParser(description='导出打卡数据')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='输出格式 (默认: json)')
    parser.add_argument('--output', default=None,
                       help='输出文件路径')
    parser.add_argument('--input', default=None,
                       help='输入 JSON 文件路径 (从浏览器导出的 localStorage)')
    
    args = parser.parse_args()
    
    # 默认输出路径
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f".tmp/export_{timestamp}.{args.format}"
    
    # 确保目录存在
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # 读取数据
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("⚠️ 请提供 --input 参数指定输入文件")
        print("提示: 在浏览器控制台运行以下命令导出 localStorage:")
        print("  copy(JSON.stringify(localStorage))")
        return
    
    # 导出
    if args.format == 'json':
        export_to_json(data, args.output)
    else:
        export_to_csv(data, args.output)


if __name__ == '__main__':
    main()
