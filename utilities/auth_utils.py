import os
from flask import request
import hmac
import hashlib


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
