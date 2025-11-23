from django.db import connection

sql_file = 'temp1123_6_application/fix_application_fields.sql'

with open(sql_file, 'r') as f:
    sql = f.read()

# 分割SQL语句
statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

with connection.cursor() as cursor:
    for i, statement in enumerate(statements, 1):
        if statement:
            try:
                print(f"执行语句 {i}/{len(statements)}...")
                cursor.execute(statement)
                print(f"✓ 成功")
            except Exception as e:
                print(f"✗ 失败: {e}")

print("\n完成！")
