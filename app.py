from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
DB = 'foodiehub.db'


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer'
    );
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        rating REAL DEFAULT 4.5,
        reviews INTEGER DEFAULT 0,
        image TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total REAL NOT NULL,
        address TEXT NOT NULL,
        payment TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        food_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(food_id) REFERENCES foods(id)
    );
    ''')

    admin = conn.execute('SELECT id FROM users WHERE email=?', ('admin@foodiehub.com',)).fetchone()
    if not admin:
        conn.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',
                     ('FoodieHub Admin', 'admin@foodiehub.com', generate_password_hash('admin123'), 'admin'))

    if conn.execute('SELECT COUNT(*) AS c FROM foods').fetchone()['c'] == 0:
        foods = [
            ('Chicken Pizza','Pizza','Stone-baked pizza with chicken, mozzarella, olives and herbs',299,4.5,120,'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=900&q=85'),
            ('Cheese Burger','Burger','Juicy grilled patty with cheddar, lettuce, tomato and house sauce',149,4.2,98,'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85'),
            ('Chicken Biriyani','Biriyani','Aromatic basmati rice, tender chicken and traditional spices',220,4.6,150,'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=900&q=85'),
            ('Veg Hakka Noodles','Chinese','Wok-tossed noodles with crisp vegetables and oriental sauces',160,4.1,75,'https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85'),
            ('French Fries','Snacks','Crispy golden fries seasoned with our signature spice blend',99,4.4,84,'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=85'),
            ('Chocolate Brownie','Desserts','Warm fudgy chocolate brownie with a rich cocoa finish',120,4.7,64,'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85'),
            ('Fresh Lime Soda','Beverages','Refreshing lime, mint and sparkling soda served chilled',70,4.3,51,'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=900&q=85'),
            ('Paneer Tikka','Indian','Smoky grilled paneer with peppers, onion and mint chutney',190,4.5,88,'https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=900&q=85'),
        ]
        conn.executemany('INSERT INTO foods(name,category,description,price,rating,reviews,image) VALUES(?,?,?,?,?,?,?)', foods)
    conn.commit()
    conn.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'warning')
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Administrator access required.', 'danger')
            return redirect(url_for('home'))
        return fn(*args, **kwargs)
    return wrapper


def cart_items():
    cart = session.get('cart', {})
    if not cart:
        return [], 0
    conn = db()
    ids = [int(x) for x in cart.keys()]
    placeholders = ','.join('?' for _ in ids)
    foods = conn.execute(f'SELECT * FROM foods WHERE id IN ({placeholders})', ids).fetchall()
    conn.close()
    items, total = [], 0
    for food in foods:
        qty = int(cart.get(str(food['id']), 0))
        subtotal = food['price'] * qty
        total += subtotal
        items.append({'food': food, 'quantity': qty, 'subtotal': subtotal})
    return items, total


@app.context_processor
def globals_for_templates():
    count = sum(session.get('cart', {}).values()) if session.get('cart') else 0
    return {'cart_count': count, 'current_user': session.get('user_name'), 'is_admin': session.get('role') == 'admin'}


@app.route('/')
def home():
    conn = db()
    foods = conn.execute('SELECT * FROM foods ORDER BY rating DESC, reviews DESC LIMIT 8').fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM foods ORDER BY category').fetchall()
    conn.close()
    return render_template('index.html', foods=foods, categories=categories)


@app.route('/menu')
def menu():
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    conn = db()
    query = 'SELECT * FROM foods WHERE 1=1'
    params = []
    if category:
        query += ' AND category=?'; params.append(category)
    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'; params += [f'%{search}%', f'%{search}%']
    query += ' ORDER BY rating DESC, name'
    foods = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM foods ORDER BY category').fetchall()
    conn.close()
    return render_template('menu.html', foods=foods, categories=categories, selected=category, search=search)


@app.route('/add-to-cart/<int:food_id>')
def add_to_cart(food_id):
    conn = db(); food = conn.execute('SELECT id FROM foods WHERE id=?', (food_id,)).fetchone(); conn.close()
    if not food:
        flash('Food item not found.', 'danger'); return redirect(url_for('menu'))
    cart = session.setdefault('cart', {})
    key = str(food_id)
    cart[key] = int(cart.get(key, 0)) + 1
    session.modified = True
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('menu'))


@app.post('/update-cart')
def update_cart():
    cart = session.get('cart', {})
    for key, value in request.form.items():
        if key.startswith('qty_'):
            food_id = key[4:]
            try: qty = max(0, int(value))
            except ValueError: qty = 1
            if qty == 0: cart.pop(food_id, None)
            else: cart[food_id] = qty
    session['cart'] = cart
    flash('Cart updated.', 'success')
    return redirect(url_for('cart'))


@app.get('/remove-from-cart/<int:food_id>')
def remove_from_cart(food_id):
    cart = session.get('cart', {})
    cart.pop(str(food_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.get('/cart')
def cart():
    items, total = cart_items()
    delivery = 0 if total >= 499 or total == 0 else 40
    return render_template('cart.html', items=items, total=total, delivery=delivery, grand_total=total+delivery)


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not name or not email or len(password) < 6:
            flash('Enter a name, valid email and password of at least 6 characters.', 'danger')
            return render_template('register.html')
        conn = db()
        try:
            conn.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)', (name,email,generate_password_hash(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close(); flash('An account with that email already exists.', 'danger'); return render_template('register.html')
        conn.close()
        flash('Account created. Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower(); password = request.form.get('password','')
        conn = db(); user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone(); conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']; session['user_name'] = user['name']; session['role'] = user['role']
            return redirect(url_for('admin') if user['role']=='admin' else url_for('home'))
        flash('Incorrect email or password.', 'danger')
    return render_template('login.html')


@app.get('/logout')
def logout():
    session.clear(); flash('You have been signed out.', 'success'); return redirect(url_for('home'))


@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    items, total = cart_items()
    if not items:
        flash('Your cart is empty.', 'warning'); return redirect(url_for('menu'))
    delivery = 0 if total >= 499 else 40
    grand_total = total + delivery
    if request.method == 'POST':
        address = request.form.get('address','').strip(); payment = request.form.get('payment','COD')
        if len(address) < 10:
            flash('Please enter a complete delivery address.', 'danger'); return render_template('checkout.html', items=items,total=total,delivery=delivery,grand_total=grand_total)
        conn = db(); cur = conn.cursor()
        cur.execute('INSERT INTO orders(user_id,total,address,payment) VALUES(?,?,?,?)', (session['user_id'],grand_total,address,payment))
        order_id = cur.lastrowid
        cur.executemany('INSERT INTO order_items(order_id,food_id,quantity,price) VALUES(?,?,?,?)', [(order_id,i['food']['id'],i['quantity'],i['food']['price']) for i in items])
        conn.commit(); conn.close(); session['cart'] = {}
        return redirect(url_for('order_success', order_id=order_id))
    return render_template('checkout.html', items=items,total=total,delivery=delivery,grand_total=grand_total)


@app.get('/order-success/<int:order_id>')
@login_required
def order_success(order_id):
    return render_template('success.html', order_id=order_id)


@app.get('/orders')
@login_required
def orders():
    conn = db(); orders = conn.execute('SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],)).fetchall(); conn.close()
    return render_template('orders.html', orders=orders)


@app.get('/admin')
@admin_required
def admin():
    conn = db()
    foods = conn.execute('SELECT * FROM foods ORDER BY id DESC').fetchall()
    orders = conn.execute('''SELECT o.*, u.name, u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC''').fetchall()
    customers = conn.execute("SELECT COUNT(*) c FROM users WHERE role='customer'").fetchone()['c']
    revenue = conn.execute('SELECT COALESCE(SUM(total),0) total FROM orders').fetchone()['total']
    conn.close()
    return render_template('admin.html', foods=foods, orders=orders, customers=customers, revenue=revenue)


@app.post('/admin/add-food')
@admin_required
def add_food():
    data = request.form
    conn = db(); conn.execute('INSERT INTO foods(name,category,description,price,rating,reviews,image) VALUES(?,?,?,?,?,?,?)',
        (data['name'],data['category'],data['description'],float(data['price']),4.5,0,data['image']))
    conn.commit(); conn.close(); flash('Food item added.', 'success'); return redirect(url_for('admin'))


@app.get('/admin/delete-food/<int:food_id>')
@admin_required
def delete_food(food_id):
    conn = db(); conn.execute('DELETE FROM foods WHERE id=?',(food_id,)); conn.commit(); conn.close(); flash('Food item deleted.','success'); return redirect(url_for('admin'))


@app.post('/admin/update-order/<int:order_id>')
@admin_required
def update_order(order_id):
    status = request.form.get('status','Pending')
    if status not in {'Pending','Preparing','Out for delivery','Delivered','Cancelled'}: status='Pending'
    conn = db(); conn.execute('UPDATE orders SET status=? WHERE id=?',(status,order_id)); conn.commit(); conn.close(); return redirect(url_for('admin'))


@app.errorhandler(404)
def not_found(_):
    return render_template('404.html'), 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
