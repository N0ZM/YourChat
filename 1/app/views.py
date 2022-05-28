from flask import Blueprint, render_template
from .models import User


bp = Blueprint('app', __name__,  url_prefix='')

@bp.route('/')
def index():
    return render_template('login.html')
    