import functools
import requests
from datetime import datetime, timedelta
from flask import Blueprint, session, request, render_template, redirect, url_for
from config import ACP_BASE_URL, ACP_TOKEN_URL, ACP_API_ID, ACP_API_KEY, SAC_CODES

acp_bp = Blueprint('acp', __name__)

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
        session["acp_token_expiry"] = (datetime.now() + timedelta(hours=1)).timestamp()
        return True
    else:
        return False

def prepare_data(action):
    customer_data = session.get('new_customer_details', {})
    state = customer_data.get('state', '')
    sac_code = SAC_CODES.get(state, '')
    if not sac_code:
        return None, None
    if action == 'verify':
        data = {
            "header": {
                "messageType": "VERIFY",
                "messageDateTime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "messageVersion": "1.0",
                "sourceId": "SP",
                "destinationId": "AC",
                "businessUnit": "SP"
            },
            "body": {
                "serviceProvider": {
                    "serviceProviderId": "SP",
                    "serviceProviderName": "Service Provider"
                },
                "subscriber": {
                    "subscriberId": customer_data.get('id', ''),
                    "subscriberName": customer_data.get('name', ''),
                    "subscriberAddress": {
                        "addressLine1": customer_data.get('address', ''),
                        "city": customer_data.get('city', ''),
                        "state": state,
                        "zip": customer_data.get('zip', '')
                    },
                    "sac": {
                        "sacCode": sac_code
                    }
                }
            }
        }
        access_token = session.get('acp_access_token')
    elif action == 'enroll':
        data = {
            "header": {
                "messageType": "ENROLL",
                "messageDateTime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "messageVersion": "1.0",
                "sourceId": "SP",
                "destinationId": "AC",
                "businessUnit": "SP"
            },
            "body": {
                "serviceProvider": {
                    "serviceProviderId": "SP",
                    "serviceProviderName": "Service Provider"
                },
                "subscriber": {
                    "subscriberId": customer_data.get('id', ''),
                    "subscriberName": customer_data.get('name', ''),
                    "subscriberAddress": {
                        "addressLine1": customer_data.get('address', ''),
                        "city": customer_data.get('city', ''),
                        "state": state,
                        "zip": customer_data.get('zip', '')
                    },
                    "sac": {
                        "sacCode": sac_code
                    },
                    "paymentMethod": {
                        "paymentMethodType": "ACH",
                        "paymentMethodAccount": {
                            "accountNumber": customer_data.get('account_number', ''),
                            "routingNumber": customer_data.get('routing_number', ''),
                            "accountName": customer_data.get('account_name', ''),
                            "accountType": customer_data.get('account_type', '')
                        }
                    }
                }
            }
        }
        access_token = session.get('acp_access_token')
    else:
        data = None
        access_token = None
    return data, access_token
