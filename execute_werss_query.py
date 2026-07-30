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
            database='multi_tenant_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            # Query for the requested data
            query = """
            SELECT 
                a.id, 
                a.title,
                a.read_num,
                t.name as tag_name,
                m.username
            FROM we_rss_wechat_article a
            JOIN we_rss_member_article_tag_relation atr ON a.id = atr.article_id
            JOIN we_rss_member_tag t ON atr.tag_id = t.id
            JOIN member m ON t.member_id = m.id
            WHERE t.name = '职场'
              AND a.read_num > 5000
              AND (m.username = 'feng1235' OR m.nick_name = 'feng1235' OR m.phone = 'feng1235')
              AND m.tenant_id = 3
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Query Results:")
            print(json.dumps(results, cls=DateTimeEncoder, indent=2, ensure_ascii=False))
            
            # Also let's check if the member exists just to be safe
            cursor.execute("SELECT id, username, nick_name, tenant_id FROM member WHERE username = 'feng1235' OR nick_name = 'feng1235'")
            print("\nMember 'feng1235':")
            print(json.dumps(cursor.fetchall(), cls=DateTimeEncoder, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
