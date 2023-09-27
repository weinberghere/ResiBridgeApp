from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from blueprints.auth import routes

print("Initializing auth blueprint")
