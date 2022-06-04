from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_babel import _


class LoginForm(FlaskForm):
    username = StringField(_('Логин'), validators=[DataRequired()])
    password = PasswordField(_('Пароль'), validators=[DataRequired()])
    submit = SubmitField(_('Вход'))


class Forma(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


