from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests
from time import time

app = Flask(__name__)

# API URLs
base_url = "https://resibridge.splynx.app/api/2.0"
customer_url = f"{base_url}/admin/customers/customer"
blank_id_url = f"{base_url}/your_api_endpoint"
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

# Function to fetch the blank IDs from the API
def get_blank_ids():
    check_token_status()
    response = requests.get(blank_id_url, headers=build_headers())
    if response.status_code == 200:
        data = response.json()
        blank_ids = [id for id in data if not data[id]]
        return blank_ids
    else:
        # Handle error cases
        print("Error: Failed to fetch blank IDs")
        return []

# Update the blank_id route
@app.route('/blank_id')
def blank_id():
    # Call the get_blank_ids function to fetch the blank IDs
    blank_ids = get_blank_ids()

    # Print the retrieved blank IDs
    print("Retrieved Blank IDs:", blank_ids)

    # Pass the blank IDs to the template for rendering
    return render_template('blank_id.html', blank_ids=blank_ids)

# Add customer
@app.route('/add_customer', methods=['POST'])
def add_customer():
    check_token_status()
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    status = request.form['status']
    login = request.form['login']
    new_customer = {
        'name': name,
        'email': email,
        'phone': phone,
        'status': status,
        'login': login
    }
    response = requests.post(customer_url, json=new_customer, headers=build_headers())
    if response.status_code == 201:
        return redirect(url_for('customers'))
    else:
        return "Error: Failed to add customer"

@app.route('/edit_customer', methods=['PUT'])
def edit_customer():
    # Get the customer ID and updated fields from the request body
    customer_id = request.json['customer_id']
    name = request.json['name']
    login = request.json['login']
    email = request.json['email']
    phone = request.json['phone']
    status = request.json['status']

    # Print the received values
    print("Received PUT request to edit_customer.")
    print("Customer ID:", customer_id)
    print("Name:", name)
    print("Login:", login)
    print("Email:", email)
    print("Phone:", phone)
    print("Status:", status)

    # Build the request URL and headers
    url = f"{customer_url}/{customer_id}"

    # Build the request body
    data = {
        "name": name,
        "login": login,
        "email": email,
        "phone": phone,
        "status": status
    }

    print("Data:", data)

    # Send the PUT request to the Splynx API
    response = requests.put(url, headers = build_headers(), json=data)
    print("Status:", response)

    # Check the response status code and return a response
    if response.status_code == 200:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False}), 500

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
    app.run(host='192.168.111.147', port=80, debug=True)