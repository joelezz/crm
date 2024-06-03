from flask import Flask, request, redirect, render_template, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate
import os, stripe
from dotenv import load_dotenv

from functools import wraps
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import secrets

from flask_wtf.csrf import CSRFProtect

foo = secrets.token_urlsafe(16)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
app.secret_key = foo
csrf = CSRFProtect(app)



bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

stripe_keys = {
    "secret_key": os.environ.get("STRIPE_SECRET_KEY"),
    "publishable_key": os.environ.get("STRIPE_PUBLISHABLE_KEY"),
}
stripe.api_key = stripe_keys["secret_key"]

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    has_paid = db.Column(db.Boolean, default=False)  # Checks if the user has payed

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(500), nullable=True)

class NameForm(FlaskForm):
    update = StringField('Update data', validators=[DataRequired(), Length(10, 40)])
    submit = SubmitField('Submit')

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.route('/')
def home():
    return render_template('index.html')

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_paid:
            return redirect(url_for('payment'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for("customers"))
        else:
            return "Invalid username or password"
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/sign_up/', methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)  # Log the user in
        return redirect(url_for("payment"))  # Redirect to the payment page
    return render_template("sign_up.html")

@app.route('/customers/')
@login_required
@payment_required
def customers():
    customers = Customer.query.all()
    return render_template('show_customers.html', customers=customers)

def product_price_in_cents():
    price = os.environ.get("CRM_SUBSCRIPTION_PRICE")
    return price

@app.route('/payment/')
@login_required
def payment():
    stripe_publishable_key = stripe_keys.get('STRIPE_PUBLISHABLE_KEY') 
    return render_template('payment.html', stripe_publishable_key=stripe_publishable_key)

@app.route("/config")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)

@app.route("/create-checkout-session/", methods=["POST"])
def create_checkout_session():
    domain_url = "http://127.0.0.1:5000/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancelled",
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "CRM-subscription",
                        },
                        "unit_amount": product_price_in_cents(),  # Amount in cents
                    },
                    "quantity": 1,
                }
            ]
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/success")
def success():
    if current_user.is_authenticated:
        user = Users.query.get(current_user.id)
        user.has_paid = True
        db.session.commit()
    return render_template("payment_success.html")


@app.route("/cancelled")
def cancelled():
    return render_template("payment_cancelled.html")

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )
    except ValueError as e:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")

    return "Success", 200

@app.route('/add_customer/', methods=["GET", "POST"])
@login_required
@payment_required
def add_customer():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        notes = request.form.get("notes")
        customer = Customer(name=name, email=email, phone=phone, notes=notes)
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for("customers"))
    return render_template("add_customer.html")

@app.route('/delete_customer/<int:customer_id>', methods=["GET", "POST"])
@login_required
@payment_required
def delete_customer(customer_id):
    method = request.form.get("method")
    customer = Customer.query.get_or_404(customer_id)
    if method == "DELETE":
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully.', 'success')
        return redirect(url_for("customers"))
    return render_template("delete_customer.html", customer=customer)

@app.route('/customer/<int:customer_id>')
@login_required
@payment_required
def customer_page(customer_id):
    customer = customers.get(customer_id)
    if customer:
        return render_template('customer.html', customer=customer)
    return 'Customer not found', 404

@app.route('/add_contact_data/<int:customer_id>' , methods=['POST', 'GET'])
@login_required
@payment_required
def add_contact_data(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == "POST":
        contact_date = request.form.get("contact_date")
        discussion = request.form.get("discussion")
        next_steps = request.form.get("next_steps")
        contact_data = Customer(contact_date=contact_date, discussion=discussion, next_steps=next_steps)
        db.session.add(contact_data)
        db.session.commit()
        return redirect(url_for("customers"))
    return render_template("contact_data.html", customer=customer)

@app.route('/delete_note/<int:customer_id>', methods=['POST'])
@login_required
@payment_required
def delete_note_page(customer_id):
    if request.method == 'POST':
        note_id = int(request.form['note_id'])
        customer = customers.get(customer_id)
        if customer:
            customer['notes'] = [note for note in customer['notes'] if note['id'] != note_id]
            return redirect(url_for('customer_page', customer_id=customer_id))
    return 'Note deletion failed', 400

@app.route('/manage/<int:customer_id>')
@login_required
@payment_required
def manage(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('manage.html', customer=customer)

@app.route('/manage_customer/<int:customer_id>', methods=["GET", "POST", "PUT"])
@login_required
@payment_required
def manage_customer(customer_id):
    method = request.form.get("_method")
    customer = Customer.query.get_or_404(customer_id)

    if method == "PUT":
        customer = Customer.query.get_or_404(customer_id)
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.notes = request.form.get('notes')
        db.session.commit()
        flash('Customer data updated successfully.', 'success')
        return redirect(url_for("customers"))
    return render_template('update_customer.html', customer=customer, note=customer.notes)

if __name__ == '__main__':
    app.run(debug=True)