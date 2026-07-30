import pymysql
import json

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
            # Check for tag 职场
            cursor.execute("SELECT * FROM cms_tag WHERE name = '职场'")
            print("Tag '职场':", cursor.fetchall())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
