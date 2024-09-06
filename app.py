# app.py
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import stripe

# Configurations
app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

# Stripe configuration
stripe.api_key = app.config['STRIPE_SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.login_view = 'auth'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Define Product model after initializing db
from models import Product, Category


# <-------------------------------Categories and Price cleaning------------------------------->
def clean_price(price_str):
    try:
        clean_str = price_str.replace('$', '').replace(',', '').replace('\xa0', '').replace('–', '').strip()
        # Remove anything after the actual price
        clean_str = clean_str.split('(')[0].strip()
        return float(clean_str)
    except ValueError as e:
        print(f"Could not convert price: {price_str}. Error: {e}")
        return None


def scrape_category(url, category_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Check if the category already exists in the database
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()

    for item in soup.select('.item-container'):
        name_tag = item.select_one('.item-title')
        price_tag = item.select_one('.price-current')
        image_tag = item.select_one('.item-img img')

        if name_tag and price_tag and image_tag:
            name = name_tag.text.strip()
            price = clean_price(price_tag.text.strip())
            if price is None:
                continue  # Skip products where price could not be determined
            image_url = image_tag['src']
            description = "No description available"

            # Check if the product already exists in the database
            existing_product = Product.query.filter_by(name=name, category_id=category.id).first()
            if not existing_product:
                product = Product(name=name, description=description, price=price, image_url=image_url, category_id=category.id)
                db.session.add(product)

    db.session.commit()


@app.route('/category/<int:category_id>')
def show_category(category_id):
    # Logic to fetch products belonging to the category_id
    products = Product.query.filter_by(category_id=category_id).all()

    # Fetch the category name
    category = Category.query.get_or_404(category_id)
    category_name = category.name

    # Pagination logic
    per_page = 12
    page = request.args.get('page', 1, type=int)
    total = len(products)

    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products[start:end]

    # Calculate total number of pages
    total_pages = (total + per_page - 1) // per_page
    return render_template('category.html',
                           products=paginated_products,
                           page=page,
                           total=total,
                           per_page=per_page,
                           total_pages=total_pages,
                           category_id=category_id,
                           category_name=category_name)


# <-------------------------------Scrape components details------------------------------->
def scrape_hard_drives():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006670&cm_sp=shop-all-products-_-categroy-_-Hard-Drives-top'
        scrape_category(url, 'Hard Drives')


def scrape_headsets():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=101702324&cm_sp=shop-all-products-_-categroy-_-Headsets-Speakers-Soundcards-top'
        scrape_category(url, 'Headsets, Speakers & Soundcards')


def scrape_monitors():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=101702291&cm_sp=shop-all-products-_-categroy-_-Monitors-top'
        scrape_category(url, 'Monitors')


def scrape_mice_and_keyboards():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=101702348&cm_sp=shop-all-products-_-categroy-_-Keyboards-Mice-top'
        scrape_category(url, 'Keyboards and Mice')


def scrape_motherboards():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006654&cm_sp=shop-all-products-_-categroy-_-Motherboards-top'
        scrape_category(url, 'Motherboards')


def scrape_power_supplies():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006656&cm_sp=shop-all-products-_-categroy-_-Power-Supplies-top'
        scrape_category(url, 'Power Supplies')


def scrape_fans_cooling():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006648&cm_sp=shop-all-products-_-categroy-_-Fans-PC-Cooling-top'
        scrape_category(url, 'Fans and Cooling')


def scrape_computer_cases():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006644&cm_sp=shop-all-products-_-categroy-_-Computer-Cases-top'
        scrape_category(url, 'Computer Cases')


def scrape_cpus():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006676&cm_sp=shop-all-products-_-categroy-_-CPUs-Processors-top'
        scrape_category(url, 'CPUs')


def scrape_ssds():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100011692&cm_sp=shop-all-products-_-categroy-_-SSDs-top'
        scrape_category(url, 'SSDs')


def scrape_gpus():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006662&cm_sp=shop-all-products-_-categroy-_-GPUs-Video-Graphics-Devices-top'
        scrape_category(url, 'GPUs')


def scrape_rams():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006650&cm_sp=shop-all-products-_-categroy-_-Memory-top'
        scrape_category(url, 'RAMs')


# <-------------------------------DB Models------------------------------->
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_active(self):
        # For simplicity, always return True
        return True

    def get_id(self):
        return str(self.id)


with app.app_context():
    db.create_all()



class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('name', 'category_id', name='unique_product_category'),)


with app.app_context():
    db.create_all()


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    product = db.relationship('Product', backref='cart_items')
    user = db.relationship('User', backref='cart')

    def __repr__(self):
        return f"Cart('{self.product.name}', '{self.quantity}')"


with app.app_context():
    db.create_all()
    scrape_cpus()
    scrape_gpus()
    scrape_rams()
    scrape_motherboards()
    scrape_computer_cases()
    scrape_power_supplies()
    scrape_fans_cooling()
    scrape_ssds()


# <-------------------------------Login and Register Routes------------------------------->
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'register':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('auth'))

        elif action == 'login':
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    products = Product.query.order_by(func.random()).limit(12).all()
    return render_template('index.html', products=products)


# <-------------------------------Cart Routes------------------------------->
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            flash("Product not found.", 'error')
            return redirect(url_for('cart'))

        # Check if the product is already in the cart
        cart_item = Cart.query.filter_by(product_id=product_id, user_id=current_user.id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = Cart(product_id=product_id, quantity=1, user_id=current_user.id)
            db.session.add(cart_item)

        db.session.commit()
        flash(f'{product.name} added to cart.', 'success')

    except Exception as e:
        flash(f'Error adding to cart: {str(e)}', 'error')

    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    try:
        cart_item = Cart.query.filter_by(product_id=product_id, user_id=current_user.id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart.', 'success')
        else:
            flash('Item not found in cart.', 'error')

    except Exception as e:
        flash(f'Error removing item from cart: {str(e)}', 'error')

    return redirect(url_for('cart'))


@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    formatted_total = f"{total:.2f}"
    return render_template('cart.html', cart_items=cart_items, total=formatted_total)


@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/support')
def customer_support():
    return render_template('support.html')


@app.route('/update-quantity', methods=['POST'])
def update_quantity():
    data = request.get_json()
    cart_item_id = data['cart_item_id']
    action = data['action']

    cart_item = Cart.query.get(cart_item_id)
    if cart_item:
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1

        db.session.commit()

        # Calculate new total price
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        new_total = sum(item.product.price * item.quantity for item in cart_items)

        return jsonify({
            'success': True,
            'new_quantity': cart_item.quantity,
            'new_total': new_total
        })
    return jsonify({'success': False}), 404


# <-------------------------------Payment Routes------------------------------->
# @app.route('/checkout', methods=['POST'])
# def checkout():
#     cart_items = []
#     total = 0
#     if 'cart' in session:
#         cart_items = Product.query.filter(Product.id.in_(session['cart'])).all()
#         total = sum(item.price for item in cart_items)
#
#     session['total'] = total
#     return render_template('checkout.html',
#                            key=app.config['STRIPE_PUBLISHABLE_KEY'],
#                            total=total)
@app.route('/checkout-success')
@login_required
def checkout_success():
    # Handle post-checkout success logic (e.g., clear cart, save order details)
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return render_template('checkout_success.html')


@app.route('/checkout-cancel')
@login_required
def checkout_cancel():
    return redirect(url_for('cart'))


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty. Please add items to your cart before proceeding to checkout.', 'checkout_warning')
        return redirect(url_for('cart'))

    # Create line items for the Stripe checkout session
    line_items = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': int(product.price * 100),  # Stripe expects the amount in cents
            },
            'quantity': item.quantity,
        })

    # Create a Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=url_for('checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('cart', _external=True),
    )

    return redirect(session.url, code=303)


@app.route('/charge', methods=['POST'])
def charge():
    amount = int(session['total'] * 100)  # Stripe uses cents

    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Flask Charge'
    )

    session.pop('cart', None)
    return render_template('charge.html', amount=amount / 100)


@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        search_results = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
        return render_template('search_results.html', query=query, search_results=search_results)
    else:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('index'))


with app.app_context():
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.commit()

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#         scrape_cpus()
#         scrape_gpus()
#         scrape_rams()
#         scrape_motherboards()
#         scrape_computer_cases()
#         scrape_power_supplies()
#         scrape_fans_cooling()
#         scrape_ssds()
#     app.run(debug=True)

if __name__ == '__main__':
    scrape_cpus()
    scrape_gpus()
    scrape_rams()
    scrape_motherboards()
    scrape_computer_cases()
    scrape_power_supplies()
    scrape_fans_cooling()
    scrape_ssds()
    scrape_mice_and_keyboards()
    scrape_monitors()
    scrape_headsets()
    scrape_hard_drives()
    app.run(debug=True)
