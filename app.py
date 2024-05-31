from flask import Flask, request, redirect, render_template, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "039u230i0323oknecw"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

customers = {
    1: {
        'id': 1,
        'name': 'John Doe',
        'notes': [
            {'id': 101, 'content': 'First note'},
            {'id': 102, 'content': 'Second note'}
        ]
    }
}


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(500), nullable=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("customers"))
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
        return redirect(url_for("login"))
    return render_template("sign_up.html")

@app.route('/customers/')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('show_customers.html', customers=customers)

@app.route('/add_customer/', methods=["GET", "POST"])
@login_required
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

@app.route('/delete_customer/<int:customer_id>', methods=["POST"])
@login_required
def delete_customer(customer_id):
    method = request.form.get("_method")
    if method == "DELETE":
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully.', 'success')
    return redirect(url_for("customers"))

""""
@app.route('/delete_note/<int:customer_id>', methods=["POST"])
@login_required
def delete_note_page(customer_id):
    method = request.form.get("_method")
    if method == "DELETE":
        customer = Customer.query.get_or_404(customer_id)
        note = request.form.get('note')
        if customer.notes:
            try:
                notes = json.loads(customer.notes)
            except json.JSONDecodeError:
                notes = []
            if note in notes:
                notes.remove(note)
                customer.notes = json.dumps(notes)
                db.session.commit()
                flash('Note removed successfully.', 'success')
            else:
                flash('Note not found.', 'danger')
        else:
            flash('No notes to delete.', 'danger')
    return redirect(url_for('customers'))"""

@app.route('/customer/<int:customer_id>')
@login_required
def customer_page(customer_id):
    customer = customers.get(customer_id)
    if customer:
        return render_template('customer.html', customer=customer)
    return 'Customer not found', 404

@app.route('/delete_note/<int:customer_id>', methods=['POST'])
@login_required
def delete_note_page(customer_id):
    if request.method == 'POST':
        note_id = int(request.form['note_id'])
        customer = customers.get(customer_id)
        if customer:
            customer['notes'] = [note for note in customer['notes'] if note['id'] != note_id]
            # Redirect after deletion
            return redirect(url_for('customer_page', customer_id=customer_id))
    return 'Note deletion failed', 400

@app.route('/manage_customer/<int:customer_id>', methods=["GET","POST", "PUT"])
@login_required
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
    return render_template('manage_customer.html', customer=customer, note=customer.notes)

if __name__ == '__main__':
    app.run(debug=True)
