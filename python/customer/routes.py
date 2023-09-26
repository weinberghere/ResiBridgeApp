from flask import Blueprint, render_template

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers')
def customers():
    return render_template('customers.html')

@customer_bp.route('/customers_active')
def customers_active():
    return render_template('customers_active.html')

@customer_bp.route('/add_customer')
def add_customer():
    return render_template('add_customer.html')
