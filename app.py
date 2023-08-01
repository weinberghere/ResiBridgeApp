from flask import Flask, render_template, request, redirect, url_for
import requests
from time import time

app = Flask(__name__)

# API URLs
base_url = "https://resibridge.splynx.app/api/2.0"
customer_url = f"{base_url}/admin/customers/customer"
token_url = f"{base_url}/admin/auth/tokens"
refresh_url = f"{base_url}/admin/auth/tokens/refresh"

# Tokens
access_token = None
access_token_expiration = None
refresh_token = None
refresh_token_expiration = None

# Build headers with access token
def build_headers():
    global access_token
    print("Access Token:", access_token)
    print("Resfresh Token:", refresh_token)
    return {'Authorization': f'(access_token={access_token})'}

# Get a new access token and refresh token
def get_tokens():
    global access_token
    global access_token_expiration
    global refresh_token
    global refresh_token_expiration

# Make request to get new tokens
response = requests.post(token_url, json={
    "auth_type": "admin",
    "login": "Jonathan",
    "password": "2mint503!"
})

# Parse response for tokens
tokens = response.json()
access_token = tokens['access_token']
access_token_expiration = tokens['access_token_expiration']
refresh_token = tokens['refresh_token']
refresh_token_expiration = tokens['refresh_token_expiration']

# Refresh the access token using the refresh token
def refresh_access_token():
    global access_token
    global access_token_expiration
    global refresh_token

# Make request to refresh access token
response = requests.post(refresh_url, json={
    "refresh_token": refresh_token
})

# Parse response for new access token
tokens = response.json()
if 'access_token' in tokens:
    access_token = tokens['access_token']
    access_token_expiration = tokens['access_token_expiration']
    refresh_token = tokens['refresh_token']
else:
    # Handle cases where the access token is not found in the response
    print("Error: Access token not found in the response.")
    get_tokens()

# Check if access token is expired and refresh if necessary
def check_token_status():
    global access_token_expiration
    global refresh_token_expiration

# If access token is expired, refresh it
if access_token_expiration is None or access_token_expiration < time():
    if refresh_token_expiration is None or refresh_token_expiration < time():
        # Both tokens are expired, get new tokens
        get_tokens()
    else:
        # Access token is expired, refresh it
        refresh_access_token()

### Start ###

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Customers page
@app.route('/customers')
def customers():
    check_token_status()
    response = requests.get(customer_url, headers=build_headers())
    customers = response.json()
    return render_template('customers.html', customers=customers, token_status='active')

# Customers Active page
@app.route('/customers_active')
def customers_active():
    check_token_status()
    response = requests.get(customer_url, headers=build_headers())
    customers = response.json()
    active_customers = [customer for customer in customers if customer['status'] == 'active']
    return render_template('customers_active.html', customers=active_customers, token_status='active')

# Add customer
@app.route('/add_customer', methods=['POST'])
def add_customer():
    check_token_status()
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    status = request.form['status']
    login = request.form['login']
    location = request.form['location']
    street = request.form['street']
    zip = request.form['zip']
    city = request.form['city']
    new_customer = {
        'name': name,
        'email': email,
        'phone': phone,
        'status': status,
        'login': login,
        'location_id': location,
        'street_1': street,
        'zip_code': zip,
        'city': city
    }
    response = requests.post(customer_url, json=new_customer, headers=build_headers())
    print(response.status_code)
    if response.status_code == 201:
        return redirect(url_for('customers'))
    else:
        return "Error: Failed to add customer"

# Edit customer
@app.route('/edit_customer', methods=['POST'])
def edit_customer():
    customer_id = request.form['customer_id']
    updated_customer = {'customer_id': customer_id}

    if request.form.get('editName'):
        updated_customer['name'] = request.form['editName']
    if request.form.get('editLogin'):
        updated_customer['login'] = request.form['editLogin']
    if request.form.get('editEmail'):
        updated_customer['email'] = request.form['editEmail']
    if request.form.get('editPhone'):
        updated_customer['phone'] = request.form['editPhone']
    if request.form.get('editStatus'):
        updated_customer['status'] = request.form['editStatus']
    
    update_url = f"{customer_url}/{customer_id}"
    response = requests.put(update_url, json=updated_customer, headers=build_headers())
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
    check_token_status()
    delete_url = f"{customer_url}/{customer_id}"
    response = requests.delete(delete_url, headers=build_headers())
    if response.status_code == 204:
        return redirect(url_for('customers'))
    else:
        return "Error: Failed to delete customer"
    
# Refresh token
@app.route('/refresh', methods=['POST'])
def refresh():
    get_tokens()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='192.168.111.147', port=80) ##debug=True)