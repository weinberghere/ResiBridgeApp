import csv
from io import StringIO, BytesIO
from flask import send_file, session, request
import os
import hmac
import hashlib
from main import app

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