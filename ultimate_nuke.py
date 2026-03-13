# ultimate_nuke.py
import os
import sys
import shutil
import importlib

print("="*60)
print("💀 ULTIMATE NUKE - COMPLETE SYSTEM RESET")
print("="*60)

# 1. Kill any existing database files
db_path = 'triowise.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted: {db_path}")
else:
    print("✅ No database file found")

# 2. Delete ALL cache folders recursively
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        shutil.rmtree(cache_path)
        print(f"✅ Deleted cache: {cache_path}")

# 3. Force reload ALL modules
print("\n🔄 Forcing complete module reload...")
modules_to_reload = ['app', 'models', 'forms', 'utils.smart_search', 'utils.upload']
for module in modules_to_reload:
    if module in sys.modules:
        del sys.modules[module]
        print(f"   Removed: {module}")

# 4. Import fresh
print("\n📥 Importing fresh modules...")
from app import app, db, create_sample_products
import models

# 5. Verify model has columns
print("\n📋 Order model columns verification:")
order_columns = [col.name for col in models.Order.__table__.columns]
print(order_columns)

if 'shipped_date' not in order_columns:
    print("❌ CRITICAL: Models still missing columns!")
    print("   This should be impossible - check models.py file permissions")
    sys.exit(1)

print("✅ Model verification passed!")

# 6. Create new database
print("\n🔄 Creating new database...")
with app.app_context():
    # Drop all tables first to ensure clean slate
    db.drop_all()
    print("   Dropped all existing tables")
    
    # Create all tables fresh
    db.create_all()
    print("   Created all tables fresh")

    # 7. Verify database columns
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    db_columns = [col['name'] for col in inspector.get_columns('order')]
    print(f"\n📊 Database columns: {db_columns}")

    if 'shipped_date' in db_columns:
        print("\n✅🎉 SUCCESS! Database has tracking columns!")
    else:
        print("\n❌ FAILURE: Database still missing columns")
        print("   This indicates a SQLAlchemy metadata issue")
        print("   Trying one more approach...")
        
        # Last resort: create tables individually
        from models import Order, User, Product, OrderItem, Review, Wishlist
        db.create_all()
        db_columns = [col['name'] for col in inspector.get_columns('order')]
        if 'shipped_date' in db_columns:
            print("✅ Second attempt succeeded!")
        else:
            print("❌ CRITICAL FAILURE - Manual intervention needed")

    # 8. Add sample products
    print("\n🔄 Adding sample products...")
    try:
        # Check if products exist first
        if Product.query.count() == 0:
            create_sample_products()
            print(f"✅ Added {Product.query.count()} products")
        else:
            print(f"📊 Database already has {Product.query.count()} products")
    except Exception as e:
        print(f"⚠️ Sample products error: {e}")

print("\n" + "="*60)
print("✅ RESET COMPLETE!")
print("="*60)
print("\nNow run: python app.py")