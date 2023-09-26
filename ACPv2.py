import requests
import base64
import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime, timedelta
import csv
from io import StringIO
from flask import send_file

app = Flask(__name__)
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

api_id = os.getenv("ACP_API_ID")
api_key = os.getenv("ACP_API_KEY")
acp_token_url = "https://api.universalservice.org/auth/token"
acp_base_url = "https://api.universalservice.org/ebbp-svc/1/"

#########################################
#########################################
###  ENTER SAC CODES AND STATES HERE: ###
SAC_CODES = {
    "NY": "815160",
    "KY": "826163"
}
#########################################
#########################################

@app.route('/')
def home():
    return render_template('acp2.html')


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
        return render_template(f'acp_{action}.html')
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
    
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    dob = request.form.get("dob")
    dob_obj = datetime.strptime(dob, "%Y-%m-%d")
    formatted_dob = dob_obj.strftime("%m/%d/%Y")
    today_date = datetime.now().strftime("%m/%d/%Y")
    ssn_last4 = request.form.get("ssn_last4")
    address = request.form.get("address")
    unit_number = request.form.get("unit_number")
    city = request.form.get("city")
    state = request.form.get("state")
    zip_code = request.form.get("zip_code")
    phone_number = request.form.get("phone_number")

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
        "repNotAssisted": "",
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
    return render_template('selection_form.html', sac_codes=SAC_CODES)

@app.route("/report/transaction", methods=["GET", "POST"])
def transaction_report():
    # Corrected lines below:
    sac = request.form.get('sac')
    month = request.form.get('month')
    
    print(f"SAC submitted: {sac}")  # Debug print

    endpoint = f"{acp_base_url}report/subscriber?reportType=detail&sac={sac}&includeSubscriberId=0&eligibilityMonth={month}&includeACPCertInd=1"

    # Proactively fetch a new token if it doesn't exist or if it's expired (if you've implemented expiry tracking)
    if not session.get("access_token"): # or datetime.now() >= session.get("token_expiry"):
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
        excluded_columns = ["BQP Last Name","BQP First Name","Mailing Street Address","Eligibility Program","Tribal Benefit Flag","Mailing City","Mailing State","Mailing ZIP","Mailing Address Validated","BQP Middle Name","Device Reimbursement Date","Device Type","Device Make","Expected Device Reimbursement Rate","Device Copay","Device Delivery Method","Device Model","Model Number","Market Value","Consumer Fee","Consumer Email","AVP Program Exception","School Lunch Exception","School Name","AMS Failure Exception","Latitude","Longitude","Duplicate Address Exception","Expected Reimbursement Rate","ACPCertInd","Middle Name","ETC General Use","Device Claimed","Device Claimed Date","Eligible for Transfer Date"]  # Replace with your column names
        parsed_csv = exclude_csv_columns(csv_content, excluded_columns)

        return render_template('csv_viewer.html', csv_content=parsed_csv)
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
    # Assuming you stored the original csv_content in the session
    csv_content = session.get('original_csv')
    if not csv_content:
        return "No CSV available", 400

    output = StringIO(csv_content)
    output.seek(0)
    
    return send_file(output, mimetype="text/csv", as_attachment=True, attachment_filename="report.csv")



if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG_MODE", "False").lower() == "true"
    app.run(port=80, debug=debug_mode)