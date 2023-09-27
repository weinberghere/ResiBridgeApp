from flask import Blueprint, render_template, session, request, redirect, url_for
from utilities.auth_utils import generate_auth_header
import requests
from configurations.splynx_config import SPLYNX_PAYMENT_URL
from datetime import datetime
import public_ip as ip
from config import date_format

banking_bp = Blueprint('banking', __name__)


@banking_bp.route('/banking')
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
        response = requests.put(SPLYNX_PAYMENT_URL + f"?id={customer_id}--1", json={
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
