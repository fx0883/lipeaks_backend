from django.db import connection

sqls = [
    "ALTER TABLE licenses_license ADD COLUMN application_id BIGINT NULL",
    "ALTER TABLE licenses_license_plan ADD COLUMN application_id BIGINT NULL",  
    "ALTER TABLE licenses_tenant_license_quota ADD COLUMN application_id BIGINT NULL",
]

with connection.cursor() as cursor:
    for sql in sqls:
        try:
            print(f"执行: {sql}")
            cursor.execute(sql)
            print("成功")
        except Exception as e:
            print(f"失败: {e}")

print("完成")
