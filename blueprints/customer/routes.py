from flask import Blueprint, render_template, request, redirect, url_for, session
from utilities.auth_utils import generate_auth_header
from configurations.splynx_config import SPLYNX_CUSTOMER_URL
import requests
import public_ip as ip
from datetime import datetime
from config import date_format

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/customers')
def customers():
    auth_header = generate_auth_header()
    response = requests.get(SPLYNX_CUSTOMER_URL, headers={'Authorization': auth_header})
    all_customers = response.json()
    return render_template('customers.html', customers=all_customers, token_status='active',
                           year=datetime.now().strftime('%Y'), date=date_format, public=f"Public IP: {ip.get()}")


@customer_bp.route('/customers_active')
def customers_active():
    auth_header = generate_auth_header()

    # Call the check_token_status() function before making the API request
    response = requests.get(SPLYNX_CUSTOMER_URL, headers={'Authorization': auth_header})
    online_customers = response.json()
    active_customers = [customer for customer in online_customers if customer['status'] == 'active']
    return render_template('customers_active.html', customers=active_customers, token_status='active',
                           year=datetime.now().strftime('%Y'), date=date_format, public=f"Public IP: {ip.get()}")


@customer_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    auth_header = generate_auth_header()
    print("Inside add_customer route")  # New Debug Statement
    if request.method == 'POST':
        print("Received POST request to add customer")  # New Debug Statement

        # Location mapping
        location_mapping = {
            '1': 'Park79',
            '2': 'Cambridge',
            # Add more mappings here if needed
        }

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        status = request.form['status']
        location_id = request.form['location']
        location_name = location_mapping.get(location_id, 'Unknown')  # Look up the location name
        unit_number = request.form['unit_number']
        street = request.form['street']
        zip = request.form['zip']
        city = request.form['city']
        ssn_last4 = request.form['ssn_last4']
        dob = request.form['dob']
        login = f"{location_name}unit{unit_number}"  # Use the location name

        new_customer = {
            'name': name,
            'email': email,
            'phone': phone,
            'status': status,
            'login': login,
            'location_id': location_id,  # Still using the numeric location ID here
            'street_1': street,
            'zip_code': zip,
            'city': city,
            'ssn_last4': ssn_last4,
            'dob': dob
        }

        response = requests.post(SPLYNX_CUSTOMER_URL, json=new_customer, headers={'Authorization': auth_header})

        # Print the response status code and full response content
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")

        if response.status_code == 201:
            session['customer_id'] = response.json().get('id')
            customer_id = session.get('customer_id')
            if customer_id is not None:
                print(f"Customer ID after creation: {customer_id}")
                return redirect(url_for('banking', customer_id=customer_id))
            else:
                print("Error: Customer ID is None")
                return "Error: Failed to add customer, customer ID is None"
        else:
            print("Response Content:", response.content)
            return "Error: Failed to add customer, status code " + str(response.status_code)
    else:
        return render_template('home.html', year=datetime.now().strftime('%Y'), date=date_format,
                               public=f"Public IP: {ip.get()}")


@customer_bp.route('/edit_customer', methods=['POST'])
def edit_customer():
    auth_header = generate_auth_header()
    customer_id = request.form['customer_id']
    updated_customer = {'customer_id': customer_id}
    if request.form.get('editName'):
        updated_customer['name'] = request.form['editName']
    if request.form.get('editStreet'):
        updated_customer['street'] = request.form['editStreet']
    if request.form.get('editEmail'):
        updated_customer['email'] = request.form['editEmail']
    if request.form.get('editPhone'):
        updated_customer['phone'] = request.form['editPhone']
    if request.form.get('editZip'):
        updated_customer['zip'] = request.form['editZip']
    if request.form.get('editLocation'):
        updated_customer['location'] = request.form['editLocation']
    if request.form.get('editCity'):
        updated_customer['city'] = request.form['editCity']
    if request.form.get('editStatus'):
        updated_customer['status'] = request.form['editStatus']
    update_url = f"{SPLYNX_CUSTOMER_URL}/{customer_id}"
    response = requests.put(update_url, json=updated_customer, headers={'Authorization': auth_header})
    print(response.status_code)
    print(response.headers)
    print(response.content)
    if response.status_code == 202:
        return redirect(url_for('customer.customers'))
    else:
        return "Error: Failed to edit customer"


@customer_bp.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    auth_header = generate_auth_header()
    delete_url = f"{SPLYNX_CUSTOMER_URL}/{customer_id}"
    response = requests.delete(delete_url, headers={'Authorization': auth_header})
    if response.status_code == 204:
        return redirect(url_for('customer.customers'))
    else:
        return "Error: Failed to delete customer"
