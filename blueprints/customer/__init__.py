from flask import Blueprint

customer_bp = Blueprint('customer', __name__)

from blueprints.customer import routes
