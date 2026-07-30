import pymysql

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
            cursor.execute("SELECT tenant_id, COUNT(*) as article_count FROM cms_article GROUP BY tenant_id")
            results = cursor.fetchall()
            print("Articles count by tenant_id:")
            for r in results:
                print(r)
                
            # Also let's check the schema of the cms_article to see if there is a 'type' field
            cursor.execute("SHOW COLUMNS FROM cms_article")
            columns = cursor.fetchall()
            print("\nColumns in cms_article:")
            for c in columns:
                print(c['Field'], c['Type'])
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    run_query()
