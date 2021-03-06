from flask_wtf import FlaskForm
from wtforms import (EmailField, PasswordField, BooleanField,
    SubmitField, StringField, TextAreaField)
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):

    email = EmailField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegisterForm(FlaskForm):

    username = StringField('Username')
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class MessageForm(FlaskForm):

    message = TextAreaField('Message:', validators=[DataRequired()])
    submit = SubmitField('Submit')
    