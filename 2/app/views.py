from flask import (Blueprint, render_template, redirect,
    url_for, flash)
from flask_login import login_user, logout_user, login_required
from .models import User
from .forms import LoginForm, RegisterForm
from app import db


bp = Blueprint('app', __name__,  url_prefix='')

@bp.route('/')
def index():
    return redirect(url_for('app.login'))
    
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('app.index'))
            else:
                flash('Invalid password.')
                return redirect(url_for('app.login'))
        else:
            flash('The email address is not registered.')
            return redirect(url_for('app.login'))
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.username.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Your info is registered correctly!')
        return redirect(url_for('app.login'))
    return render_template('register.html', form=form)
