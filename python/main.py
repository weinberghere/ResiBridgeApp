from flask import Flask
from blueprints.acp.routes import acp_bp
from blueprints.customer.routes import customer_bp
from blueprints.auth.routes import auth_bp
from blueprints.banking.routes import banking_bp
from error_handlers import error_handlers_bp
import flask_config
import acp_config
import splynx_config

app = Flask(__name__)

# Registering blueprints
app.register_blueprint(acp_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(banking_bp)
app.register_blueprint(error_handlers_bp)

# Loading configurations
app.config.from_object(flask_config)
app.config.from_object(acp_config)
app.config.from_object(splynx_config)

if __name__ == '__main__':
    app.run()