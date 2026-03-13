# reset_db.py
import os
from app import app, db
from sqlalchemy import inspect

print("="*60)
print("⚠️  DATABASE RESET TOOL")
print("="*60)
print("This will DELETE your current database and create a new one.")
print("All existing order, user, and product data will be LOST.\n")

# Safely ask for confirmation
confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")

if confirm.lower() == 'yes':
    db_path = 'triowise.db'
    
    # 1. Delete the old database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Deleted old database: {db_path}")
    else:
        print("📁 No existing database file found.")
    
    # 2. Create a new database with the updated schema
    with app.app_context():
        print("🔄 Creating new database tables...")
        db.create_all()
        print("✅ New database created successfully!")
        
        # 3. Verify the new columns are present
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('order')]
        print(f"📊 Order table columns: {columns}")
        
        if 'shipped_date' in columns:
            print("✅ TRACKING COLUMNS VERIFIED: shipped_date is present!")
        else:
            print("❌ ERROR: Tracking columns are still missing.")
            
        # 4. (Optional) Re-populate with sample data
        print("\n🔄 Re-creating sample products...")
        try:
            from app import create_sample_products
            create_sample_products()
            print("✅ Sample products added successfully!")
        except Exception as e:
            print(f"⚠️  Could not add sample products: {e}")
            print("   You can add them manually later.")
    
    print("\n" + "="*60)
    print("✅ DATABASE RESET COMPLETE!")
    print("="*60)
    print("You can now restart your Flask app:")
    print("python app.py")

else:
    print("❌ Operation cancelled.")