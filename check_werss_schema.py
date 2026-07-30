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
            cursor.execute("SHOW TABLES")
            tables = [list(t.values())[0] for t in cursor.fetchall()]
            
            we_rss_tables = [t for t in tables if 'we_rss' in t or 'member' in t]
            print("Relevant Tables:")
            for t in we_rss_tables:
                print(f"\n--- Schema for {t} ---")
                cursor.execute(f"DESCRIBE {t}")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"{col['Field']} - {col['Type']}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_query()
