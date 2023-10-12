import functools
import requests
from datetime import datetime, timedelta
from flask import Blueprint, session, request, render_template, send_file, redirect, url_for
from io import BytesIO
from configurations.acp_config import ACP_BASE_URL, ACP_TOKEN_URL, ACP_API_ID, ACP_API_KEY, ACP_NV_BASE_URL
from config import SAC_CODES, date_format
import public_ip as ip
from dotenv import load_dotenv
from utils import exclude_csv_columns
import json

acp_bp = Blueprint('acp', __name__)
load_dotenv()


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
    response = requests.post(ACP_TOKEN_URL, headers=headers, auth=(ACP_API_ID, ACP_API_KEY))
    if response.status_code == 200:
        response_data = response.json()
        session["acp_access_token"] = response_data["access_token"]
        session["acp_token_expiry"] = (datetime.now() + timedelta(hours=1))
        return True
    else:
        return False


@acp_bp.route("/acp/<action>", methods=["GET", "POST"])
def acp_action(action):
    print("Entered acp_action route")
    if request.method == "GET":
        customer_data = session.get('new_customer_details', {})
        return render_template(f'acp_{action}.html', data=customer_data, year=datetime.now().strftime('%Y'),
                               date=date_format, public=f"Public IP: {ip.get()}")
    elif request.method == "POST":
        acp_access_token, data = prepare_data(action)
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

        endpoint = ACP_BASE_URL + endpoint_mapping[action]
        headers = {
            "Authorization": f"Bearer {acp_access_token}",
            "Content-Type": "application/json"
        }
        print("Headers for ACP Action Route:", headers)
        response = requests.post(endpoint, headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if isinstance(response_data, list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:
                if not session.get('acp_access_token'):
                    fetch_new_token()
                headers["Authorization"]: f"Bearer {session.get['acp_access_token']}"
                response = requests.post(endpoint, headers=headers, json=data)

            response_data = response.json()
            if isinstance(response_data, dict):
                failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            else:
                failure_type = "Unknown failure"
                body_messages = str(response_data)

            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400


@acp_bp.route("/report/selection", methods=["GET", "POST"])
def select_parameters():
    print("Entered acp_report_selection route")
    if request.method == "POST":
        sac = request.form.get("sac")
        month = request.form.get('month')
        return redirect(url_for('acp.transaction_report', sac=sac, month=month))
    return render_template('selection_form.html', sac_codes=SAC_CODES, year=datetime.now().strftime('%Y'),
                           date=date_format, public=f"Public IP: {ip.get()}")


@acp_bp.route('/confirm_transfer')
def confirm_transfer():
    return render_template('confirm_transfer.html')


@acp_bp.route('/handle_transfer', methods=['POST'])
def handle_transfer():
    decision = request.form.get('decision')
    if decision == 'Yes':
        # Call your transfer function here
        transfer_result = perform_transfer()
        return transfer_result
    elif decision == 'No':
        return redirect(url_for('acp.acp_action', action='verify'))
    else:
        return "Invalid decision."


def perform_transfer():
    # Import data and headers from the session variables
    data = session.get('data')
    headers = session.get('headers')

    # Update the transaction type for transfer
    data["transactionType"] = "transfer"

    # Make a request to the transfer route
    transfer_response = requests.post(ACP_BASE_URL + "transfer", headers=headers, json=data)

    # Check if the transfer was successful
    if transfer_response.status_code == 200:
        return "Subscriber successfully transferred"
    else:
        # Handle the error similarly to the previous error handling
        try:
            response_data = transfer_response.json()
            failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
            body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
        except json.JSONDecodeError:
            return f"*** Failure Type: Non-JSON Response or Empty Response.***<br><br><br>Details:<br>Received status code: {transfer_response.status_code}. Response content: {transfer_response.text} <br>", 500
        return body_messages


@acp_bp.route("/acp_verify", methods=["GET", "POST"])
def acp_verify():
    if request.method == "POST":
        access_token = session.get("access_token")
        if not access_token:
            fetch_new_token()
            access_token = session.get("access_token")

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        dob = request.form.get("dob")
        dob_obj = datetime.strptime(dob, "%Y-%m-%d")
        formatted_dob = dob_obj.strftime("%m/%d/%Y")
        serialized_dob = dob_obj.strftime('%Y-%m-%d')
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
            "primaryUrbanizationCode": "",
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
            "mailingUrbanizationCode": "",
            "avpPgrmException": "",
            "mailingState": "",
            "etcGeneralUse": "",
            "includeSubscriberId": "",
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
            "marketValue": "",
            "deviceCopay": "",
            "contactPhoneNumber": "",
            "consumerEmail": "",
            "acpCertInd": "1",
            "eligibilityCode": ""
        }

        headers = {
            "Authorization": f"Bearer {session.get('acp_access_token')}",
            "Content-Type": "application/json"
        }

        response = requests.post(ACP_BASE_URL + "verify", headers=headers, json=data)
        print(response.content)
        print(data)
        print(headers)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if response_data and isinstance(response_data,
                                                                                  list) else "Unexpected response format"
            return render_template('message_template.html', title=message, details="", json="")
        else:
            if response.status_code == 401:
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(ACP_BASE_URL + "verify", headers=headers, json=data)
                # If the second request is also not successful, return an error message
                if response.status_code != 200:
                    return f"Error after retrying with new token. Received status code: {response.status_code}", 500
            try:
                response_data = response.json()
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            except json.JSONDecodeError:
                return f"*** Failure Type: Non-JSON Response or Empty Response.***<br><br><br>Details:<br>Received status code: {response.status_code}. Response content: {response.text} <br>", 500

            if "The subscriber has not qualified" in body_messages:
                # Construct the data for the eligibility-check
                eligibility_data = {
                    "firstName": first_name,
                    "middleName": "",
                    "lastName": last_name,
                    "address": f"{address} {unit_number}",
                    "state": state,
                    "city": city,
                    "zipCode": zip_code,
                    "urbanizationCode": "",
                    "dob": serialized_dob,
                    "ssn4": ssn_last4,
                    "tribalId": "",
                    "bqpFirstName": "",
                    "bqpLastName": "",
                    "bqpDob": "",
                    "bqpSsn4": "",
                    "bqpTribalId": "",
                    "alternateId": "",
                    "bqpAlternateId": "",
                    "eligibilityProgramCode": "E2",
                    "publicHousingCode": "",
                    "consentInd": "y",
                    "contactPhoneNumber": phone_number,
                    "contactEmail": "",
                    "contactAddress": f"{address} {unit_number}",
                    "contactCity": city,
                    "contactState": state,
                    "contactZipCode": zip_code,
                    "contactUrbCode": "",
                    "repId": "",
                    "repNotAssisted": "1",
                    "carrierUrl": "https://www.resibridge.com"
                }
                nv_response = requests.post(ACP_NV_BASE_URL + "eligibility-check", headers=headers,
                                            json=eligibility_data)
                if nv_response.status_code == 200:
                    nv_data = nv_response.json()
                    # Return the data as a formatted string for display in the browser
                    return f"<pre>{json.dumps(nv_data, indent=4)}</pre>"
                elif nv_response.status_code == 400:
                    title = "Something Went Wrong"
                    details = "Error 400"
                    json_data = nv_response.content.decode('utf-8')  # Removed the curly braces
                    return render_template('message_template.html', title=title, details=details, json_data=json_data)
                else:
                    title = "Unexpected Response"
                    details = f"Received status code: {nv_response.status_code}"  # Added the status code here
                    json_data = nv_response.content.decode('utf-8')  # Removed the curly braces
                    return render_template('message_template.html', title=title, details=details, json_data=json_data)
            elif "transaction is a duplicate" in body_messages:
                session['data'] = data
                session['headers'] = headers
                return redirect(url_for('acp.confirm_transfer'))
            else:
                return render_template('message_template.html', title="Subscriber Qualified", details=body_messages,
                                       json="")
    else:  # This will handle the GET request
        customer_data = session.get('new_customer_details', {})
        return render_template('acp_verify.html', data=customer_data)


@acp_bp.route("/acp_enroll", methods=["GET", "POST"])
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
            "primaryUrbanizationCode": "",
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
            "mailingUrbanizationCode": "",
            "avpPgrmException": "",
            "mailingState": "",
            "etcGeneralUse": "",
            "includeSubscriberId": "",
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
            "marketValue": "",
            "deviceCopay": "",
            "contactPhoneNumber": "",
            "consumerEmail": "",
            "acpCertInd": "1",
            "eligibilityCode": ""
        }

        headers = {
            "Authorization": f"Bearer {session.get('acp_access_token')}",
            "Content-Type": "application/json"
        }

        response = requests.post(ACP_BASE_URL + "subscriber", headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if response_data and isinstance(response_data,
                                                                                  list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(ACP_BASE_URL + "enroll", headers=headers, json=data)

            response_data = response.json()

            # Check if response_data is a dictionary
            if isinstance(response_data, dict):
                failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            else:
                failure_type = "Unknown failure"
                body_messages = str(response_data)

            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400


@acp_bp.route("/acp_transfer", methods=["GET", "POST"])
def acp_transfer():
    if request.method == "GET":
        return render_template('acp_transfer.html')
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
            "primaryUrbanizationCode": "",
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
            "mailingUrbanizationCode": "",
            "avpPgrmException": "",
            "mailingState": "",
            "etcGeneralUse": "",
            "includeSubscriberId": "",
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
            "marketValue": "",
            "deviceCopay": "",
            "contactPhoneNumber": "",
            "consumerEmail": "",
            "acpCertInd": "1",
            "eligibilityCode": ""
        }

        headers = {
            "Authorization": f"Bearer {session.get('acp_access_token')}",
            "Content-Type": "application/json"
        }

        response = requests.post(ACP_BASE_URL + "transfer", headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            message = response_data[0]["message"] if response_data and isinstance(response_data,
                                                                                  list) else "Unexpected response format"
            return message
        else:
            if response.status_code == 401:
                fetch_new_token()
                headers["Authorization"] = f"Bearer {session.get('access_token')}"
                response = requests.post(ACP_BASE_URL + "transfer", headers=headers, json=data)

            response_data = response.json()

            # Check if response_data is a dictionary
            if isinstance(response_data, dict):
                failure_type = response_data.get("header", {}).get("failureType", "Unknown failure")
                body_messages = "<br>".join([" ".join(item) for item in response_data.get("body", [])])
            else:
                failure_type = "Unknown failure"
                body_messages = str(response_data)

            return f"*** Failure Type: {failure_type}.***<br><br><br>Details:<br>{body_messages} <br>", 400



@acp_bp.route("/report/transaction", methods=["GET", "POST"])
def transaction_report():
    print("Entered acp_report_transaction route")
    sac = request.form.get('sac')
    month = request.form.get('month')
    endpoint = f"{ACP_BASE_URL}report/subscriber?reportType=detail&sac={sac}&includeSubscriberId=0&eligibilityMonth={month}&includeACPCertInd=1"

    token_expiry_timestamp = session.get("acp_token_expiry")

    # Validate the token_expiry_timestamp
    if isinstance(token_expiry_timestamp, (int, float)):
        token_expiry = datetime.fromtimestamp(token_expiry_timestamp)
    else:
        print(f"Invalid token_expiry_timestamp type: {type(token_expiry_timestamp)}")
        token_expiry = None

    if not session.get("acp_access_token") or (token_expiry and datetime.now() >= token_expiry):
        fetch_new_token()

    headers = {
        "Authorization": f"Bearer {session.get('acp_access_token')}",
        "Content-Type": "application/json"
    }
    print("Headers for Transaction Report Route:", headers)
    response = requests.get(endpoint, headers=headers)

    # If unauthorized, fetch new token and try again
    if response.status_code == 401:
        fetch_new_token()
        headers["Authorization"] = f"Bearer {session.get('acp_access_token')}"
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


def prepare_data(action):
    print("Customer Details:", session.get('new_customer_details'))
    customer_data = session.get('new_customer_details', {})
    state = customer_data.get('state', '')
    sac_code = SAC_CODES.get(state, '')
    if not sac_code:
        return None, None
    # if action == 'verify':
    #     data = {
    #         "header": {
    #             "messageType": "VERIFY",
    #             "messageDateTime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    #             "messageVersion": "1.0",
    #             "sourceId": "SP",
    #             "destinationId": "AC",
    #             "businessUnit": "SP"
    #         },
    #         "body": {
    #             "serviceProvider": {
    #                 "serviceProviderId": "SP",
    #                 "serviceProviderName": "Service Provider"
    #             },
    #             "subscriber": {
    #                 "subscriberId": customer_data.get('id', ''),
    #                 "subscriberName": customer_data.get('name', ''),
    #                 "subscriberAddress": {
    #                     "addressLine1": customer_data.get('address', ''),
    #                     "city": customer_data.get('city', ''),
    #                     "state": state,
    #                     "zip": customer_data.get('zip', '')
    #                 },
    #                 "sac": {
    #                     "sacCode": sac_code
    #                 }
    #             }
    #         }
    #     }
    #     acp_access_token = session.get('acp_access_token')
    # elif action == 'enroll':
    #     data = {
    #         "header": {
    #             "messageType": "ENROLL",
    #             "messageDateTime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    #             "messageVersion": "1.0",
    #             "sourceId": "SP",
    #             "destinationId": "AC",
    #             "businessUnit": "SP"
    #         },
    #         "body": {
    #             "serviceProvider": {
    #                 "serviceProviderId": "SP",
    #                 "serviceProviderName": "Service Provider"
    #             },
    #             "subscriber": {
    #                 "subscriberId": customer_data.get('id', ''),
    #                 "subscriberName": customer_data.get('name', ''),
    #                 "subscriberAddress": {
    #                     "addressLine1": customer_data.get('address', ''),
    #                     "city": customer_data.get('city', ''),
    #                     "state": state,
    #                     "zip": customer_data.get('zip', '')
    #                 },
    #                 "sac": {
    #                     "sacCode": sac_code
    #                 },
    #                 "paymentMethod": {
    #                     "paymentMethodType": "ACH",
    #                     "paymentMethodAccount": {
    #                         "accountNumber": customer_data.get('account_number', ''),
    #                         "routingNumber": customer_data.get('routing_number', ''),
    #                         "accountName": customer_data.get('account_name', ''),
    #                         "accountType": customer_data.get('account_type', '')
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     acp_access_token = session.get('acp_access_token')
    else:
        data = None
        acp_access_token = None
    return data, acp_access_token


@acp_bp.route("/report/download_csv", methods=["GET"])
def download_csv():
    csv_content = session.get('original_csv')
    if not csv_content:
        return "No CSV available", 400
    buffer = BytesIO()
    buffer.write(csv_content.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name="report.csv")
