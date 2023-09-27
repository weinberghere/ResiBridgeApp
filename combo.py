import requests
import os
import json
import hmac
import hashlib
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, send_file
from datetime import datetime, timedelta
import csv
from io import BytesIO, StringIO
import logging
import functools
import public_ip as ip

app = Flask(__name__)
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.logger.setLevel(logging.DEBUG)

# ACP Configuration
api_id = os.getenv("ACP_API_ID")
api_key = os.getenv("ACP_API_KEY")
acp_token_url = "https://api.universalservice.org/auth/token"
acp_base_url = "https://api.universalservice.org/ebbp-svc/1/"

# Footer Fun
days = datetime.now().strftime('%d')
day = int(days)
if 4 <= day <= 20 or 24 <= day <= 30:
    suffix = "th"
else:
    suffix = ["st", "nd", "rd"][day % 10 - 1]
date_format = datetime.now().strftime('%A %B') + " " + days + suffix

#########################################
#########################################
###  ENTER SAC CODES AND STATES HERE: ###
SAC_CODES = {
    "NY": "815160",
    "KY": "826163"
}
#########################################
#########################################

# Splynx Configuration
splynx_base_url = "https://crm.resibridge.com/api/2.0"
splynx_customer_url = f"{splynx_base_url}/admin/customers/customer"
splynx_payment_url = f"{splynx_base_url}/admin/customers/customer-payment-accounts"
splynx_token_url = f"{splynx_base_url}/admin/auth/tokens"


# Defining Splynx Header
def generate_auth_header():
    splynx_api_key = os.getenv("SPLYNX_KEY")
    splynx_api_secret = os.getenv("SPLYNX_SECRET")
    nonce = request.cookies.get('nonce')
    if not nonce:
        nonce = '0'
    else:
        nonce = str(int(nonce) + 1)
    str_to_hash = nonce + splynx_api_key
    hash_signature = hmac.new(splynx_api_secret.encode(), str_to_hash.encode(), hashlib.sha256).hexdigest().upper()
    auth_header = f'Splynx-EA (key={splynx_api_key}&nonce={nonce}&signature={hash_signature})'
    return auth_header


@app.route('/')
def home():
    return render_template('login.html', year=datetime.now().strftime('%Y'), date=date_format,
                           public=f"Public IP: {ip.get()}")


# Login page
@app.route('/login', methods=['POST'])
def login():
    auth_header = generate_auth_header()
    print("Inside login route")
    username = request.form['username']
    password = request.form['password']

    # Make API call to get the token
    if request.method == 'POST':
        print("Received POST request to login")
        response = requests.post(splynx_token_url, headers={'Authorization': auth_header}, json={
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
            return redirect('/add_customer')
        else:
            return 'Login failed'
    else:
        return render_template('login.html', year=datetime.now().strftime('%Y'), date=date_format,
                               public=f"Public IP: {ip.get()}")


# Customers page
@app.route('/customers')
def customers():
    auth_header = generate_auth_header()
    response = requests.get(splynx_customer_url, headers={'Authorization': auth_header})
    customers = response.json()
    return render_template('customers.html', customers=customers, token_status='active',
                           year=datetime.now().strftime('%Y'), date=date_format, public=f"Public IP: {ip.get()}")


# Customers Active page
@app.route('/customers_active')
def customers_active():
    auth_header = generate_auth_header()

    # Call the check_token_status() function before making the API request
    response = requests.get(splynx_customer_url, headers={'Authorization': auth_header})
    customers = response.json()
    active_customers = [customer for customer in customers if customer['status'] == 'active']
    return render_template('customers_active.html', customers=active_customers, token_status='active',
                           year=datetime.now().strftime('%Y'), date=date_format, public=f"Public IP: {ip.get()}")


# Add customer

### TO DO ###
### ADD OPTIONS FOR VERIFYING AND ENROLLING ###
### IF VERIFICATION IS SUCCESSFUL CHANGE BUTTON TO ENROLL ###
### IF VERIFICATION IS REJECTED GIVE ERROR ###
### ADD HANDLING FOR ACPBENEFITS CHECK ###

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    global customer_id
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

        response = requests.post(splynx_customer_url, json=new_customer, headers={'Authorization': auth_header})

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
        return render_template('home.html', year=datetime.now().strftime('%Y'), date=date_format,
                               public=f"Public IP: {ip.get()}")


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
    update_url = f"{splynx_customer_url}/{customer_id}"
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
    delete_url = f"{splynx_customer_url}/{customer_id}"
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
        response = requests.put(splynx_payment_url + f"?id={customer_id}--1", json={
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
            return redirect(url_for('acp_action', action='verify'))
        else:
            return "Error: Failed to add banking information"
    else:
        return render_template('banking.html', year=datetime.now().strftime('%Y'), date=date_format,
                               public=f"Public IP: {ip.get()}")


# ACP related routes

def requires_token(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        # Check if there's an existing token and it's still valid
        token = session.get('acp_access_token')
        token_expiry = session.get('acp_token_expiry', datetime.now() - timedelta(hours=1))

        if not token or datetime.now() >= token_expiry:
            if not fetch_new_token():
                return "Failed to retrieve ACP token", 500

        return func(*args, **kwargs)

    return decorated_function


def fetch_new_token():
    headers = {"Content-Type": "application/json"}
    response = requests.post(acp_token_url, headers=headers, auth=(api_id, api_key))

    if response.status_code == 200:
        response_data = response.json()
        session["access_token"] = response_data["access_token"]
        session["token_expiry"] = (datetime.now() + timedelta(hours=1)).timestamp()


@app.route("/acp/<action>", methods=["GET", "POST"])
def acp_action(action):
    if request.method == "GET":
        customer_data = session.get('new_customer_details', {})
        return render_template(f'acp_{action}.html', data=customer_data, year=datetime.now().strftime('%Y'),
                               date=date_format, public=f"Public IP: {ip.get()}")
    elif request.method == "POST":
        access_token, data = prepare_data(action)
        endpoint_mapping = {
            'verify': 'verify',
            'enroll': 'subscriber',
            'transfer': 'transfer',
            'delete': 'delete',
            'unenroll': 'unenroll',
            # add other actions here
        }

        if action not in endpoint_mapping:
            return "Invalid action", 400

        endpoint = acp_base_url + endpoint_mapping[action]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if isinstance(response_data, list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(endpoint, headers=headers, json=data)

            response_data = response.json()
            if isinstance(response_data, dict):
                failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            else:
                failure_type = "Unknown failure"
                body_messages = str(response_data)

            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400


def prepare_data(action):
    if not session.get("access_token") or datetime.now().timestamp() >= session.get("token_expiry", 0):
        fetch_new_token()

    access_token = session.get("access_token")
    print("Session Data:", session)
    print("Customer Details:", session.get('new_customer_details'))

    # Initialize default values
    first_name = ""
    last_name = ""
    address = ""
    zip_code = ""
    city = ""
    unit_number = ""
    phone_number = ""
    state = ""
    ssn_last4 = ""
    dob = ""
    formatted_dob = ""

    # Location mapping
    location_mapping = {
        '1': 'NY',
        '2': 'KY',
    }

    if action == 'verify':
        if 'new_customer_details' in session:
            customer_details = session.get('new_customer_details')

            # Extract details from session
            first_name = customer_details['name'].split()[0]
            last_name = customer_details['name'].split()[-1]
            address = customer_details['street_1']
            city = customer_details['city']
            zip_code = customer_details['zip_code']
            phone_number = customer_details['phone']
            state = location_mapping.get(customer_details['location_id'], 'Unknown')
            ssn_last4 = customer_details['ssn_last4']
            dob = customer_details['dob']
            dob_obj = datetime.strptime(dob, "%Y-%m-%d")
            formatted_dob = dob_obj.strftime("%m/%d/%Y")

    # Construct the payload
    today_date = datetime.now().strftime("%m/%d/%Y")
    sac = SAC_CODES.get(state, "")

    data = {
        "applicationId": "",
        "transactionType": action,
        "transactionEffectiveDate": "",
        "sac": sac,
        "lastName": last_name,
        "firstName": first_name,
        "middleName": "",
        "phoneNumber": phone_number,
        "last4ssn": ssn_last4,
        "tribalId": "",
        "dob": formatted_dob,
        "primaryAddress1": address,
        "primaryAddress2": unit_number,
        "primaryCity": city,
        "primaryState": state,
        "primaryZipCode": zip_code,
        "serviceType": "Fiber",
        "dupAddressException": "",
        "serviceInitializationDate": today_date,
        "latitude": "",
        "bqpMiddleName": "",
        "bqpTribalId": "",
        "amsFailureException": "",
        "bqpDob": "",
        "mailingAddress2": "",
        "mailingAddress1": "",
        "mailingZipCode": "",
        "avpPgrmException": "",
        "mailingState": "",
        "etcGeneralUse": "",
        "schoolName": "",
        "longitude": "",
        "bqpLastName": "",
        "deviceDeliveryMethod": "",
        "mailingCity": "",
        "deviceReimbursementDate": "",
        "consumerFee": "0",
        "bqpLast4ssn": "",
        "bqpFirstName": "",
        "expectedRate": "",
        "repId": "",
        "repNotAssisted": "1",
        "schoolLunchException": "",
        "ebbpTribalBenefitFlag": "0",
        "schoolLunchCert": "",
        "modelNumber": "",
        "deviceCopay": "",
        "contactPhoneNumber": "",
        "consumerEmail": "",
        "acpCertInd": "1"
    }

    return access_token, data


@app.route("/report/selection", methods=["GET", "POST"])
def select_parameters():
    if request.method == "POST":
        sac = request.form.get("sac")
        month = request.form.get('month')
        return redirect(url_for('transaction_report', sac=sac, month=month))
    return render_template('selection_form.html', sac_codes=SAC_CODES, year=datetime.now().strftime('%Y'),
                           date=date_format, public=f"Public IP: {ip.get()}")


@app.route("/report/transaction", methods=["GET", "POST"])
def transaction_report():
    sac = request.form.get('sac')
    month = request.form.get('month')
    endpoint = f"{acp_base_url}report/subscriber?reportType=detail&sac={sac}&includeSubscriberId=0&eligibilityMonth={month}&includeACPCertInd=1"

    # Proactively fetch a new token if it doesn't exist or if it's expired
    if not session.get("access_token") or datetime.now() >= session.get("token_expiry"):
        fetch_new_token()

    headers = {
        "Authorization": f"Bearer {session.get('access_token')}",
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)

    # If unauthorized, fetch new token and try again
    if response.status_code == 401:
        fetch_new_token()
        headers["Authorization"] = f"Bearer {session.get('access_token')}"
        response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        csv_content = response.text
        session['original_csv'] = csv_content  # Store the original csv for downloading
        excluded_columns = ["BQP Last Name", "BQP First Name", "Mailing Street Address", "Eligibility Program",
                            "Tribal Benefit Flag", "Mailing City", "Mailing State", "Mailing ZIP",
                            "Mailing Address Validated", "BQP Middle Name", "Device Reimbursement Date", "Device Type",
                            "Device Make", "Expected Device Reimbursement Rate", "Device Copay",
                            "Device Delivery Method", "Device Model", "Model Number", "Market Value", "Consumer Fee",
                            "Consumer Email", "AVP Program Exception", "School Lunch Exception", "School Name",
                            "AMS Failure Exception", "Latitude", "Longitude", "Duplicate Address Exception",
                            "Expected Reimbursement Rate", "ACPCertInd", "Middle Name", "ETC General Use",
                            "Device Claimed", "Device Claimed Date",
                            "Eligible for Transfer Date"]  # Replace with your column names
        parsed_csv = exclude_csv_columns(csv_content, excluded_columns)

        return render_template('csv_viewer.html', csv_content=parsed_csv, year=datetime.now().strftime('%Y'),
                               date=date_format, public=f"Public IP: {ip.get()}")
    else:
        try:
            response_data = response.json()
            failure_type = "JSON Response"
            body_messages = str(response_data)
        except json.JSONDecodeError:
            failure_type = "Non-JSON Response or Empty Response"
            body_messages = response.text

        return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400


def exclude_csv_columns(csv_content, excluded_columns):
    input_csv = StringIO(csv_content)
    output_csv = StringIO()

    reader = csv.DictReader(input_csv)
    fieldnames = [field for field in reader.fieldnames if field not in excluded_columns]
    writer = csv.DictWriter(output_csv, fieldnames=fieldnames)

    writer.writeheader()
    for row in reader:
        # Exclude the columns from each row
        filtered_row = {key: row[key] for key in row if key not in excluded_columns}
        writer.writerow(filtered_row)

    return output_csv.getvalue()


@app.route("/report/download_csv", methods=["GET"])
def download_csv():
    csv_content = session.get('original_csv')
    if not csv_content:
        return "No CSV available", 400

    # Create a BytesIO buffer and write CSV content to it.
    buffer = BytesIO()
    buffer.write(csv_content.encode('utf-8'))
    buffer.seek(0)  # Reset file position to the beginning.

    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name="report.csv")


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG_MODE", "False").lower() == "true"
    # app.run(port=80, debug=debug_mode)
    app.run(port=80, debug=True)
