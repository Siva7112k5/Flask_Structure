# fresh_start.py
import os
from app import app, db

# Define the Order model class again here INSIDE the script to ensure it's the latest
# (This is a trick to force SQLAlchemy to use the model definition from this script)
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(120), nullable=False)
    customer_phone = Column(String(20))
    address = Column(Text, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    payment_method = Column(String(50))
    subtotal = Column(Float, default=0)
    shipping = Column(Float, default=0)
    total = Column(Float, default=0)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- THE NEW TRACKING COLUMNS (explicitly listed) ---
    shipped_date = Column(DateTime, nullable=True)
    out_for_delivery_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)
    cancelled_date = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # --- END OF NEW COLUMNS ---

    items = relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

# Now, run the reset with this fresh model definition
print("="*60)
print("⚠️  FORCEFUL DATABASE RESET")
print("="*60)
print("This will DELETE your current database and create a new one.")
print("All existing order, user, and product data will be LOST.\n")

confirm = input("Are you sure? (type 'yes'): ")

if confirm.lower() == 'yes':
    db_path = 'triowise.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Deleted old database: {db_path}")

    with app.app_context():
        print("🔄 Creating new database tables...")
        # This db.create_all() will use the Order model defined above in THIS file
        db.create_all()
        print("✅ New database created!")

        # Verify the columns
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('order')]
        print(f"📊 Order table columns: {columns}")

        if 'shipped_date' in columns:
            print("✅ SUCCESS: Tracking columns are now present!")
        else:
            print("❌ FAILURE: Tracking columns are STILL missing.")
            print("   This indicates the model definition is still not being picked up.")
else:
    print("❌ Cancelled.")