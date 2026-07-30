import pymysql
import json
from datetime import datetime
import os

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def run_query():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='multi_tenant_db_dev',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            # Query articles where the feed is tagged with '职场' and the member is feng1235
            query = """
            SELECT 
                a.id, 
                a.title,
                a.read_num,
                a.publish_time,
                a.url,
                f.mp_name
            FROM we_rss_wechat_article a
            JOIN we_rss_wechat_feed f ON a.feed_id = f.id
            JOIN we_rss_member_feed_tag_relation ftr ON f.id = ftr.feed_id
            JOIN we_rss_member_tag t ON ftr.tag_id = t.id
            JOIN member m ON t.member_id = m.id
            WHERE t.name = '职场'
              AND a.read_num > 5000
              AND m.username = 'feng1235'
              AND m.tenant_id = 3
            ORDER BY a.read_num DESC
            """
            cursor.execute(query)
            articles = cursor.fetchall()
            
            # Formatting as Markdown table
            md_content = "# 用户 feng1235 的“职场”标签下阅读量超 5000 的文章\n\n"
            md_content += f"共找到 {len(articles)} 篇文章。\n\n"
            
            if articles:
                md_content += "| ID | 标题 | 公众号 | 阅读量 | 发布时间 | 链接 |\n"
                md_content += "|---|---|---|---|---|---|\n"
                for a in articles:
                    title = a['title'].replace('|', '&#124;')
                    url = f"[阅读原文]({a['url']})" if a['url'] else "无链接"
                    pub_time = a['publish_time'].strftime("%Y-%m-%d %H:%M") if a['publish_time'] else "未知"
                    md_content += f"| {a['id']} | {title} | {a['mp_name']} | {a['read_num']} | {pub_time} | {url} |\n"
            
            output_file = r'C:\Users\Administrator\.gemini\antigravity\brain\e2a9cde7-7b7e-4241-bb9f-ebe40e246344\high_read_articles.md'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"Results written to {output_file}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
