# final_check.py
from app import app, db
import sys

print("="*60)
print("🔍 FINAL MODEL CHECK")
print("="*60)

with app.app_context():
    # Print the columns SQLAlchemy sees for the Order model
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('order')]
    print(f"📊 Columns in 'order' table: {columns}")

    if 'shipped_date' in columns:
        print("\n✅ SUCCESS: The database has the new tracking columns!")
    else:
        print("\n❌ FAILURE: The database still does NOT have the new columns.")
        print("   This means your models.py file is not being read correctly.")
        print("   Please copy and paste your entire models.py file here so I can see it.")

    # Also print the path to the models file being used
    import models
    print(f"\n📁 models.py loaded from: {models.__file__}")