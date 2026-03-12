"""
Add history tracking and species verification columns to PlantProgress table.
Run this once to update the database schema.
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'greensphere.db')

# New columns to add
NEW_COLUMNS = [
    # Species verification
    ("species_name", "VARCHAR(255)"),
    ("species_scientific", "VARCHAR(255)"),
    ("species_confidence", "REAL"),
    ("species_verified", "BOOLEAN DEFAULT 1"),
    ("species_mismatch_reason", "VARCHAR(500)"),
    # Growth tracking
    ("height_change_pct", "REAL"),
    ("area_change_pct", "REAL"),
    ("days_since_last", "INTEGER"),
    ("growth_rate", "REAL"),
    ("leaf_tips_detected", "INTEGER"),
    ("pixels_per_cm", "REAL"),
    # AI analysis
    ("ai_recommendations", "TEXT"),
    ("ai_issues_detected", "TEXT"),
]

def add_columns():
    """Add new columns to plant_progress table if they don't exist."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(plant_progress)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    added = []
    skipped = []
    
    for col_name, col_type in NEW_COLUMNS:
        if col_name in existing_columns:
            skipped.append(col_name)
        else:
            try:
                cursor.execute(f"ALTER TABLE plant_progress ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"  + Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  ! Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\nSummary:")
    print(f"  Added: {len(added)} columns")
    print(f"  Skipped (already exist): {len(skipped)} columns")
    
    if added:
        print(f"\nNew columns: {', '.join(added)}")
    
    return True

if __name__ == "__main__":
    print("Adding history tracking columns to PlantProgress table...")
    print(f"Database: {DB_PATH}\n")
    add_columns()
    print("\nDone!")
