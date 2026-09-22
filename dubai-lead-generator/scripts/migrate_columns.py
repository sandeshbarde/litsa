"""
Database migration script to add executive intelligence, loophole research,
worldwide location, and sequence stage tracking columns.
"""
import sqlite3

def run_migration():
    conn = sqlite3.connect('dubai_leads.db')
    cursor = conn.cursor()

    columns_to_add = [
        ('city', "TEXT DEFAULT 'Dubai'"),
        ('country', "TEXT DEFAULT 'United Arab Emirates'"),
        ('business_type', "TEXT DEFAULT 'B2B'"),
        ('is_dealer_or_wholesale', "BOOLEAN DEFAULT 0"),
        ('decision_maker_name', "TEXT"),
        ('decision_maker_title', "TEXT"),
        ('decision_maker_email', "TEXT"),
        ('decision_maker_linkedin', "TEXT"),
        ('loophole_summary', "TEXT"),
        ('loophole_data', "JSON"),
        ('sequence_stage', "TEXT DEFAULT 'NOT_STARTED'"),
        ('next_action_due', "DATETIME")
    ]

    cursor.execute("PRAGMA table_info(businesses)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    added = 0
    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            print(f"Adding {col_name} ({col_type})...")
            cursor.execute(f"ALTER TABLE businesses ADD COLUMN {col_name} {col_type}")
            added += 1
        else:
            print(f"{col_name} already exists.")

    conn.commit()
    conn.close()
    print(f"Migration completed successfully. Added {added} columns.")

if __name__ == "__main__":
    run_migration()
