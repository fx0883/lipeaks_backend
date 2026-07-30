import pymysql

def describe_tables():
    tables = ['cms_article', 'cms_tag', 'cms_article_tag', 'cms_article_statistics']
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='multi_tenant_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            for table in tables:
                print(f"--- Schema for {table} ---")
                try:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"{col['Field']} - {col['Type']}")
                except Exception as e:
                    print(f"Error describing {table}: {e}")
                print()
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    describe_tables()
