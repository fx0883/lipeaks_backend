import pymysql
import json
from datetime import datetime

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
            # Check articles for tag_id = 10
            query = """
            SELECT a.id, a.title, a.read_num
            FROM we_rss_wechat_article a
            JOIN we_rss_member_article_tag_relation atr ON a.id = atr.article_id
            WHERE atr.tag_id = 10
            """
            cursor.execute(query)
            articles = cursor.fetchall()
            print("Articles for Tag '职场':")
            print(json.dumps(articles, cls=DateTimeEncoder, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
