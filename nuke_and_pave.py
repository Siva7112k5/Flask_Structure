# nuke_and_pave.py
import os
import sys
import importlib

print("="*60)
print("💣 NUKE AND PAVE - COMPLETE DATABASE RESET")
print("="*60)

# 1. Delete database file
db_path = 'triowise.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted: {db_path}")
else:
    print("✅ No database file found")

# 2. Delete all cache folders
import shutil
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        shutil.rmtree(cache_path)
        print(f"✅ Deleted cache: {cache_path}")

# 3. FORCE reload all modules
print("\n🔄 Forcing module reload...")
if 'app' in sys.modules:
    del sys.modules['app']
if 'models' in sys.modules:
    del sys.modules['models']

# 4. Import fresh
from app import app, db
import models

# 5. Print the Order model columns from the FRESH import
print("\n📋 Order model columns from FRESH import:")
order_columns = [col.name for col in models.Order.__table__.columns]
print(order_columns)

if 'shipped_date' in order_columns:
    print("✅ CONFIRMED: models.py has tracking columns!")
else:
    print("❌ ERROR: models.py still missing columns")
    print("   This should not happen - your models.py looks correct")
    sys.exit(1)

# 6. Create new database
print("\n🔄 Creating new database...")
with app.app_context():
    db.create_all()
    print("✅ Database created successfully!")

    # 7. Verify database columns
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    db_columns = [col['name'] for col in inspector.get_columns('order')]
    print(f"\n📊 Actual database columns: {db_columns}")

    if 'shipped_date' in db_columns:
        print("\n✅🎉 SUCCESS! Tracking columns are now in the database!")
    else:
        print("\n❌ FAILURE: Database still missing columns")
        print("   This is very unusual - your models.py is correct")
        print("   The issue must be elsewhere")

    # 8. Add sample products
    print("\n🔄 Adding sample products...")
    try:
        from app import create_sample_products
        create_sample_products()
        print("✅ Sample products added!")
    except Exception as e:
        print(f"⚠️ Sample products error: {e}")

print("\n" + "="*60)
print("✅ RESET COMPLETE!")
print("="*60)
print("\nNow run: python app.py")