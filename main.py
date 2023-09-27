from flask import Flask
from blueprints.acp.routes import acp_bp
from blueprints.customer.routes import customer_bp
from blueprints.auth.routes import auth_bp
from blueprints.banking.routes import banking_bp
from configurations import flask_config, acp_config, splynx_config
from dotenv import load_dotenv
import os


app = Flask(__name__)


load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Registering blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(acp_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(banking_bp)


# Print routes for troubleshooting
for rule in app.url_map.iter_rules():
    print(rule)


# Loading configurations
app.config.from_object(flask_config)
app.config.from_object(acp_config)
app.config.from_object(splynx_config)


if __name__ == '__main__':
    app.run()
