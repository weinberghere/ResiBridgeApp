import os

# Splynx Configuration
SPLYNX_BASE_URL = "https://crm.resibridge.com/api/2.0"
SPLYNX_CUSTOMER_URL = f"{SPLYNX_BASE_URL}/admin/customers/customer"
SPLYNX_PAYMENT_URL = f"{SPLYNX_BASE_URL}/admin/customers/customer-payment-accounts"
SPLYNX_TOKEN_URL = f"{SPLYNX_BASE_URL}/admin/auth/tokens"

# Splynx Auth
SPLYNX_KEY = os.getenv("SPLYNX_KEY")
SPLYNX_SECRET = os.getenv("SPLYNX_SECRET")