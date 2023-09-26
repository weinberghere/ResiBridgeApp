from flask import Flask, render_template
from banking.routes import banking_bp
from customer.routes import customer_bp
from acp.routes import acp_bp
from config import FLASK_SECRET_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

app.register_blueprint(banking_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(acp_bp)

@app.route('/')
def index():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
