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
            # Let's get all articles for tenant_id = 3 to see what's there
            query = """
            SELECT a.id, a.title, a.tenant_id, t.name as tag_name, c.name as category_name, s.views_count
            FROM cms_article a
            LEFT JOIN cms_article_tag at ON a.id = at.article_id
            LEFT JOIN cms_tag t ON at.tag_id = t.id
            LEFT JOIN cms_article_category ac ON a.id = ac.article_id
            LEFT JOIN cms_category c ON ac.category_id = c.id
            LEFT JOIN cms_article_statistics s ON a.id = s.article_id
            WHERE a.tenant_id = 3
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Articles for tenant 3:")
            print(json.dumps(results, cls=DateTimeEncoder, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    run_query()
