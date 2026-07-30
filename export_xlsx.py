import pymysql
from datetime import datetime
import os
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import openpyxl
except ImportError:
    install('openpyxl')
    import openpyxl
from openpyxl import Workbook

def export_to_excel():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='multi_tenant_db_dev',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            # Query articles where read_num > 10000
            query = """
            SELECT 
                a.id, 
                a.title,
                a.read_num,
                a.like_num,
                a.old_like_num,
                a.share_num,
                a.collect_num,
                a.comment_count,
                a.comment_total_count,
                a.publish_time,
                a.url,
                f.mp_name
            FROM we_rss_wechat_article a
            JOIN we_rss_wechat_feed f ON a.feed_id = f.id
            JOIN we_rss_member_feed_tag_relation ftr ON f.id = ftr.feed_id
            JOIN we_rss_member_tag t ON ftr.tag_id = t.id
            JOIN member m ON t.member_id = m.id
            WHERE t.name = '职场'
              AND a.read_num > 10000
              AND m.username = 'feng1235'
              AND m.tenant_id = 3
            ORDER BY a.read_num DESC
            """
            cursor.execute(query)
            articles = cursor.fetchall()
            
            # Create a new workbook and select active sheet
            wb = Workbook()
            ws = wb.active
            ws.title = "高阅读量文章"
            
            # Write headers
            headers = [
                'ID', '文章标题', '所属公众号', '阅读量', '点赞量', 
                '在看数量', '分享量', '收藏量', '评论数', '总评论数',
                '发布时间', '文章链接'
            ]
            ws.append(headers)
            
            # Write data rows
            for a in articles:
                pub_time = a['publish_time'].strftime("%Y-%m-%d %H:%M:%S") if a['publish_time'] else ""
                row = [
                    a['id'],
                    a['title'],
                    a['mp_name'],
                    a['read_num'],
                    a['like_num'],
                    a['old_like_num'],
                    a['share_num'],
                    a['collect_num'],
                    a['comment_count'],
                    a['comment_total_count'],
                    pub_time,
                    a['url']
                ]
                ws.append(row)
                
            # Adjust column widths for better readability
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter # Get the column name
                for cell in col:
                    try: # Necessary to avoid error on empty cells
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                if adjusted_width > 50:
                    adjusted_width = 50
                ws.column_dimensions[column].width = adjusted_width
                
            output_file = r'C:\Users\Administrator\.gemini\antigravity\brain\e2a9cde7-7b7e-4241-bb9f-ebe40e246344\high_read_articles.xlsx'
            wb.save(output_file)
            
            print(f"Success. Exported {len(articles)} rows to {output_file}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    export_to_excel()
