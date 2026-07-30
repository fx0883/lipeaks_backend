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
            # Check member
            cursor.execute("SELECT id, username, nick_name, tenant_id FROM member WHERE username = 'feng1235' OR nick_name = 'feng1235'")
            print("Member feng1235:")
            print(json.dumps(cursor.fetchall(), cls=DateTimeEncoder, indent=2, ensure_ascii=False))

            # Check tag
            cursor.execute("SELECT * FROM we_rss_member_tag WHERE name = '职场'")
            print("\nTag '职场':")
            print(json.dumps(cursor.fetchall(), cls=DateTimeEncoder, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
