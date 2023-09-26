from flask import Blueprint, render_template

banking_bp = Blueprint('banking', __name__)

@banking_bp.route('/banking')
def banking():
    return render_template('banking.html')
