import sqlite3

db_path = 'instance/greensphere.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding age column to garden_plants table...")

# Add age column if it doesn't exist
try:
    cursor.execute("ALTER TABLE garden_plants ADD COLUMN age VARCHAR(100)")
    print("✅ Added age column")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e):
        print("⚠️ age column already exists")
    else:
        print(f"Error: {e}")

conn.commit()
conn.close()

print("\nVerifying updated schema:")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(garden_plants)")
columns = cursor.fetchall()

print("Garden_plants columns:")
for col in columns:
    col_id, name, type_, notnull, dflt_value, pk = col
    print(f"  {name:<25}| {type_:<15}")

print(f"\nTotal columns: {len(columns)}")
conn.close()

print("\n✅ Migration complete!")
