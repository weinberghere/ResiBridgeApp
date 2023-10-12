from flask import request, Blueprint, render_template, redirect, session
from utils import generate_auth_header
from config import date_format
from configurations.splynx_config import SPLYNX_TOKEN_URL
import requests
from datetime import datetime
import public_ip as ip
from utilities.auth_utils import generate_auth_header
import logging
logging.basicConfig(level=logging.DEBUG)

auth_bp = Blueprint('auth', __name__)
print("Defining auth routes")


@auth_bp.route('/')
def home():
    logging.debug("Inside the home route")
    client_ip = session.get('client_ip', 'IP not set')
    return render_template('/login.html', year=datetime.now().strftime('%Y'), date=date_format, cx=f"Public IP: {client_ip}")


@auth_bp.route('/login', methods=['POST'])
def login():
    auth_header = generate_auth_header()
    print("Inside login route")
    username = request.form['username']
    password = request.form['password']
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    session['client_ip'] = client_ip

    # Make API call to get the token
    if request.method == 'POST':
        print("Received POST request to login")
        response = requests.post(SPLYNX_TOKEN_URL, headers={'Authorization': auth_header}, json={
            'auth_type': 'admin',
            'login': username,
            'password': password
        })
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        if response.status_code == 201:
            token_data = response.json()
            access_token = token_data['access_token']
            # Store the access_token securely for subsequent API requests
            # Redirect to authenticated pages
            return redirect("/add_customer")
        else:
            return 'Login failed'
    else:
        return render_template('login.html', year=datetime.now().strftime('%Y'), date=date_format,
                               cx=f"Public IP: {client_ip}")
