import requests
import base64
import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
load_dotenv()

api_id = os.getenv("ACP_API_ID")
api_key = os.getenv("ACP_API_KEY")
acp_token_url = "https://api.universalservice.org/auth/token"
acp_base_url = "https://api.universalservice.org/ebbp-svc/1/"

@app.route('/')
def home():
    return render_template('acp2.html')

def fetch_new_token():
    headers = {
        "Content-Type": "application/json"
    }
    credentials = f"{api_id}:{api_key}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(acp_token_url, headers=headers, data=data, auth=(api_id, api_key))
    if response.status_code == 200:
        response_data = response.json()
        session["access_token"] = response_data["access_token"]

@app.route("/acp_verify", methods=["GET", "POST"])
def acp_verify():
    if request.method == "GET":
        return render_template('acp_verify.html')
    elif request.method == "POST":
        access_token = session.get("access_token")
        if not access_token:
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

        if state == "NY":
            sac = "815160"
        elif state == "KY":
            sac = "826163"
        else:
            sac = ""  # default value if state is neither NY nor KY

        data = {
            "applicationId": "",
            "transactionType": "enroll",
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

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(acp_base_url + "verify", headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if response_data and isinstance(response_data, list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:  # Assuming 401 is the code for unauthorized due to token expiry
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(acp_base_url + "verify", headers=headers, json=data)
                # Additional error handling might be required here for the second attempt
            response_data = response.json()
            failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
            body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400

@app.route("/acp_enroll", methods=["GET", "POST"])
def acp_enroll():
    if request.method == "GET":
        return render_template('acp_enroll.html')
    elif request.method == "POST":
        access_token = session.get("access_token")
        if not access_token:
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

        if state == "NY":
            sac = "815160"
        elif state == "KY":
            sac = "826163"
        else:
            sac = ""  # default value if state is neither NY nor KY

        data = {
            "applicationId": "",
            "transactionType": "enroll",
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

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(acp_base_url + "subscriber", headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if response_data and isinstance(response_data, list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:  # Assuming 401 is the code for unauthorized due to token expiry
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(acp_base_url + "verify", headers=headers, json=data)
                # Additional error handling might be required here for the second attempt

            response_data = response.json()

            # Check if response_data is a dictionary
            if isinstance(response_data, dict):
                failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            else:  # If it's not a dictionary (probably a list or something else)
                failure_type = "Unknown failure"
                body_messages = str(response_data)  # convert whatever it is to a string

            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400

@app.route("/report/transaction", methods=["GET"])
def transaction_report():
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    endpoint = f"{acp_base_url}report/subscriber?reportType=detail&sac=826163&includeSubscriberId=0&eligibilityMonth=09&includeACPCertInd=1"

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
        return render_template('csv_viewer.html', csv_content=csv_content)
    else:
        try:
            response_data = response.json()
            failure_type = "JSON Response"
            body_messages = str(response_data)
        except json.JSONDecodeError:
            failure_type = "Non-JSON Response or Empty Response"
            body_messages = response.text
            
        return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400



if __name__ == "__main__":
    app.run(port=80, debug=True)