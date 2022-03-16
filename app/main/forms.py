from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class Forma(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


