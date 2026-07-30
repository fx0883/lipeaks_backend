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
            # Query the data
            query = """
            SELECT 
                a.id, 
                a.title, 
                a.status,
                s.views_count,
                t.name as tag_name
            FROM cms_article a
            JOIN cms_article_tag at ON a.id = at.article_id
            JOIN cms_tag t ON at.tag_id = t.id
            JOIN cms_article_statistics s ON a.id = s.article_id
            WHERE a.tenant_id = 3
              AND t.name = '职场'
              AND s.views_count > 5000
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Query Results:")
            print(json.dumps(results, cls=DateTimeEncoder, indent=2, ensure_ascii=False))
            
            # Also let's check categories if there's any related to "文章"
            cursor.execute("SELECT * FROM cms_category")
            categories = cursor.fetchall()
            print("\nCategories:")
            print(json.dumps(categories, cls=DateTimeEncoder, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    run_query()
