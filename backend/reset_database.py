# backend/reset_database.py

from config import DATABASE_KEY
from database import db

# python reset_database.py

# Secure two-step process
plan = db.plan_database_empty(DATABASE_KEY)
print(f"🗑️  Will drop collections: {plan['collections_to_drop']}")

# ask the user to press y to confirm and n to cancel
confirm = input("⚠️  Press 'y' to confirm or 'n' to cancel: ").strip().lower()
if confirm != 'y':
    print("❌ Operation cancelled. No changes were made.")
else:
    # Proceed with the database reset
    print("🔄 Proceeding with database reset...")
    db.execute_database_empty(plan)
    print("✅ Database reset completed successfully!")
