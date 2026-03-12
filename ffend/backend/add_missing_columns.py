import sqlite3

db_path = 'instance/greensphere.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding missing columns to garden_plants table...")

# Add image_data column if it doesn't exist
try:
    cursor.execute("ALTER TABLE garden_plants ADD COLUMN image_data BLOB")
    print("✅ Added image_data column")
except sqlite3.OperationalError as e:
    print(f"image_data column: {e}")

# Add image_filename column if it doesn't exist
try:
    cursor.execute("ALTER TABLE garden_plants ADD COLUMN image_filename VARCHAR(255)")
    print("✅ Added image_filename column")
except sqlite3.OperationalError as e:
    print(f"image_filename column: {e}")

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
