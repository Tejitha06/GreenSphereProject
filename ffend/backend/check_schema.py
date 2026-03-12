import sqlite3

db_path = 'instance/greensphere.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(garden_plants)")
columns = cursor.fetchall()

print("Column Information for garden_plants table:")
print("=" * 60)
for col in columns:
    col_id, name, type_, notnull, dflt_value, pk = col
    print(f"{name:<25}| {type_:<15} | PK:{pk} | NN:{notnull}")

print("\n" + "=" * 60)
print(f"Total columns: {len(columns)}")

conn.close()
