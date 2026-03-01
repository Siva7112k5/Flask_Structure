from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Order, OrderItem, Review, ReviewImage  # Added ReviewImage
from forms import LoginForm, RegisterForm, ReviewForm
from functools import wraps
import random
import string
from datetime import datetime
from flask import render_template
from textblob import TextBlob
from models import Wishlist  # Or wherever your models are stored
import os  # Make sure this is imported

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///triowise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ IMPORTANT: Add upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Make sure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'reviews'), exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add this with your other configurations
@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now()}

 #   this is the starting point to arrange the backend code 

#Home router

@app.route('/')
def home():
    # Get latest 5 products (newest first)
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    # Get best seller products (highest rated)
    best_seller_products = Product.query.order_by(Product.rating.desc()).limit(5).all()
    
    # Total products count
    total_products = Product.query.count()
    
    categories = ['Appliances', 'Home & Kitchen', 'Fashion', 'Sports', 'Beauty', 'Toys', 'Books', 'Furniture', 
                  'Bags', 'Mobiles', 'Laptop', 'Watch', 'Men Dresses', 'Woman Dresses', 'Decorations', 
                  'Pets care', 'Bathing products', 'Skin care', 'Face care', 'Shoes', 'Mens Accesories', 
                  'Women Accesories', 'Gifts', 'Hair care']
    
    return render_template('index.html', 
                         featured_products=latest_products,  # Keep for backward compatibility
                         latest_products=latest_products,
                         best_seller_products=best_seller_products,
                         total_products=total_products,
                         categories=categories)


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

from sqlalchemy import func

from sqlalchemy import func

# At the top of app.py, add these imports
from utils.smart_search import SmartSearch, SearchHistory
from functools import lru_cache
import time

# Initialize search history (can be stored in database later)
search_history = SearchHistory()

@app.route('/search')
def search():
    """
    Enhanced smart search route
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    start_time = time.time()
    
    if not query:
        # Show popular searches if no query
        popular = search_history.get_popular_searches(10)
        return render_template('search_results.html', 
                             products=[],
                             query='',
                             popular_searches=popular,
                             search_time=0)
    
    # Get all products (you might want to cache this)
    products = Product.query.all()
    
    # Create smart search instance
    smart_search = SmartSearch(products)
    
    # Perform smart search
    results = smart_search.search(query)
    
    # Log the search
    search_history.log_search(query, len(results))
    
    # Check if we should suggest spelling correction
    if len(results) == 0:
        corrected = smart_search.suggest_corrections(query)
        if corrected and corrected != query:
            flash(f'Did you mean: "{corrected}"?', 'info')
    
    # Get related searches
    related = search_history.get_related_searches(query)
    
    # Extract just the products from results
    products_found = [r[0] for r in results]
    
    # Calculate search time
    search_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
    
    # Paginate results
    total = len(products_found)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products_found[start:end]
    
    return render_template('search_results.html',
                         products=paginated_products,
                         query=query,
                         total_results=total,
                         page=page,
                         per_page=per_page,
                         search_time=search_time,
                         related_searches=related)


@app.route('/search/click', methods=['POST'])
def track_search_click():
    """
    Track when users click on search results
    This helps improve search relevance over time
    """
    data = request.get_json()
    query = data.get('query')
    product_id = data.get('product_id')
    
    if query and product_id:
        search_history.log_click(query, product_id)
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def get_cart():
    return session.get('cart', [])

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

def cart_count():
    return sum(item['quantity'] for item in get_cart())

def generate_order_number():
    return 'ORD' + ''.join(random.choices(string.digits, k=8))

from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active chats (in production, use Redis)
active_chats = {}
chat_messages = {}
support_agents = set()

class ChatMessage:
    def __init__(self, sender, message, timestamp):
        self.sender = sender
        self.message = message
        self.timestamp = timestamp

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    # Remove from active chats
    for chat_id, data in list(active_chats.items()):
        if data['user_sid'] == request.sid or data.get('agent_sid') == request.sid:
            # Notify other party
            if data['user_sid'] == request.sid:
                # User disconnected
                if data.get('agent_sid'):
                    emit('chat_ended', {'message': 'User has left the chat'}, room=data['agent_sid'])
            else:
                # Agent disconnected
                emit('chat_ended', {'message': 'Support agent has left the chat'}, room=data['user_sid'])
            del active_chats[chat_id]
            break

@socketio.on('start_chat')
def handle_start_chat(data):
    user_id = current_user.id if current_user.is_authenticated else f"guest_{uuid.uuid4().hex[:8]}"
    user_name = current_user.name if current_user.is_authenticated else data.get('name', 'Guest')
    user_email = current_user.email if current_user.is_authenticated else data.get('email', '')
    
    chat_id = str(uuid.uuid4())[:8]
    
    active_chats[chat_id] = {
        'id': chat_id,
        'user_id': user_id,
        'user_name': user_name,
        'user_email': user_email,
        'user_sid': request.sid,
        'agent_sid': None,
        'status': 'waiting',
        'start_time': datetime.utcnow(),
        'messages': []
    }
    
    join_room(chat_id)
    
    # Notify user
    emit('chat_started', {
        'chat_id': chat_id,
        'message': 'Connecting you to a support agent...'
    })
    
    # If no agents online, show offline message
    if len(support_agents) == 0:
        emit('agent_offline', {
            'message': 'No agents are online right now. Please leave a message.',
            'email': 'support@triowise.com'
        })

@socketio.on('agent_join')
def handle_agent_join(data):
    agent_name = data.get('name', 'Support Agent')
    support_agents.add(request.sid)
    
    # Check for waiting chats
    waiting_chats = [c for c in active_chats.values() if c['status'] == 'waiting']
    
    emit('agent_joined', {
        'waiting_chats': len(waiting_chats),
        'agent_name': agent_name
    })

@socketio.on('agent_assign')
def handle_agent_assign(data):
    chat_id = data.get('chat_id')
    agent_name = data.get('agent_name', 'Support Agent')
    
    if chat_id in active_chats:
        active_chats[chat_id]['agent_sid'] = request.sid
        active_chats[chat_id]['status'] = 'active'
        active_chats[chat_id]['agent_name'] = agent_name
        
        join_room(chat_id)
        
        # Notify user
        emit('agent_assigned', {
            'agent_name': agent_name,
            'message': f'You are now connected with {agent_name}'
        }, room=active_chats[chat_id]['user_sid'])
        
        # Send chat history
        if active_chats[chat_id]['messages']:
            emit('chat_history', {
                'messages': active_chats[chat_id]['messages']
            }, room=request.sid)

@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data.get('chat_id')
    message = data.get('message')
    sender = data.get('sender', 'user')  # 'user' or 'agent'
    
    if chat_id in active_chats:
        chat_data = active_chats[chat_id]
        
        msg = {
            'sender': sender,
            'message': message,
            'timestamp': datetime.utcnow().strftime('%H:%M'),
            'sender_name': chat_data['user_name'] if sender == 'user' else chat_data.get('agent_name', 'Support')
        }
        
        chat_data['messages'].append(msg)
        
        # Broadcast to room
        emit('new_message', msg, room=chat_id)
        
        # If agent not assigned, store as offline message
        if not chat_data['agent_sid'] and sender == 'user':
            # Store in database for later follow-up
            store_offline_message(chat_data, message)

@socketio.on('typing')
def handle_typing(data):
    chat_id = data.get('chat_id')
    is_typing = data.get('is_typing', False)
    
    if chat_id in active_chats:
        emit('user_typing', {'is_typing': is_typing}, 
             room=active_chats[chat_id].get('agent_sid') if active_chats[chat_id].get('agent_sid') else None)

@socketio.on('end_chat')
def handle_end_chat(data):
    chat_id = data.get('chat_id')
    
    if chat_id in active_chats:
        emit('chat_ended', {'message': 'Chat has ended'}, room=chat_id)
        
        # Save chat transcript
        save_chat_transcript(active_chats[chat_id])
        
        # Clean up
        leave_room(chat_id)
        del active_chats[chat_id]

def store_offline_message(chat_data, message):
    """Store offline message in database"""
    class OfflineMessage(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        chat_id = db.Column(db.String(20))
        user_name = db.Column(db.String(100))
        user_email = db.Column(db.String(120))
        message = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        status = db.Column(db.String(20), default='pending')
    
    offline_msg = OfflineMessage(
        chat_id=chat_data['id'],
        user_name=chat_data['user_name'],
        user_email=chat_data['user_email'],
        message=message
    )
    db.session.add(offline_msg)
    db.session.commit()
    
    # Send email notification to support
    send_offline_message_notification(offline_msg)

def save_chat_transcript(chat_data):
    """Save chat transcript to database"""
    class ChatTranscript(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        chat_id = db.Column(db.String(20))
        user_id = db.Column(db.String(100))
        user_name = db.Column(db.String(100))
        user_email = db.Column(db.String(120))
        agent_name = db.Column(db.String(100))
        messages = db.Column(db.Text)  # JSON string
        start_time = db.Column(db.DateTime)
        end_time = db.Column(db.DateTime, default=datetime.utcnow)
        rating = db.Column(db.Integer, nullable=True)
        feedback = db.Column(db.Text, nullable=True)
    
    transcript = ChatTranscript(
        chat_id=chat_data['id'],
        user_id=chat_data['user_id'],
        user_name=chat_data['user_name'],
        user_email=chat_data['user_email'],
        agent_name=chat_data.get('agent_name', ''),
        messages=json.dumps(chat_data['messages']),
        start_time=chat_data['start_time']
    )
    db.session.add(transcript)
    db.session.commit()


@app.route('/products')
def all_products():
    # Define categories
    categories = ['Appliances', 'Home & Kitchen', 'Fashion', 'Sports', 'Beauty', 'Toys', 'Books', 'Furniture', 
                  'Bags', 'Mobiles', 'Laptop', 'Watch', 'Men Dresses', 'Woman Dresses', 'Decorations', 
                  'Pets care', 'Bathing products', 'Skin care', 'Face care', 'Shoes', 'Mens Accesories', 
                  'Women Accesories', 'Gifts', 'Hair care']
    
    # Get filter parameters
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    brand = request.args.get('brand')
    sort = request.args.get('sort', 'newest')
    
    # IMPORTANT: Get ALL products first
    query = Product.query
    
    # Apply filters if they exist
    if category and category != '':
        query = query.filter(Product.category == category)
    if min_price and min_price > 0:
        query = query.filter(Product.price >= min_price)
    if max_price and max_price > 0:
        query = query.filter(Product.price <= max_price)
    if brand and brand != '':
        query = query.filter(Product.brand == brand)
    
    # Apply sorting
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    # Get ALL products (not paginated)
    all_products = query.all()
    
    # Get unique brands for filter sidebar
    brands_raw = db.session.query(Product.brand).distinct().all()
    brands = [b[0] for b in brands_raw if b[0]]
    
    print(f"Products found: {len(all_products)}")  # Debug in console
    
    return render_template('all_products.html', 
                         products=all_products, 
                         brands=brands,
                         categories=categories,
                         filters=request.args)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category=product.category)\
                                   .filter(Product.id != product_id)\
                                   .limit(4).all()
    
    # Track recently viewed
    recent = session.get('recently_viewed', [])
    
    # Remove if already exists
    if product_id in recent:
        recent.remove(product_id)
    
    # Add to beginning
    recent.insert(0, product_id)
    
    # Keep only last 6
    recent = recent[:6]
    session['recently_viewed'] = recent
    
    # Get recent products
    recent_products = []
    if recent:
        recent_products = Product.query.filter(Product.id.in_(recent)).all()
        # Sort by the order in session
        recent_products.sort(key=lambda x: recent.index(x.id))
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         recent_products=recent_products)

@app.route('/api/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    try:
        # Check if already in wishlist
        existing = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Product already in wishlist'
            })
        
        wishlist_item = Wishlist(
            user_id=current_user.id,
            product_id=product_id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added to wishlist',
            'wishlist_count': Wishlist.query.filter_by(user_id=current_user.id).count()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    try:
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first_or_404()
        
        db.session.delete(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Removed from wishlist',
            'wishlist_count': Wishlist.query.filter_by(user_id=current_user.id).count()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id)\
                                  .order_by(Wishlist.created_at.desc()).all()
    products = [item.product for item in wishlist_items]
    
    return render_template('wishlist.html', products=products)




@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        quantity = data.get('quantity', 1)
        
        cart = get_cart()
        
        # Check if product already in cart
        found = False
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] += quantity
                found = True
                break
        
        if not found:
            cart.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'image': product.image,
                'quantity': quantity
            })
        
        save_cart(cart)
        return jsonify({'success': True, 'cart_count': cart_count()})
        
    except Exception as e:
        print(f"Error adding to cart: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/check-orders')
def check_orders():
    orders = Order.query.all()
    if not orders:
        return "No orders found in database"
    
    html = "<h1>Orders in Database</h1>"
    html += "<table border='1'><tr><th>ID</th><th>Order #</th><th>Customer</th><th>Date</th><th>Status</th></tr>"
    for o in orders:
        html += f"<tr>"
        html += f"<td>{o.id}</td>"
        html += f"<td>{o.order_number}</td>"
        html += f"<td>{o.customer_name}</td>"
        html += f"<td>{o.created_at}</td>"
        html += f"<td>{o.status}</td>"
        html += f"</tr>"
    html += "</table>"
    return html    

@app.route('/test-cart/<int:product_id>')
def test_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        cart = get_cart()
        
        cart.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.image,
            'quantity': 1
        })
        
        save_cart(cart)
        return f"Added {product.name} to cart! <a href='/cart'>View Cart</a>"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        cart = get_cart()
        
        for item in cart:
            if item['id'] == product_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    item['quantity'] = quantity
                break
        
        save_cart(cart)
        
        subtotal = sum(float(item['price']) * item['quantity'] for item in cart)
        item_total = 0
        for item in cart:
            if item['id'] == product_id:
                item_total = float(item['price']) * item['quantity']
                break
        
        return jsonify({
            'success': True,
            'cart_count': cart_count(),
            'subtotal': subtotal,
            'item_total': item_total
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    try:
        cart = get_cart()
        cart = [item for item in cart if item['id'] != product_id]
        save_cart(cart)
        return jsonify({'success': True, 'cart_count': cart_count()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cart')
def cart():
    cart_items = get_cart()
    subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        data = request.get_json()
        cart_items = get_cart()
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'})
        
        subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            customer_name=current_user.name,
            customer_email=current_user.email,
            customer_phone=data.get('phone', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            pincode=data.get('pincode', ''),
            payment_method=data.get('payment_method', 'cod'),
            subtotal=subtotal,
            shipping=0,
            total=subtotal,
            status='confirmed'
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['id'],
                product_name=item['name'],
                price=float(item['price']),
                quantity=item['quantity'],
                subtotal=float(item['price']) * item['quantity']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # ✅ Send email confirmation (ADD THIS LINE)
        send_order_confirmation_email(order)
        
        # Clear cart
        session.pop('cart', None)
        
        return jsonify({
            'success': True, 
            'order_id': order.id,
            'order_number': order.order_number
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Checkout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500



def send_order_confirmation_email(order):
    try:
        user = User.query.get(order.user_id)
        
        # Render the template (this is CORRECT - uses Jinja2 properly)
        body = render_template('emails/order_confirmation.txt', order=order)
        
        msg = Message(
            subject=f"Order Confirmation - #{order.order_number}",
            recipients=[user.email]
        )
        msg.body = body
        mail.send(msg)
        print(f"✅ Email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        return False
    

@app.route('/order-confirmed/<int:order_id>')
@login_required
def order_confirmed(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    return render_template('order_confirmed.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    users = User.query.all()
    products = Product.query.all()
    return render_template('admin/dashboard.html', orders=orders, users=users, products=products)

# ========== ADMIN ROUTES - ADD THESE RIGHT AFTER YOUR EXISTING ADMIN ROUTES ==========

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        price = request.form.get('price')
        category = request.form.get('category')
        description = request.form.get('description')
        short_description = request.form.get('short_description', description[:100] if description else '')
        image = request.form.get('image', 'images/placeholder.jpg')
        brand = request.form.get('brand', 'Generic')
        stock = request.form.get('stock', 10)
        
        # Create new product
        product = Product(
            name=name,
            price=float(price) if price else 0,
            compare_price=float(request.form.get('compare_price', 0)) if request.form.get('compare_price') else None,
            discount=int(request.form.get('discount', 0)) if request.form.get('discount') else 0,
            category=category,
            description=description,
            short_description=short_description,
            image=image,
            brand=brand,
            stock=int(stock) if stock else 10,
            rating=4.5,
            reviews_count=0,
            featured=False
        )
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    categories = ['Appliances', 'Home & Kitchen', 'Fashion', 'Sports', 'Beauty', 'Toys', 'Books', 
                  'Furniture', 'Bags', 'Mobiles', 'Laptop', 'Watch', 'Men Dresses', 'Woman Dresses', 
                  'Decorations', 'Pets care', 'Bathing products', 'Skin care', 'Face care', 'Shoes', 
                  'Mens Accesories', 'Women Accesories', 'Gifts', 'Hair care']
    
    brands = ['Apple', 'Samsung', 'OnePlus', 'Google', 'Xiaomi', 'Nike', 'Adidas', 'Puma', 
              'Levi\'s', 'H&M', 'Zara', 'Arrow', 'US Polo', 'Raymond', 'Woodland']
    
    return render_template('admin/add_product.html', categories=categories, brands=brands)    

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/chats')
@login_required
@admin_required
def admin_chats():
    return render_template('admin/chats.html')




# ========== ADMIN PRODUCT EDIT ROUTE ==========
# Make sure you have ONLY ONE of these!

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now()}

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        # Update product with form data
        product.name = request.form.get('name', product.name)
        product.price = float(request.form.get('price')) if request.form.get('price') else product.price
        product.compare_price = float(request.form.get('compare_price')) if request.form.get('compare_price') else None
        product.discount = int(request.form.get('discount')) if request.form.get('discount') else 0
        product.category = request.form.get('category', product.category)
        product.brand = request.form.get('brand', product.brand)
        product.stock = int(request.form.get('stock')) if request.form.get('stock') else product.stock
        product.description = request.form.get('description', product.description)
        product.short_description = request.form.get('short_description', product.short_description)
        product.image = request.form.get('image', product.image)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    categories = ['Appliances', 'Home & Kitchen', 'Fashion', 'Sports', 'Beauty', 'Toys', 'Books', 
                  'Furniture', 'Bags', 'Mobiles', 'Laptop', 'Watch', 'Men Dresses', 'Woman Dresses', 
                  'Decorations', 'Pets care', 'Bathing products', 'Skin care', 'Face care', 'Shoes', 
                  'Mens Accesories', 'Women Accesories', 'Gifts', 'Hair care']
    
    brands = ['Apple', 'Samsung', 'OnePlus', 'Google', 'Xiaomi', 'Nike', 'Adidas', 'Puma', 
              'Levi\'s', 'H&M', 'Zara', 'Arrow', 'US Polo', 'Raymond', 'Woodland']
    
    return render_template('admin/edit_product.html', product=product, categories=categories, brands=brands)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/api/product/<int:product_id>')
def api_product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': url_for('static', filename=product.image),
        'description': product.short_description,
        'rating': product.rating,
        'reviews': product.reviews_count
    })    

@app.route('/admin/update-order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        status = request.json.get('status')
        order.status = status
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# At the top with other imports
from flask_mail import Mail, Message

# Add to your app configuration (around line 10-15)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Your Gmail
app.config['MAIL_PASSWORD'] = 'your-app-password'      # Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        user = User.query.get(order.user_id)
        
        # Create email body (NO f-string with Jinja!)
        subject = f"Order Confirmation - #{order.order_number}"
        
        # Build email body manually
        body = f"Dear {order.customer_name},\n\n"
        body += f"Thank you for your order! Order #{order.order_number} has been confirmed.\n\n"
        body += "Order Details:\n"
        body += "-" * 50 + "\n"
        
        # Loop through items (this is Python, not Jinja)
        for item in order.items:
            body += f"{item.product_name} x{item.quantity} = ₹{item.subtotal}\n"
        
        body += "-" * 50 + "\n"
        body += f"Subtotal: ₹{order.subtotal}\n"
        body += f"Shipping: ₹{order.shipping}\n"
        body += f"TOTAL: ₹{order.total}\n\n"
        body += f"Shipping Address: {order.address}, {order.city} - {order.pincode}\n\n"
        body += f"Track your order: {url_for('my_orders', _external=True)}\n\n"
        body += "Thank you for shopping with Triowise!"
        
        # Create and send email
        msg = Message(subject, recipients=[user.email])
        msg.body = body
        mail.send(msg)
        
        print(f"✅ Order confirmation email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False
    
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # ✅ Now 'remember' exists in the form
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            
            # Check if it's an AJAX request from popup
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'redirect': url_for('home')})
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data  # ✅ This will now work
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user, remember=remember)
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'redirect': url_for('home')
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid email or password.'
        })

@app.route('/api/register', methods=['POST'])
def api_register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role = request.form.get('role', 'user')
    
    # Validation
    if not all([name, email, password, confirm_password]):
        return jsonify({'success': False, 'error': 'All fields are required.'})
    
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match.'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters.'})
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered.'})
    
    # Create user
    user = User(
        name=name,
        email=email,
        role=role
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful! You can now login.',
        'email': email
    })



@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Here you would send an email with reset link
            flash('Password reset instructions sent to your email!', 'success')
        else:
            flash('Email not found!', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/api/filter-products', methods=['POST'])
def filter_products_api():
    data = request.get_json()
    
    query = Product.query
    
    # Apply filters
    if data.get('categories'):
        query = query.filter(Product.category.in_(data['categories']))
    
    if data.get('min_price'):
        query = query.filter(Product.price >= float(data['min_price']))
    
    if data.get('max_price'):
        query = query.filter(Product.price <= float(data['max_price']))
    
    if data.get('brands'):
        query = query.filter(Product.brand.in_(data['brands']))
    
    if data.get('min_rating'):
        query = query.filter(Product.rating >= float(data['min_rating']))
    
    # Sorting
    sort_by = data.get('sort_by', 'newest')
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    products = query.all()
    
    # Render HTML for products
    html = render_template('includes/product_grid.html', products=products)
    
    return jsonify({
        'success': True,
        'html': html,
        'count': len(products)
    })

@app.route('/debug-products')
def debug_products():
    products = Product.query.all()
    html = "<h1>Products in Database</h1>"
    html += "<table border='1' cellpadding='8'>"
    html += "<tr><th>ID</th><th>Name</th><th>Category</th><th>Price</th></tr>"
    for p in products:
        html += f"<tr><td>{p.id}</td><td>{p.name}</td><td>{p.category}</td><td>₹{p.price}</td></tr>"
    html += f"</table><p>Total: {len(products)} products</p>"
    return html

# Create tables and sample data
def create_sample_products():
    if Product.query.count() == 0:
        products = [
            # In your create_sample_products() function, add this section:


# ========== GIFTS (10 products) ==========
# Gift Hamper
Product(name='Luxury Gift Hamper', price=2499, compare_price=3499, discount=29,
       category='Gifts', brand='The Hamper Company', rating=4.8, reviews_count=1234,
       image='images/gifts_hamper.png',
       description='Beautifully curated luxury gift hamper with gourmet chocolates, premium nuts, artisanal cookies, and a bottle of fine wine. Perfect for corporate gifting or special occasions.',
       short_description='Luxury gourmet gift hamper'),

# Personalized Photo Frame
Product(name='Personalized Photo Frame', price=799, compare_price=1199, discount=33,
       category='Gifts', brand='Personalized', rating=4.6, reviews_count=2345,
       image='images/gifts_photoframe.png',
       description='Elegant wooden photo frame with personalized engraving. Can be customized with names, dates, or special messages. Perfect for weddings, anniversaries, or birthdays.',
       short_description='Personalized engraved photo frame'),

# Scented Candle Set
Product(name='Luxury Scented Candle Set', price=1299, compare_price=1899, discount=32,
       category='Gifts', brand='Yankee Candle', rating=4.7, reviews_count=1876,
       image='images/gifts_candles.png',
       description='Set of 3 luxury scented candles in elegant glass jars. Fragrances include vanilla, lavender, and sandalwood. Burns for up to 40 hours each.',
       short_description='Set of 3 luxury scented candles'),

# Jewelry Box
Product(name='Velvet Jewelry Box', price=1499, compare_price=2199, discount=32,
       category='Gifts', brand='Artisan', rating=4.6, reviews_count=987,
       image='images/gifts_jewelrybox.png',
       description='Elegant velvet jewelry box with multiple compartments. Features ring rolls, necklace hooks, and earring holders. Perfect for organizing precious jewelry.',
       short_description='Elegant velvet jewelry organizer'),

# Watch Gift Set
Product(name='Men\'s Watch Gift Set', price=3499, compare_price=4999, discount=30,
       category='Gifts', brand='Fossil', rating=4.7, reviews_count=1543,
       image='images/gifts_watchset.png',
       description='Complete gift set including premium analog watch, leather wallet, and cufflinks. Comes in elegant gift box. Perfect for birthdays or anniversaries.',
       short_description='Men\'s watch and accessories gift set'),

# Perfume Gift Set
Product(name='Women\'s Perfume Gift Set', price=3999, compare_price=5499, discount=27,
       category='Gifts', brand='Victoria\'s Secret', rating=4.8, reviews_count=2109,
       image='images/gifts_perfumeset.png',
       description='Luxury perfume gift set including 50ml Eau de Parfum, 100ml body lotion, and 100ml shower gel. Packaged in elegant gift box.',
       short_description='Women\'s perfume and body care gift set'),

# Chocolate Hamper
Product(name='Gourmet Chocolate Hamper', price=1899, compare_price=2699, discount=30,
       category='Gifts', brand='Ferrero Rocher', rating=4.8, reviews_count=3456,
       image='images/gifts_chocolate.png',
       description='Decadent chocolate hamper with Ferrero Rocher, Lindt truffles, Godiva chocolates, and artisanal pralines. Perfect for Valentine\'s Day or any special occasion.',
       short_description='Luxury gourmet chocolate hamper'),

# Spa Gift Set
Product(name='Relaxing Spa Gift Set', price=2199, compare_price=2999, discount=27,
       category='Gifts', brand='Bath & Body Works', rating=4.7, reviews_count=1234,
       image='images/gifts_spaset.png',
       description='Ultimate relaxation gift set with lavender bath salts, scented candles, body butter, foot cream, and a soft bathrobe. Comes in beautiful gift box.',
       short_description='Luxury spa and relaxation gift set'),

# Coffee Lover's Gift Set
Product(name='Coffee Lover\'s Gift Set', price=1599, compare_price=2199, discount=27,
       category='Gifts', brand='Starbucks', rating=4.6, reviews_count=876,
       image='images/gifts_coffee.png',
       description='Perfect for coffee enthusiasts! Includes premium coffee beans, French press, ceramic mug, and gourmet cookies. Beautifully packaged.',
       short_description='Coffee lover\'s complete gift set'),

# Anniversary Clock
Product(name='Engraved Anniversary Clock', price=2799, compare_price=3699, discount=24,
       category='Gifts', brand='Bulova', rating=4.7, reviews_count=654,
       image='images/gifts_clock.png',
       description='Elegant mantel clock with personalized engraving for anniversaries. Quartz movement, classic design, can be engraved with names and date.',
       short_description='Personalized engraved anniversary clock'),
# ========== BATHING PRODUCTS (10 products) ==========
# Body Wash
Product(name='Nivea Shower Gel', price=249, compare_price=349, discount=29,
       category='Bathing products', brand='Nivea', rating=4.6, reviews_count=4567,
       image='images/bath_showergel.png',
       description='Nourishing shower gel with almond oil. Keeps skin moisturized, refreshing fragrance, suitable for daily use. 500ml bottle.',
       short_description='Nourishing shower gel 500ml'),

# Bath Soap
Product(name='Dove Beauty Bar', price=199, compare_price=299, discount=33,
       category='Bathing products', brand='Dove', rating=4.7, reviews_count=6789,
       image='images/bath_soap.png',
       description='Moisturizing beauty cream bar with 1/4 moisturizing cream. Gentle on skin, suitable for face and body. Pack of 4.',
       short_description='Moisturizing beauty bar soap pack of 4'),

# Bath Sponge
Product(name='Exfoliating Bath Sponge', price=99, compare_price=149, discount=34,
       category='Bathing products', brand='Bath & Body Works', rating=4.4, reviews_count=1234,
       image='images/bath_sponge.png',
       description='Soft exfoliating bath sponge for gentle scrubbing. Creates rich lather, improves blood circulation, durable and quick-drying.',
       short_description='Exfoliating bath sponge'),

# Bath Towel
Product(name='Premium Cotton Bath Towel', price=599, compare_price=899, discount=33,
       category='Bathing products', brand='Bombay Dyeing', rating=4.6, reviews_count=2345,
       image='images/bath_towel.png',
       description='100% cotton premium bath towel, 650 GSM. Highly absorbent, soft texture, quick-drying. Size 70x140 cm.',
       short_description='Premium cotton bath towel'),

# Bath Mat
Product(name='Non-Slip Bath Mat', price=449, compare_price=649, discount=31,
       category='Bathing products', brand='Yantra', rating=4.5, reviews_count=876,
       image='images/bath_mat.png',
       description='Non-slip microfiber bath mat with quick-dry technology. Machine washable, anti-skid backing, available in multiple colors.',
       short_description='Non-slip quick-dry bath mat'),

# Bath Robe
Product(name='Cotton Terry Bath Robe', price=1499, compare_price=2199, discount=32,
       category='Bathing products', brand='Jockey', rating=4.7, reviews_count=1543,
       image='images/bath_robe.png',
       description='100% cotton terry bath robe with hood. Soft, absorbent, unisex design, two front pockets, adjustable belt. One size fits most.',
       short_description='Cotton terry bath robe'),

# Loofah
Product(name='Natural Loofah Scrubber', price=149, compare_price=199, discount=25,
       category='Bathing products', brand='EcoTools', rating=4.4, reviews_count=987,
       image='images/bath_loofah.png',
       description='Natural loofah scrubber for gentle exfoliation. Creates rich lather, biodegradable, with hanging cord for easy drying.',
       short_description='Natural exfoliating loofah'),

# Bath Salts
Product(name='Lavender Bath Salts', price=299, compare_price=449, discount=33,
       category='Bathing products', brand='Bath & Body Works', rating=4.5, reviews_count=765,
       image='images/bath_salts.png',
       description='Relaxing lavender scented bath salts with Epsom salt. Helps relieve stress, soothes muscles, softens skin. 500g jar.',
       short_description='Lavender relaxing bath salts'),

# Bath Brush
Product(name='Long Handle Bath Brush', price=249, compare_price=349, discount=29,
       category='Bathing products', brand='Yantra', rating=4.3, reviews_count=654,
       image='images/bath_brush.png',
       description='Long handle bath brush with soft bristles. Perfect for back scrubbing, removable head for easy cleaning, ergonomic handle.',
       short_description='Long handle back scrubber brush'),

# Bath Caddy
Product(name='Bamboo Bath Tray Caddy', price=1899, compare_price=2499, discount=24,
       category='Bathing products', brand='Stone & Beam', rating=4.7, reviews_count=432,
       image='images/bath_caddy.png',
       description='Adjustable bamboo bath tray for relaxing soaks. Holds book, tablet, wine glass, and candles. Expands to fit most tubs.',
       short_description='Bamboo bathtub caddy tray'),
# ========== PETS CARE (10 products) ==========
# Dog Food
Product(name='Pedigree Adult Dry Dog Food', price=1299, compare_price=1699, discount=24,
       category='Pets care', brand='Pedigree', rating=4.7, reviews_count=3456,
       image='images/pets_dogfood.png',
       description='3kg pack of nutritious dry dog food for adult dogs. With wholegrain, vitamins, and minerals for healthy digestion and strong bones.',
       short_description='Adult dog dry food 3kg'),

# Cat Food
Product(name='Whiskas Cat Dry Food', price=899, compare_price=1199, discount=25,
       category='Pets care', brand='Whiskas', rating=4.6, reviews_count=2341,
       image='images/pets_catfood.png',
       description='1.2kg pack of dry cat food with ocean fish flavor. Complete and balanced nutrition with essential vitamins and minerals.',
       short_description='Ocean fish cat food 1.2kg'),

# Dog Accessories
Product(name='Adjustable Dog Leash', price=399, compare_price=599, discount=33,
       category='Pets care', brand='Petmate', rating=4.5, reviews_count=1234,
       image='images/pets_leash.png',
       description='Durable nylon dog leash with comfortable handle. Adjustable length from 4-6 feet, strong metal clip, reflective stitching for night walks.',
       short_description='Adjustable reflective dog leash'),

# Pet Toys
Product(name='Interactive Dog Chew Toy', price=299, compare_price=449, discount=33,
       category='Pets care', brand='KONG', rating=4.8, reviews_count=1876,
       image='images/pests_toy.png',
       description='Durable rubber chew toy for dogs. Perfect for interactive play, treat dispensing, and dental health. Suitable for medium to large dogs.',
       short_description='Durable rubber dog chew toy'),

# Pet Grooming
Product(name='Pet Nail Clipper Set', price=349, compare_price=499, discount=30,
       category='Pets care', brand='Andis', rating=4.5, reviews_count=987,
       image='images/pets_nailclipper.png',
       description='Professional pet nail clipper with safety guard. Stainless steel blades, ergonomic non-slip handles, includes nail file.',
       short_description='Safety pet nail clipper'),

# Cat Accessories
Product(name='Cat Scratching Post', price=799, compare_price=1199, discount=33,
       category='Pets care', brand='PetFusion', rating=4.6, reviews_count=1543,
       image='images/pets_scratchingpost.png',
       description='Durable sisal cat scratching post with stable base. 60cm height, helps protect furniture, includes hanging toy.',
       short_description='Sisal cat scratching post'),

# Pet Beds
Product(name='Orthopedic Dog Bed', price=2499, compare_price=3499, discount=29,
       category='Pets care', brand='PetFusion', rating=4.7, reviews_count=2109,
       image='images/pets_dogbed.png',
       description='Memory foam orthopedic dog bed with washable cover. Provides joint relief for older dogs, anti-slip bottom, available in medium size.',
       short_description='Memory foam orthopedic dog bed'),

# Pet Carriers
Product(name='Pet Travel Carrier', price=1899, compare_price=2499, discount=24,
       category='Pets care', brand='Sherpa', rating=4.5, reviews_count=876,
       image='images/pets_carrier.png',
       description='Airline-approved pet carrier for small dogs and cats. Ventilated mesh panels, padded shoulder strap, machine washable liner.',
       short_description='Airline-approved pet carrier'),

# Pet Bowls
Product(name='Stainless Steel Pet Bowls', price=449, compare_price=649, discount=31,
       category='Pets care', brand='Neater Pets', rating=4.6, reviews_count=1234,
       image='images/pets_bowls.png',
       description='Set of 2 stainless steel pet bowls with non-skid base. Rust-proof, dishwasher safe, 2-cup capacity each.',
       short_description='Non-skid stainless steel pet bowls'),

# Pet Supplements
Product(name='Dog Joint Supplements', price=899, compare_price=1299, discount=31,
       category='Pets care', brand='Nutri-Vet', rating=4.5, reviews_count=765,
       image='images/pets_supplements.png',
       description='Joint health supplements for dogs with glucosamine and chondroitin. Supports healthy joints and mobility, chewable tablets.',
       short_description='Glucosamine joint supplements for dogs'),
# ========== BAGS (5 products) ==========
# Backpacks
Product(name='Travel Laptop Backpack', price=2499, compare_price=3999, discount=38,
       category='Bags', brand='American Tourister', rating=4.6, reviews_count=2345,
       image='images/bags_backpack.png',
       description='Water-resistant laptop backpack with USB charging port. Fits up to 15.6-inch laptop, multiple compartments, padded shoulder straps, luggage strap.',
       short_description='USB charging laptop backpack'),

# Handbags
Product(name='Women\'s Tote Handbag', price=3299, compare_price=4999, discount=34,
       category='Bags', brand='Lavie', rating=4.5, reviews_count=1876,
       image='images/bags_tote.png',
       description='Stylish tote bag for women with gold-toned hardware. PU leather, spacious main compartment, inner zip pocket, adjustable shoulder straps.',
       short_description='Elegant tote bag for women'),

# Messenger Bags
Product(name='Men\'s Messenger Bag', price=1899, compare_price=2999, discount=37,
       category='Bags', brand='Wildcraft', rating=4.4, reviews_count=1543,
       image='images/bags_messenger.png',
       description='Canvas messenger bag with multiple pockets. Adjustable shoulder strap, water-resistant, perfect for office or college.',
       short_description='Canvas messenger bag for men'),

# Duffel Bags
Product(name='Gym Duffle Bag', price=1499, compare_price=2499, discount=40,
       category='Bags', brand='Puma', rating=4.5, reviews_count=2109,
       image='images/bags_duffle.png',
       description='Sports duffle bag for gym and travel. Water-resistant fabric, separate shoe compartment, wet pocket, adjustable shoulder strap.',
       short_description='Sports duffle bag for gym'),

# Crossbody Bags
Product(name='Mini Crossbody Bag', price=1299, compare_price=1999, discount=35,
       category='Bags', brand='Fossil', rating=4.7, reviews_count=1234,
       image='images/bags_crossbody.png',
       description='Genuine leather mini crossbody bag. Compact design with adjustable strap, front pocket, perfect for evenings and parties.',
       short_description='Genuine leather crossbody bag'),            
# ========== BEAUTY (5 products) ==========
# Skincare
Product(name='Vitamin C Face Serum', price=899, compare_price=1499, discount=40,
       category='Beauty', brand='Minimalist', rating=4.7, reviews_count=3456,
       image='images/beauty_serum.png',
       description='10% Vitamin C face serum with Hyaluronic Acid. Brightens skin, reduces dark spots, improves texture. Suitable for all skin types.',
       short_description='Brightening vitamin C serum'),

# Makeup
Product(name='Matte Liquid Lipstick', price=499, compare_price=899, discount=45,
       category='Beauty', brand='Sugar Cosmetics', rating=4.5, reviews_count=2341,
       image='images/beauty_lipstick.png',
       description='Long-lasting matte liquid lipstick with intense color payoff. Transfer-proof, smudge-proof, available in 12 shades.',
       short_description='Long-lasting matte lipstick'),

# Skincare
Product(name='Niacinamide Face Wash', price=299, compare_price=499, discount=40,
       category='Beauty', brand='Minimalist', rating=4.6, reviews_count=1876,
       image='images/beauty_facewash.png',
       description='5% Niacinamide face wash for oily and acne-prone skin. Controls oil, reduces pores, gentle cleansing.',
       short_description='Niacinamide face wash for acne'),

# Hair Care
Product(name='Argan Hair Mask', price=599, compare_price=999, discount=40,
       category='Beauty', brand='Mamaearth', rating=4.5, reviews_count=1543,
       image='images/beauty_hairmask.png',
       description='Deep conditioning hair mask with Argan oil. Repairs damaged hair, adds shine, reduces frizz. Suitable for all hair types.',
       short_description='Deep conditioning hair mask'),

# Fragrance
Product(name='Women\'s Perfume', price=2499, compare_price=3999, discount=38,
       category='Beauty', brand='Victoria\'s Secret', rating=4.8, reviews_count=2890,
       image='images/beauty_perfume.png',
       description='Bombshell perfume with notes of purple passion fruit, Shangri-la peony, and vanilla orchid. Long-lasting fragrance.',
       short_description='Long-lasting women\'s perfume'),
     # ========== FASHION (5 products) ==========
# Men's Fashion
Product(name='Men\'s Premium Cotton T-Shirt', price=899, compare_price=1499, discount=40,
       category='Fashion', brand='US Polo', rating=4.5, reviews_count=2345,
       image='images/fashion_tshirt.png',
       description='Premium cotton crewneck t-shirt with logo embroidery. Soft fabric, regular fit, available in black, white, navy, and grey.',
       short_description='Premium cotton t-shirt for men'),

Product(name='Women\'s Floral Maxi Dress', price=2499, compare_price=3999, discount=38,
       category='Fashion', brand='H&M', rating=4.6, reviews_count=1876,
       image='images/fashion_maxidress.png',
       description='Beautiful floral print maxi dress with adjustable straps. Lightweight fabric, flowy silhouette, perfect for summer and parties.',
       short_description='Elegant floral maxi dress'),

Product(name='Men\'s Slim Fit Jeans', price=1999, compare_price=2999, discount=33,
       category='Fashion', brand='Levi\'s', rating=4.4, reviews_count=3124,
       image='images/fashion_jeans.png',
       description='Classic slim fit jeans with stretch comfort. 5-pocket styling, durable denim, available in dark blue and black.',
       short_description='Slim fit stretch jeans for men'),

Product(name='Women\'s Handbag', price=3499, compare_price=4999, discount=30,
       category='Fashion', brand='Lavie', rating=4.5, reviews_count=1543,
       image='images/fashion_handbag.png',
       description='Premium synthetic leather handbag with gold-toned hardware. Multiple compartments, adjustable shoulder strap, perfect for daily use.',
       short_description='Stylish handbag for women'),

Product(name='Unisex Sunglasses', price=1299, compare_price=2499, discount=48,
       category='Fashion', brand='Ray-Ban', rating=4.7, reviews_count=2890,
       image='images/fashion_sunglasses.png',
       description='Classic aviator style sunglasses with UV400 protection. Metal frame, polarized lenses, unisex design.',
       short_description='UV protected aviator sunglasses'),
    # ... your existing products ...
    
    # ========== TRENDING APPLIANCES (10 products) ==========
    # Kitchen Appliances
    Product(name='Philips Air Fryer HD9252', price=8999, compare_price=10999, discount=18,
           category='Appliances', brand='Philips', rating=4.7, reviews_count=2345,
           image='images/appliance_airfryer.png',
           description='Rapid Air Technology for healthy frying with up to 90% less fat. 4.1L capacity, digital touchscreen with 7 presets, keep warm function.',
           short_description='Healthy air fryer with 4.1L capacity'),
    
    Product(name='Samsung Microwave Oven', price=7499, compare_price=8999, discount=17,
           category='Appliances', brand='Samsung', rating=4.6, reviews_count=1876,
           image='images/appliance_microwave.png',
           description='28L convection microwave with ceramic enamel interior, 6 cooking modes, auto cook menu, eco mode.',
           short_description='28L convection microwave oven'),
    
    Product(name='Morphy Richards Toaster', price=2499, compare_price=3299, discount=24,
           category='Appliances', brand='Morphy Richards', rating=4.5, reviews_count=987,
           image='images/appliance_toaster.png',
           description='2-slice stainless steel toaster with 6 browning levels, defrost and reheat function, removable crumb tray.',
           short_description='2-slice toaster with 6 browning levels'),
    
    Product(name='Bajaj 1000W Mixer Grinder', price=3499, compare_price=4299, discount=19,
           category='Appliances', brand='Bajaj', rating=4.4, reviews_count=1567,
           image='images/appliance_mixer.png',
           description='1000W motor, 3 stainless steel jars, turbo vent technology, overload protection.',
           short_description='1000W powerful mixer grinder'),
    
    Product(name='Prestige Electric Kettle', price=1299, compare_price=1699, discount=24,
           category='Appliances', brand='Prestige', rating=4.5, reviews_count=2341,
           image='images/appliance_kettle.png',
           description='1.5L stainless steel kettle, 1500W fast boiling, auto shut-off, boil-dry protection.',
           short_description='1.5L fast boiling electric kettle'),
    
    # Home Appliances
    Product(name='Dyson Vacuum Cleaner V15', price=54999, compare_price=59999, discount=8,
           category='Appliances', brand='Dyson', rating=4.8, reviews_count=1234,
           image='images/appliance_vacuum.png',
           description='Cordless vacuum with laser detection, 60-minute runtime, HEPA filtration, 5-stage filtration system.',
           short_description='Cordless vacuum with laser detection'),
    
    Product(name='Havells Air Purifier', price=14999, compare_price=17999, discount=17,
           category='Appliances', brand='Havells', rating=4.5, reviews_count=876,
           image='images/appliance_airpurifier.png',
           description='HEPA filter with 4-stage purification, coverage up to 400 sq.ft, air quality indicator, 360° air intake.',
           short_description='HEPA air purifier for home'),
    
    Product(name='Blue Star Air Conditioner', price=38999, compare_price=42999, discount=9,
           category='Appliances', brand='Blue Star', rating=4.6, reviews_count=1543,
           image='images/appliance_ac.png',
           description='1.5 ton 5-star inverter split AC, copper condenser, turbo cool, anti-dust filter, stabilizer-free operation.',
           short_description='1.5 ton 5-star inverter AC'),
    
    Product(name='Whirlpool Refrigerator', price=28999, compare_price=32999, discount=12,
           category='Appliances', brand='Whirlpool', rating=4.5, reviews_count=2109,
           image='images/appliance_fridge.png',
           description='240L direct-cool single door refrigerator, 6th Sense technology, adaptive intelligence, anti-bacterial gasket.',
           short_description='240L direct-cool refrigerator'),
    
    Product(name='IFB Washing Machine', price=27999, compare_price=31999, discount=13,
           category='Appliances', brand='IFB', rating=4.6, reviews_count=1876,
           image='images/appliance_washingmachine.png',
           description='7kg front load washing machine, 8 wash programs, auto-dispense, steam wash, inverter motor.',
           short_description='7kg front load washing machine'),
    
    # ... rest of your products ...


            # ========== BOOKS (5 products) ==========
Product(name='The Psychology of Money', price=399, compare_price=499, discount=20,
       category='Books', brand='Jaico Publishing', rating=4.8, reviews_count=3456,
       image='images/book_psychology_money.png',
       description='Timeless lessons on wealth, greed, and happiness. Morgan Housel shares 19 short stories exploring the strange ways people think about money.',
       short_description='Bestseller on wealth and happiness'),

Product(name='Atomic Habits', price=450, compare_price=599, discount=25,
       category='Books', brand='Penguin Random House', rating=4.9, reviews_count=5678,
       image='images/book_atomic_habits.png',
       description='An Easy & Proven Way to Build Good Habits & Break Bad Ones. James Clear reveals practical strategies that will teach you how to form good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.',
       short_description='#1 Bestseller on habit formation'),

Product(name='Rich Dad Poor Dad', price=350, compare_price=450, discount=22,
       category='Books', brand='Plata Publishing', rating=4.7, reviews_count=4321,
       image='images/book_rich_dad.png',
       description='What the Rich Teach Their Kids About Money That the Poor and Middle Class Do Not! Robert Kiyosaki shares the story of his two dads and the lessons about money and investing.',
       short_description='Personal finance classic'),

Product(name='The Alchemist', price=299, compare_price=399, discount=25,
       category='Books', brand='HarperOne', rating=4.8, reviews_count=7890,
       image='images/book_alchemist.png',
       description='Paulo Coelho\'s masterpiece tells the mystical story of Santiago, an Andalusian shepherd boy who yearns to travel in search of a worldly treasure. His journey teaches us about the essential wisdom of listening to our hearts.',
       short_description='International bestselling novel'),

Product(name='Think and Grow Rich', price=249, compare_price=349, discount=29,
       category='Books', brand='Napoleon Hill Foundation', rating=4.6, reviews_count=2345,
       image='images/book_think_grow.png',
       description='Napoleon Hill\'s classic book reveals the secrets to success based on studying over 500 millionaires. The 13 principles outlined in this book have helped countless people achieve their dreams.',
       short_description='Classic success philosophy'),
           
            
            # ========== LAPTOPS (5 products) ==========
            Product(name='Apple 2024 MacBook Pro"', price=249999, compare_price=269999, discount=7,
                   category='Laptop', brand='Apple', rating=4.9, reviews_count=3452,
                   image='images/macbook.png',
                   description='Apple M3 Max chip, 48GB RAM, 1TB SSD, 16-inch Liquid Retina XDR display, 22-hour battery.',
                   short_description='Ultimate professional laptop'),
            
            Product(name='Dell XPS 15', price=189999, compare_price=199999, discount=5,
                   category='Laptop', brand='Dell', rating=4.8, reviews_count=2341,
                   image='images/dell.png',
                   description='Intel i9-13900H, 32GB RAM, 1TB SSD, NVIDIA RTX 4060, 4K OLED touch display.',
                   short_description='Premium laptop for professionals'),
            
            Product(name='HP Spectre x360', price=149999, compare_price=159999, discount=6,
                   category='Laptop', brand='HP', rating=4.6, reviews_count=1234,
                   image='images/hp.png',
                   description='2-in-1 convertible, Intel i7, 16GB RAM, 1TB SSD, OLED touchscreen.',
                   short_description='Versatile 2-in-1 laptop'),
            
            Product(name='ASUS ROG Zephyrus G14', price=149999, compare_price=159999, discount=6,
                   category='Laptop', brand='ASUS', rating=4.6, reviews_count=987,
                   image='images/asus.png',
                   description='AMD Ryzen 9, 32GB RAM, 1TB SSD, NVIDIA RTX 4060, 120Hz QHD display.',
                   short_description='Compact gaming powerhouse'),
            
            Product(name='Lenovo LOQ', price=129999, compare_price=139999, discount=7,
                   category='Laptop', brand='Lenovo', rating=4.5, reviews_count=876,
                   image='images/Lenova_Loq.png',
                   description='AMD Ryzen 7, 16GB RAM, 1TB SSD, NVIDIA RTX 3070, 165Hz QHD display.',
                   short_description='Best gaming laptop under 1.5 lakhs'),
            
            # ========== WATCHES (5 products) ==========
            Product(name='Apple Watch Ultra 2', price=89999, compare_price=94999, discount=5,
                   category='Watch', brand='Apple', rating=4.8, reviews_count=2345,
                   image='images/applewatch.png',
                   description='49mm titanium case, GPS + Cellular, Always-On display, 100m water resistance.',
                   short_description='Ultimate sports watch'),
            
            Product(name='Samsung Galaxy Watch 6 Classic', price=39999, compare_price=44999, discount=11,
                   category='Watch', brand='Samsung', rating=4.5, reviews_count=1876,
                   image='images/samsungwatch.png',
                   description='47mm, Super AMOLED, rotating bezel, ECG, blood pressure monitoring.',
                   short_description='Classic design with modern features'),
            
            Product(name='Garmin Fenix 7', price=69999, compare_price=74999, discount=7,
                   category='Watch', brand='Garmin', rating=4.7, reviews_count=654,
                   image='images/garmin.png',
                   description='1.3" solar display, multi-band GPS, topo maps, 28-day battery life.',
                   short_description='Premium multisport GPS watch'),
            
            Product(name='Fossil Gen 6', price=24999, compare_price=27999, discount=11,
                   category='Watch', brand='Fossil', rating=4.3, reviews_count=567,
                   image='images/fossil.png',
                   description='Wear OS, heart rate tracking, GPS, Google Assistant.',
                   short_description='Stylish smartwatch'),
            
            Product(name='Amazfit GTR 4', price=14999, compare_price=16999, discount=12,
                   category='Watch', brand='Amazfit', rating=4.5, reviews_count=456,
                   image='images/amazfit.png',
                   description='GPS, bio-tracking sensor, 14-day battery life, always-on display.',
                   short_description='Premium fitness watch'),
            
            # ========== MEN DRESSES (5 products) ==========
            Product(name='Men\'s Casual Shirt', price=899, compare_price=1299, discount=31,
                   category='Men Dresses', brand='Levi\'s', rating=4.3, reviews_count=456,
                   image='images/casualshirt.png',
                   description='100% cotton, regular fit, perfect for casual occasions. Available in multiple colors.',
                   short_description='Comfortable casual shirt'),
            
            Product(name='Men\'s Formal Blazer', price=3999, compare_price=5999, discount=33,
                   category='Men Dresses', brand='Arrow', rating=4.5, reviews_count=234,
                   image='images/formalshirt.png',
                   description='Premium formal blazer for office and parties. Made from high-quality polyester blend.',
                   short_description='Elegant formal blazer'),
            
            Product(name='Men\'s Slim Fit Jeans', price=1999, compare_price=2999, discount=33,
                   category='Men Dresses', brand='Lee', rating=4.4, reviews_count=678,
                   image='images/jean.png',
                   description='Slim fit jeans, stretchable fabric, 5-pocket styling, available in dark blue and black.',
                   short_description='Comfortable slim fit jeans'),
            
            Product(name='Men\'s Sports Shoes', price=2499, compare_price=3499, discount=29,
                   category='Shoes', brand='Nike', rating=4.5, reviews_count=789,
                   image='images/sports.png',
                   description='Running shoes with air cushioning, breathable mesh upper, durable rubber outsole.',
                   short_description='Comfortable running shoes'),
            
            Product(name='Men\'s Leather Jacket', price=4999, compare_price=7999, discount=38,
                   category='Men Dresses', brand='Woodland', rating=4.3, reviews_count=345,
                   image='images/leatherjacket.png',
                   description='Genuine leather jacket, zip closure, multiple pockets, perfect for winter.',
                   short_description='Stylish leather jacket'),
            
            # ========== WOMEN DRESSES (5 products) ==========
            Product(name='Women\'s Ethnic Kurta', price=1299, compare_price=2499, discount=48,
                   category='Woman Dresses', brand='Biba', rating=4.4, reviews_count=678,
                   image='images/akkadress1.png',
                   description='Beautiful ethnic wear for festivals and parties. Cotton silk fabric with embroidery.',
                   short_description='Traditional kurta with modern design'),
            
            Product(name='Women\'s Maxi Dress', price=1899, compare_price=2999, discount=37,
                   category='Woman Dresses', brand='H&M', rating=4.2, reviews_count=345,
                   image='images/akkadress2.png',
                   description='Floral print maxi dress for summer. Lightweight fabric with adjustable straps.',
                   short_description='Elegant floral dress'),
            
            Product(name='Women\'s Handbag', price=2499, compare_price=3499, discount=29,
                   category='Women Accesories', brand='Lavie', rating=4.3, reviews_count=456,
                   image='images/handbag.png',
                   description='Premium synthetic leather handbag, multiple compartments, adjustable shoulder strap.',
                   short_description='Stylish handbag for women'),
            
            Product(name='Women\'s Heels', price=1999, compare_price=2999, discount=33,
                   category='Woman Dresses', brand='Bata', rating=4.2, reviews_count=234,
                   image='images/heels.png',
                   description='Elegant high heels for parties. Cushioned insole for comfort, durable sole.',
                   short_description='Comfortable party heels'),
            
            Product(name='Women\'s Watch', price=3999, compare_price=4999, discount=20,
                   category='Watch', brand='Fossil', rating=4.5, reviews_count=567,
                   image='images/womenwatch.png',
                   description='Elegant analog watch with stainless steel strap. Rose gold finish.',
                   short_description='Stylish women\'s watch'),
            
            # ========== FASHION ACCESSORIES (5 products) ==========
            Product(name='Men\'s Leather Belt', price=799, compare_price=1299, discount=38,
                   category='Mens Accesories', brand='Arrow', rating=4.3, reviews_count=234,
                   image='images/leatherbelt.png',
                   description='Genuine leather belt with automatic buckle. Available in black and brown.',
                   short_description='Premium leather belt'),
            
            Product(name='Women\'s Sunglasses', price=1499, compare_price=1999, discount=25,
                   category='Women Accesories', brand='Ray-Ban', rating=4.6, reviews_count=345,
                   image='images/coolingglass.png',
                   description='UV protection, polarized lenses, stylish design for women.',
                   short_description='Stylish sunglasses'),
            
            Product(name='Men\'s Wallet', price=599, compare_price=999, discount=40,
                   category='Mens Accesories', brand='Tommy Hilfiger', rating=4.4, reviews_count=456,
                   image='images/wallet.png',
                   description='Genuine leather wallet with multiple card slots and currency compartment.',
                   short_description='Slim leather wallet'),
            
            Product(name='Silk Scarf', price=899, compare_price=1499, discount=40,
                   category='Women Accesories', brand='Vero Moda', rating=4.3, reviews_count=123,
                   image='images/scraf.png',
                   description='Luxurious silk scarf with printed design. Perfect accessory for any outfit.',
                   short_description='Elegant silk scarf'),
            
            Product(name='Men\'s Tie Set', price=699, compare_price=999, discount=30,
                   category='Mens Accesories', brand='Arrow', rating=4.2, reviews_count=89,
                   image='images/tie.png',
                   description='Premium silk tie with matching pocket square. Perfect for formal occasions.',
                   short_description='Formal tie set'),
            
            # ========== SHOES (5 products) ==========
            Product(name='Nike Air Max 270', price=8995, compare_price=9995, discount=10,
                   category='Shoes', brand='Nike', rating=4.7, reviews_count=890,
                   image='images/airmax.png',
                   description='Men\'s running shoes with Air Max cushioning, breathable mesh upper.',
                   short_description='Comfortable running shoes'),
            
            Product(name='Adidas Ultraboost', price=11999, compare_price=13999, discount=14,
                   category='Shoes', brand='Adidas', rating=4.6, reviews_count=678,
                   image='images/addidas.png',
                   description='Men\'s running shoes with Boost technology, energy-returning midsole.',
                   short_description='Premium running shoes'),
            
            Product(name='Puma Casual Sneakers', price=3499, compare_price=3999, discount=13,
                   category='Shoes', brand='Puma', rating=4.4, reviews_count=456,
                   image='images/puma.png',
                   description='Unisex casual sneakers, lightweight and comfortable for daily wear.',
                   short_description='Stylish casual sneakers'),
            
            Product(name='Woodland Boots', price=5499, compare_price=6999, discount=21,
                   category='Shoes', brand='Woodland', rating=4.5, reviews_count=345,
                   image='images/woodland.png',
                   description='Men\'s leather boots, waterproof, perfect for trekking and outdoor activities.',
                   short_description='Durable leather boots'),
            
            Product(name='Bata Formal Shoes', price=2499, compare_price=2999, discount=17,
                   category='Shoes', brand='Bata', rating=4.3, reviews_count=234,
                   image='images/formalshoe.png',
                   description='Men\'s formal leather shoes, perfect for office wear and parties.',
                   short_description='Elegant formal shoes'),
            
            # ========== HOME & KITCHEN (5 products) ==========
            Product(name='Prestige Pressure Cooker', price=2499, compare_price=2999, discount=17,
                   category='Home & Kitchen', brand='Prestige', rating=4.5, reviews_count=678,
                   image='images/prestige.png',
                   description='5-liter stainless steel pressure cooker with safety valve.',
                   short_description='Premium pressure cooker'),
            
            Product(name='Butterfly Mixer Grinder', price=3299, compare_price=3799, discount=13,
                   category='Home & Kitchen', brand='Butterfly', rating=4.4, reviews_count=456,
                   image='images/mixer.png',
                   description='750W motor, 3 jars, stainless steel blades, kitchen essential.',
                   short_description='Powerful mixer grinder'),
            
            Product(name='Borosil Glass Set', price=1499, compare_price=1999, discount=25,
                   category='Home & Kitchen', brand='Borosil', rating=4.5, reviews_count=234,
                   image='images/glasscup.png',
                   description='6-piece dinner set, microwave and dishwasher safe.',
                   short_description='Elegant dinner set'),
            
            Product(name='Non-stick Cookware Set', price=3999, compare_price=4999, discount=20,
                   category='Home & Kitchen', brand='Prestige', rating=4.4, reviews_count=345,
                   image='images/panset.png',
                   description='5-piece non-stick cookware set including frying pans and saucepans.',
                   short_description='Complete cookware set'),
            
            Product(name='Electric Kettle', price=1299, compare_price=1499, discount=13,
                   category='Home & Kitchen', brand='Philips', rating=4.5, reviews_count=567,
                   image='images/waterhot.png',
                   description='1.5L stainless steel electric kettle with auto shut-off.',
                   short_description='Fast boiling kettle'),
            
            # ========== FURNITURE (5 products) ==========
            Product(name='Office Chair', price=7999, compare_price=9999, discount=20,
                   category='Furniture', brand='Featherlite', rating=4.3, reviews_count=234,
                   image='images/officechair.png',
                   description='Ergonomic office chair with lumbar support and adjustable height.',
                   short_description='Comfortable office chair'),
            
            Product(name='Wooden Study Table', price=5999, compare_price=6999, discount=14,
                   category='Furniture', brand='Nilkamal', rating=4.2, reviews_count=156,
                   image='images/studytable.png',
                   description='Engineered wood study table with drawer, perfect for home office.',
                   short_description='Spacious study table'),
            
            Product(name='3-Seater Sofa', price=24999, compare_price=29999, discount=17,
                   category='Furniture', brand='Urban Ladder', rating=4.5, reviews_count=345,
                   image='images/sofa.png',
                   description='Fabric sofa with wooden frame, comfortable cushions, modern design.',
                   short_description='Comfortable 3-seater sofa'),
            
            Product(name='Queen Size Bed', price=29999, compare_price=34999, discount=14,
                   category='Furniture', brand='Wakefit', rating=4.6, reviews_count=234,
                   image='images/bed.png',
                   description='Engineered wood bed with storage, includes mattress.',
                   short_description='Spacious queen bed with storage'),
            
            Product(name='Bookshelf', price=8999, compare_price=9999, discount=10,
                   category='Furniture', brand='IKEA', rating=4.4, reviews_count=189,
                   image='images/bookself.png',
                   description='5-tier wooden bookshelf, perfect for home library.',
                   short_description='Modern bookshelf'),
            
            # ========== DECORATIONS (5 products) ==========
            Product(name='Modern Table Lamp', price=1299, compare_price=1999, discount=35,
                   category='Decorations', brand='Philips', rating=4.6, reviews_count=189,
                   image='images/lamp.png',
                   description='Modern table lamp with sleek design. LED bulb included.',
                   short_description='Elegant table lamp'),
            
            Product(name='Wall Art Canvas', price=2499, compare_price=3499, discount=29,
                   category='Decorations', brand='Artify', rating=4.3, reviews_count=167,
                   image='images/art.png',
                   description='Beautiful canvas art for home decoration. 24x36 inches, ready to hang.',
                   short_description='Artistic wall decor'),
            
            Product(name='Artificial Plant', price=599, compare_price=899, discount=33,
                   category='Decorations', brand='Green Decor', rating=4.2, reviews_count=123,
                   image='images/plasticplant.png',
                   description='Low maintenance artificial plant for home decor.',
                   short_description='Artificial plant'),
            
            Product(name='Wall Clock', price=899, compare_price=1299, discount=31,
                   category='Decorations', brand='Ajanta', rating=4.3, reviews_count=234,
                   image='images/clock.png',
                   description='Modern design, silent movement, wall clock.',
                   short_description='Stylish wall clock'),
            
            Product(name='water_purifier', price=1499, compare_price=1999, discount=25,
                   category='Decorations', brand='IKEA', rating=4.5, reviews_count=145,
                   image='images/water_purifier.png',
                   description='Wooden photo frame collage with 6 frames. Perfect for family photos.',
                   short_description='Beautiful photo frame set'),
            
            # ========== BEAUTY & PERSONAL CARE (5 products) ==========
            Product(name='Face Cream', price=399, compare_price=599, discount=33,
                   category='Face care', brand='Nivea', rating=4.3, reviews_count=567,
                   image='images/cream.png',
                   description='Moisturizing face cream for all skin types, SPF 15.',
                   short_description='Hydrating face cream'),
            
            Product(name='Hair Dryer', price=1499, compare_price=1999, discount=25,
                   category='Hair care', brand='Philips', rating=4.4, reviews_count=345,
                   image='images/hairdryer.png',
                   description='1600W hair dryer with ionic technology, 3 heat settings.',
                   short_description='Professional hair dryer'),
            
            Product(name='Men\'s Trimmer', price=1299, compare_price=1699, discount=24,
                   category='Bathing products', brand='Philips', rating=4.5, reviews_count=678,
                   image='images/trimmer.png',
                   description='Cordless trimmer with 5 length settings, washable blades.',
                   short_description='Precision beard trimmer'),
            
            Product(name='Face Wash', price=199, compare_price=299, discount=33,
                   category='Face care', brand='Himalaya', rating=4.3, reviews_count=456,
                   image='images/facewash.png',
                   description='Neem face wash for acne-prone skin, oil control formula.',
                   short_description='Natural face wash'),
            
            Product(name='Jaguar (Perfume for Men)', price=2499, compare_price=2999, discount=17,
                   category='Mens Accesories', brand='Davidoff', rating=4.6, reviews_count=234,
                   image='images/jaguar.png',
                   description='Long-lasting fragrance with woody and citrus notes.',
                   short_description='Premium men\'s perfume'),
            
            # ========== SPORTS & FITNESS (5 products) ==========
            Product(name='Yoga Mat', price=799, compare_price=999, discount=20,
                   category='Sports', brand='Puma', rating=4.4, reviews_count=345,
                   image='images/yogamat.png',
                   description='Non-slip yoga mat, 6mm thickness, carrying strap included.',
                   short_description='Comfortable yoga mat'),
            
            Product(name='Dumbbell Set', price=2999, compare_price=3499, discount=14,
                   category='Sports', brand='Cosco', rating=4.5, reviews_count=234,
                   image='images/dumbells.png',
                   description='10kg adjustable dumbbell set with 2 dumbbells and weights.',
                   short_description='Home gym dumbbell set'),
            
            Product(name='Cricket Bat', price=1999, compare_price=2499, discount=20,
                   category='Sports', brand='SG', rating=4.4, reviews_count=189,
                   image='images/cricket.png',
                   description='English willow cricket bat, full size, with cover.',
                   short_description='Professional cricket bat'),
            
            Product(name='Football', price=899, compare_price=1099, discount=18,
                   category='Sports', brand='Nivia', rating=4.3, reviews_count=156,
                   image='images/football.png',
                   description='Size 5 football, machine-stitched, durable outer cover.',
                   short_description='High-quality football'),
            
            Product(name='Tennis Racket', price=2499, compare_price=2999, discount=17,
                   category='Sports', brand='Yonex', rating=4.5, reviews_count=123,
                   image='images/tennis.png',
                   description='Graphite tennis racket, lightweight, with cover.',
                   short_description='Professional tennis racket'),
            
            # ========== TOYS & GAMES (5 products) ==========
            Product(name='LEGO City Set', price=3499, compare_price=3999, discount=13,
                   category='Toys', brand='LEGO', rating=4.8, reviews_count=456,
                   image='images/set.png',
                   description='600+ pieces building set for kids age 6+.',
                   short_description='Creative building blocks'),
            
            Product(name='Remote Control Car', price=1299, compare_price=1699, discount=24,
                   category='Toys', brand='Hot Wheels', rating=4.4, reviews_count=234,
                   image='images/remotecontrol.png',
                   description='High-speed RC car with rechargeable battery.',
                   short_description='Fast remote control car'),
            
            Product(name='Chess Board', price=599, compare_price=799, discount=25,
                   category='Toys', brand='Parker', rating=4.5, reviews_count=189,
                   image='images/chess.png',
                   description='Wooden chess board with magnetic pieces, foldable design.',
                   short_description='Classic wooden chess set'),
            
            Product(name='Barbie Doll', price=899, compare_price=1199, discount=25,
                   category='Toys', brand='Barbie', rating=4.6, reviews_count=345,
                   image='images/barbie.png',
                   description='Fashion doll with accessories and outfit.',
                   short_description='Beautiful Barbie doll'),
            
            Product(name='Board Game - Monopoly', price=1499, compare_price=1799, discount=17,
                   category='Toys', brand='Monopoly', rating=4.7, reviews_count=234,
                   image='images/monopoly.png',
                   description='Classic family board game, 2-6 players.',
                   short_description='Fun family board game'),


            # ========== MOBILES - Premium iPhones ==========
Product(name='iPhone 13', price=54999, compare_price=59999, discount=8,
       category='Mobiles', brand='Apple', rating=4.7, reviews_count=8765,
       image='images/mobile_iphone13.png',
       description='6.1-inch Super Retina XDR display, A15 Bionic chip, Dual 12MP camera system, Ceramic Shield, 5G capable, All-day battery life.',
       short_description='Apple iPhone 13 - 128GB'),

Product(name='iPhone 14', price=62999, compare_price=69999, discount=10,
       category='Mobiles', brand='Apple', rating=4.7, reviews_count=6543,
       image='images/mobile_iphone14.png',
       description='6.1-inch Super Retina XDR display, A15 Bionic chip with 5-core GPU, Advanced dual-camera system, Action mode video, Crash Detection, 5G.',
       short_description='Apple iPhone 14 - 128GB'),

Product(name='iPhone 15 Pro', price=134999, compare_price=149999, discount=10,
       category='Mobiles', brand='Apple', rating=4.8, reviews_count=4321,
       image='images/mobile_iphone15pro.png',
       description='6.1-inch Super Retina XDR display with ProMotion, A17 Pro chip, Titanium design, 48MP main camera, USB-C, Action button.',
       short_description='Apple iPhone 15 Pro - 256GB'),

Product(name='iPhone 17', price=159999, compare_price=169999, discount=6,
       category='Mobiles', brand='Apple', rating=4.9, reviews_count=1234,
       image='images/mobile_iphone17.png',
       description='6.3-inch Super Retina XDR display with ProMotion, A19 Pro chip, Titanium design, 48MP main + 12MP telephoto, USB-C 3.0, Action button.',
       short_description='Apple iPhone 17 - 256GB'),

# ========== MOBILES - Samsung Premium ==========
Product(name='Samsung Galaxy S24 Ultra', price=134999, compare_price=149999, discount=10,
       category='Mobiles', brand='Samsung', rating=4.8, reviews_count=5678,
       image='images/mobile_s24ultra.png',
       description='6.8-inch Dynamic AMOLED 2X, 200MP camera with 100x Space Zoom, Snapdragon 8 Gen 3, 12GB RAM, 512GB storage, S-Pen included, 5000mAh battery.',
       short_description='Samsung Galaxy S24 Ultra - 512GB'),

# ========== MOBILES - Samsung Under 45K (Top 3) ==========
Product(name='Samsung Galaxy S23 FE', price=39999, compare_price=49999, discount=20,
       category='Mobiles', brand='Samsung', rating=4.5, reviews_count=3456,
       image='images/mobile_s23fe.png',
       description='6.4-inch Dynamic AMOLED 2X, 50MP triple camera, Snapdragon 8 Gen 1, 8GB RAM, 128GB storage, 4500mAh battery, IP68 water resistant.',
       short_description='Samsung Galaxy S23 FE - 128GB'),

Product(name='Samsung Galaxy A55 5G', price=35999, compare_price=39999, discount=10,
       category='Mobiles', brand='Samsung', rating=4.5, reviews_count=2345,
       image='images/mobile_a55.png',
       description='6.6-inch Super AMOLED, 50MP quad camera, Exynos 1480, 8GB RAM, 256GB storage, 5000mAh battery, 25W fast charging.',
       short_description='Samsung Galaxy A55 5G - 256GB'),

Product(name='Samsung Galaxy M55 5G', price=24999, compare_price=29999, discount=17,
       category='Mobiles', brand='Samsung', rating=4.4, reviews_count=1876,
       image='images/mobile_m55.png',
       description='6.7-inch Super AMOLED Plus, 108MP camera, Snapdragon 7 Gen 1, 8GB RAM, 128GB storage, 6000mAh battery, 45W fast charging.',
       short_description='Samsung Galaxy M55 5G - 128GB'),

# ========== MOBILES - Vivo Top 5 ==========
Product(name='Vivo X100 Pro', price=89999, compare_price=99999, discount=10,
       category='Mobiles', brand='Vivo', rating=4.7, reviews_count=2341,
       image='images/mobile_vivox100pro.png',
       description='6.78-inch AMOLED, 50MP ZEISS triple camera, MediaTek Dimensity 9300, 16GB RAM, 512GB storage, 5400mAh battery, 100W fast charging.',
       short_description='Vivo X100 Pro - 512GB'),

Product(name='Vivo V30 Pro', price=42999, compare_price=47999, discount=10,
       category='Mobiles', brand='Vivo', rating=4.6, reviews_count=1876,
       image='images/mobile_vivov30pro.png',
       description='6.78-inch AMOLED, 50MP ZEISS triple camera, MediaTek Dimensity 8200, 12GB RAM, 256GB storage, 5000mAh battery, 80W fast charging.',
       short_description='Vivo V30 Pro - 256GB'),

Product(name='Vivo T3 Ultra', price=31999, compare_price=35999, discount=11,
       category='Mobiles', brand='Vivo', rating=4.5, reviews_count=1543,
       image='images/mobile_vivot3ultra.png',
       description='6.78-inch AMOLED, 50MP Sony camera, MediaTek Dimensity 7200, 8GB RAM, 256GB storage, 5000mAh battery, 80W fast charging.',
       short_description='Vivo T3 Ultra - 256GB'),

Product(name='Vivo V30e', price=27999, compare_price=30999, discount=10,
       category='Mobiles', brand='Vivo', rating=4.4, reviews_count=2109,
       image='images/mobile_vivov30e.png',
       description='6.67-inch AMOLED, 64MP OIS camera, Snapdragon 695, 8GB RAM, 128GB storage, 5000mAh battery, 44W fast charging.',
       short_description='Vivo V30e - 128GB'),

Product(name='Vivo Y100 5G', price=19999, compare_price=22999, discount=13,
       category='Mobiles', brand='Vivo', rating=4.3, reviews_count=3456,
       image='images/mobile_vivoy100.png',
       description='6.38-inch AMOLED, 64MP OIS camera, Snapdragon 695, 8GB RAM, 128GB storage, 4500mAh battery, 44W fast charging.',
       short_description='Vivo Y100 5G - 128GB'),

# ========== MOBILES - Realme ==========
Product(name='Realme GT 6', price=38999, compare_price=42999, discount=9,
       category='Mobiles', brand='Realme', rating=4.6, reviews_count=2345,
       image='images/mobile_realme_gt6.png',
       description='6.78-inch LTPO AMOLED, 50MP Sony LYTIA camera, Snapdragon 8s Gen 3, 12GB RAM, 256GB storage, 5500mAh battery, 120W fast charging.',
       short_description='Realme GT 6 - 256GB'),

Product(name='Realme 14 Pro+', price=32999, compare_price=36999, discount=11,
       category='Mobiles', brand='Realme', rating=4.5, reviews_count=1876,
       image='images/mobile_realme14proplus.png',
       description='6.7-inch curved AMOLED, 64MP periscope camera, Snapdragon 7s Gen 2, 8GB RAM, 256GB storage, 5000mAh battery, 67W fast charging.',
       short_description='Realme 14 Pro+ - 256GB'),

Product(name='Realme Narzo 80 Pro', price=19999, compare_price=22999, discount=13,
       category='Mobiles', brand='Realme', rating=4.4, reviews_count=2987,
       image='images/mobile_realme_narzo80pro.png',
       description='6.67-inch Super AMOLED, 50MP OIS camera, MediaTek Dimensity 7050, 8GB RAM, 128GB storage, 5000mAh battery, 67W fast charging.',
       short_description='Realme Narzo 80 Pro - 128GB'),

Product(name='Realme 14x 5G', price=16999, compare_price=19999, discount=15,
       category='Mobiles', brand='Realme', rating=4.3, reviews_count=3456,
       image='images/mobile_realme14x.png',
       description='6.72-inch IPS LCD, 64MP AI camera, MediaTek Dimensity 6100+, 6GB RAM, 128GB storage, 5000mAh battery, 33W fast charging.',
       short_description='Realme 14x 5G - 128GB'),

# ========== MOBILES - Redmi ==========
Product(name='Redmi Note 13 Pro+', price=29999, compare_price=33999, discount=12,
       category='Mobiles', brand='Redmi', rating=4.6, reviews_count=5678,
       image='images/mobile_redmi_note13proplus.png',
       description='6.67-inch curved AMOLED, 200MP OIS camera, MediaTek Dimensity 7200 Ultra, 12GB RAM, 256GB storage, 5000mAh battery, 120W fast charging, IP68.',
       short_description='Redmi Note 13 Pro+ - 256GB'),

Product(name='Redmi Note 13 Pro', price=25999, compare_price=28999, discount=10,
       category='Mobiles', brand='Redmi', rating=4.5, reviews_count=4321,
       image='images/mobile_redmi_note13pro.png',
       description='6.67-inch AMOLED, 200MP OIS camera, Snapdragon 7s Gen 2, 8GB RAM, 256GB storage, 5100mAh battery, 67W fast charging.',
       short_description='Redmi Note 13 Pro - 256GB'),

Product(name='Redmi 13 5G', price=14999, compare_price=17999, discount=17,
       category='Mobiles', brand='Redmi', rating=4.3, reviews_count=2987,
       image='images/mobile_redmi13.png',
       description='6.79-inch IPS LCD, 108MP camera, MediaTek Dimensity 6100+, 6GB RAM, 128GB storage, 5030mAh battery, 33W fast charging.',
       short_description='Redmi 13 5G - 128GB'),

Product(name='Redmi 12 5G', price=12499, compare_price=14999, discount=17,
       category='Mobiles', brand='Redmi', rating=4.2, reviews_count=4567,
       image='images/mobile_redmi12.png',
       description='6.79-inch IPS LCD, 50MP dual camera, Snapdragon 4 Gen 2, 4GB RAM, 128GB storage, 5000mAh battery, 18W fast charging.',
       short_description='Redmi 12 5G - 128GB'),     


        # ========== MOBILES (5 products) ==========
            Product(name='Samsung Galaxy S25 Ultra', price=134999, compare_price=149999, discount=10,
                   category='Mobiles', brand='Samsung', rating=4.8, reviews_count=3456,
                   image='images/samsung25.png',
                   description='6.8-inch Dynamic AMOLED, 200MP camera, 12GB RAM, 512GB storage, S-Pen included.',
                   short_description='Ultimate Android flagship with AI features'),
            
            Product(name='iPhone 17', price=159999, compare_price=169999, discount=6,
                   category='Mobiles', brand='Apple', rating=4.9, reviews_count=5678,
                   image='images/iphone 17.png',
                   description='6.7-inch Super Retina XDR, A17 Pro chip, 48MP camera, Titanium body.',
                   short_description='Apple\'s most advanced iPhone'),
            
            Product(name='OnePlus 12', price=64999, compare_price=69999, discount=7,
                   category='Mobiles', brand='OnePlus', rating=4.6, reviews_count=2341,
                   image='images/1+.png',
                   description='6.7-inch ProXDR display, Snapdragon 8 Gen 3, 50MP Sony camera, 100W charging.',
                   short_description='Flagship killer with amazing performance'),
            
            Product(name='Motorola G57 Power 5G', price=19999, compare_price=20999, discount=10,
                   category='Mobiles', brand='Google', rating=4.7, reviews_count=1876,
                   image='images/moto.png',
                   description='Features a 6.72-inch FHD+ display with a 120 Hz refresh rate and up to 1050 nits brightness for smooth and clear viewing',
                   short_description='Pure Android with best camera'),
            
            Product(name='Redmi A4 5G', price=44999, compare_price=49999, discount=10,
                   category='Mobiles', brand='Redmi', rating=4.4, reviews_count=1567,
                   image='images/redmi.png',
                   description='Glyph interface, Snapdragon 8+ Gen 1, 50MP dual camera, transparent design.',
                   short_description='Unique transparent phone'),


 Product(
    name='Wipro Vesta GD203 1000-Watt Dry Iron',
    price=1099, # Price from the checkout box
    compare_price=9995,
    discount=10,
    category='Home & Kitchen > Kitchen & Home Appliances > Vacuum, Cleaning & Ironing > Irons > Dry Irons',
    brand='Wipro',
    rating=4.7,
    reviews_count=890,
    image='images/ironbox.png',
    description="Wipro heavy weight dry iron with eatble mesh upper , breathable shoes. Comfortable",
    short_description='1000-Watt Dry Iron'
)     
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        print(f"✅ {len(products)} non-food products created successfully!")
    else:
        print(f"📊 Database already has {Product.query.count()} products")

# With this:
with app.app_context():
    db.create_all()
    # Only create sample products if the table is empty
    if Product.query.count() == 0:
        create_sample_products()
        print("✅ Sample products created!")
    else:
        print(f"📊 Database already has {Product.query.count()} products")


    
from textblob import TextBlob

import os
from werkzeug.utils import secure_filename
from utils.upload import save_review_images

@app.route('/product/<int:product_id>/review', methods=['GET', 'POST'])
@login_required
def product_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    
    # Check if user already reviewed this product
    existing_review = Review.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this product!', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    if form.validate_on_submit():
        # Analyze sentiment using TextBlob
        blob = TextBlob(form.comment.data)
        sentiment_score = blob.sentiment.polarity
        
        # Categorize sentiment
        if sentiment_score > 0.3:
            sentiment = "Very Positive"
        elif sentiment_score > 0:
            sentiment = "Positive"
        elif sentiment_score > -0.3:
            sentiment = "Neutral"
        elif sentiment_score > -0.7:
            sentiment = "Negative"
        else:
            sentiment = "Very Negative"
        
        # Create review
        review = Review(
            user_id=current_user.id,
            product_id=product_id,
            rating=form.rating.data,
            comment=form.comment.data,
            sentiment=sentiment,
            sentiment_score=sentiment_score
        )
        
        db.session.add(review)
        db.session.flush()  # Get review ID for images
        
        # Handle image uploads
        if form.images.data:
            # Filter out empty file inputs
            files = [f for f in form.images.data if f and f.filename]
            if files:
                image_paths = save_review_images(files, review.id)
                for path in image_paths:
                    review_image = ReviewImage(
                        review_id=review.id,
                        image_url=path
                    )
                    db.session.add(review_image)
        
        # Update product's average rating
        all_reviews = Review.query.filter_by(product_id=product_id).all()
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        product.rating = round(avg_rating, 1)
        product.reviews_count = len(all_reviews)
        
        db.session.commit()
        
        flash(f'Thank you for your review! Sentiment detected: {sentiment}', 'success')
        return redirect(url_for('product_detail', product_id=product_id))
    
    return render_template('add_review.html', form=form, product=product)
if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist (doesn't delete existing data)
        db.create_all()
        
        # Only add sample products if NO products exist
        if Product.query.count() == 0:
            create_sample_products()
            print("✅ Sample products created!")
        else:
            print(f"📊 Database already has {Product.query.count()} products")
        
        # Debug stats - shows your actual data
        print(f"👥 Users in database: {User.query.count()}")
        print(f"📦 Orders in database: {Order.query.count()}")
    
    # Start the app
    app.run(debug=True, port=3000)