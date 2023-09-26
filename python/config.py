import os
from datetime import datetime
from flask_config import *
from acp_config import *
from splynx_config import *

# Flask Secret Key
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# ACP Configuration
ACP_API_ID = os.getenv("ACP_API_ID")
ACP_API_KEY = os.getenv("ACP_API_KEY")
ACP_TOKEN_URL = "https://api.universalservice.org/auth/token"
ACP_BASE_URL = "https://api.universalservice.org/ebbp-svc/1/"

# SAC CODES Configuration
SAC_CODES = {
    "NY": "815160",
    "KY": "826163"
}

# Splynx Configuration
SPLYNX_BASE_URL = "https://crm.resibridge.com/api/2.0"
SPLYNX_CUSTOMER_URL = f"{SPLYNX_BASE_URL}/admin/customers/customer"
SPLYNX_PAYMENT_URL = f"{SPLYNX_BASE_URL}/admin/customers/customer-payment-accounts"
SPLYNX_TOKEN_URL = f"{SPLYNX_BASE_URL}/admin/auth/tokens"

# Splynx Auth
SPLYNX_KEY = os.getenv("SPLYNX_KEY")
SPLYNX_SECRET = os.getenv("SPLYNX_SECRET")

# Footer Date
days = datetime.now().strftime('%d')
day = int(days)
if 4 <= day <= 20 or 24 <= day <= 30:
    suffix = "th"
else:
    suffix = ["st", "nd", "rd"][day % 10 - 1]
date_format=datetime.now().strftime('%A %B') + " " +days+suffix

