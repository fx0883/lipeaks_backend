import pymysql

def check_content_types():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='multi_tenant_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT content_type FROM cms_article")
            types = cursor.fetchall()
            print("Distinct content_types in cms_article:")
            for t in types:
                print(t['content_type'])
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_content_types()
