from flask import Flask, render_template, request, redirect, url_for
import hashlib
import hmac
import requests
from flask import session
from dotenv import load_dotenv
import secrets

load_dotenv()
app = Flask(__name__)

# Secret Key
app.secret_key = secrets.token_hex(16)

# API URLs
base_url = "https://crm.resibridge.com/api/2.0"
customer_url = f"{base_url}/admin/customers/customer"
payment_url = f"{base_url}/admin/customers/customer-payment-accounts"

# Defining Header
def generate_auth_header():
    KEY = 'bd793c726617bee375996ccbb1c8d092'
    SECRET = '9d4124dedfd3cb7ce75aecc70f432d7e'
    nonce = request.cookies.get('nonce')
    if not nonce:
        nonce = '0'
    else:
        nonce = str(int(nonce) + 1)
    str_to_hash = nonce + KEY
    hash_signature = hmac.new(SECRET.encode(), str_to_hash.encode(), hashlib.sha256).hexdigest().upper()
    auth_header = f'Splynx-EA (key={KEY}&nonce={nonce}&signature={hash_signature})'
    return auth_header

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Customers page
@app.route('/customers')
def customers():
    auth_header = generate_auth_header()
    response = requests.get(customer_url, headers={'Authorization':auth_header})
    customers = response.json()
    return render_template('customers.html', customers=customers, token_status='active')

# Customers Active page
@app.route('/customers_active')
def customers_active():
    auth_header = generate_auth_header()

    # Call the check_token_status() function before making the API request
    response = requests.get(customer_url, headers={'Authorization':auth_header})
    customers = response.json()
    active_customers = [customer for customer in customers if customer['status'] == 'active']
    return render_template('customers_active.html', customers=active_customers, token_status='active')

# Add customer
@app.route('/add_customer', methods=['GET', 'POST'])
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
            'city': city
        }

        response = requests.post(customer_url, json=new_customer, headers={'Authorization':auth_header})

        # Print the response status code and full response content
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")

        if response.status_code == 201:
            customer_id = response.json().get('id')
            if customer_id is not None:
                print(f"Customer ID after creation: {customer_id}")
                session['customer_id'] = customer_id
                return redirect(url_for('banking', customer_id=customer_id))
            else:
                print("Error: Customer ID is None")
                return "Error: Failed to add customer, customer ID is None"
        else:
            print("Response Content:", response.content)
            return "Error: Failed to add customer, status code " + str(response.status_code)
    else:
        return render_template('home.html')

# Edit customer
@app.route('/edit_customer', methods=['POST'])
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
    update_url = f"{customer_url}/{customer_id}"
    response = requests.put(update_url, json=updated_customer, headers={'Authorization': auth_header})
    print(response.status_code)
    print(response.headers)
    print(response.content)
    if response.status_code == 202:
        return redirect(url_for('customers'))
    else:
        return "Error: Failed to edit customer"

# Delete customer
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    auth_header = generate_auth_header()
    delete_url = f"{customer_url}/{customer_id}"
    response = requests.delete(delete_url, headers={'Authorization': auth_header})
    if response.status_code == 204:
        return redirect(url_for('customers'))
    else:
        return "Error: Failed to delete customer"

# Customer banking information
@app.route('/banking', methods=['POST', 'GET'])
def banking():
    auth_header = generate_auth_header()
    print("Inside banking route")  # Testing
    customer_id = session.get('customer_id')
    # Print the customer_id to debug
    print(f"Customer ID in banking route: {customer_id}")
    
    if request.method == 'POST':
        cardNumber = request.form['field_1']
        cardholderName = request.form['field_2']
        cardLast4 = request.form['field_3']
        cardexpirationDate = request.form['field_4']
        accountNumber = request.form['field_6']
        routingNumber = request.form['field_7']
        accountName = request.form['field_8']
        accountType = request.form['field_9']

        # Make API call to add credit card information
        response = requests.put(payment_url + f"?id={customer_id}--1", json={
            'field_1': cardNumber,
            'field_2': cardholderName,
            'field_3': cardLast4,
            'field_4': cardexpirationDate,
            'field_6': accountNumber,
            'field_7': routingNumber,
            'field_8': accountName,
            'field_9': accountType,
        }, headers={'Authorization': auth_header})

        print("----API Response:----")
        print("Status Code:", response.status_code)
        print("Response Content:", response.content)

        if response.status_code == 202:
            return redirect(url_for('customers'))
        else:
            return "Error: Failed to add banking information"
    else:
        return render_template('banking.html')

if __name__ == '__main__':
    app.run(host='192.168.111.147', port=80, debug=True)