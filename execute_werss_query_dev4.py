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
            # Check feed tags
            query = """
            SELECT feed_id 
            FROM we_rss_member_feed_tag_relation 
            WHERE tag_id = 10
            """
            cursor.execute(query)
            feeds = cursor.fetchall()
            print("Feeds for Tag '职场':")
            print(json.dumps(feeds, indent=2))
            
            if feeds:
                feed_ids = [f['feed_id'] for f in feeds]
                feed_ids_str = ','.join(map(str, feed_ids))
                query_articles = f"""
                SELECT a.id, a.title, a.read_num 
                FROM we_rss_wechat_article a
                WHERE a.feed_id IN ({feed_ids_str})
                  AND a.read_num > 5000
                """
                cursor.execute(query_articles)
                articles = cursor.fetchall()
                print("\nArticles for these feeds with read_num > 5000:")
                print(json.dumps(articles, cls=DateTimeEncoder, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
