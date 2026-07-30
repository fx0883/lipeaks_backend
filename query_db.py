import pymysql
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def query_db():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='multi_tenant_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            # Query tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("Tables in multi_tenant_db:")
            for t in tables:
                print(list(t.values())[0])
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    query_db()
