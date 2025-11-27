from django.db import connection

# 检查licenses_license表结构
with connection.cursor() as cursor:
    cursor.execute("DESCRIBE licenses_license")
    columns = cursor.fetchall()
    print("licenses_license表结构:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}")
