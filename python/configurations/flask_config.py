# Flask specific configurations
import os
DEBUG = True
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
