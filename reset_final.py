# reset_final.py
import os
from app import app, db

print("="*60)
print("🔥 FINAL DATABASE RESET")
print("="*60)

# Double-check the file is gone
db_path = 'triowise.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️  Deleted: {db_path}")
else:
    print("✅ No database file found.")

# Remove cache folder again to be sure
if os.path.exists('__pycache__'):
    import shutil
    shutil.rmtree('__pycache__')
    print("🗑️  Deleted __pycache__")

print("\n🔄 Creating a brand new database...")
with app.app_context():
    # This will use your original models.py with the new columns
    db.create_all()
    print("✅ Database created successfully!")

    # Verify the new columns
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('order')]
    print(f"\n📊 Order table columns: {columns}")

    if 'shipped_date' in columns:
        print("\n✅ SUCCESS! Tracking columns are now present!")
        print("   You can now run your app normally.")
    else:
        print("\n❌ ERROR: Tracking columns are still missing.")
        print("   This indicates an issue with your models.py file.")

    # Re-create sample products
    print("\n🔄 Adding sample products...")
    try:
        from app import create_sample_products
        create_sample_products()
        print("✅ Sample products added!")
    except Exception as e:
        print(f"⚠️  Could not add sample products: {e}")

print("\n" + "="*60)
print("✅ RESET COMPLETE!")
print("="*60)
print("\nYou can now start your app with: python app.py")