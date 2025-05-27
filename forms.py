from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class TravelForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    location = StringField('Местоположение', validators=[DataRequired(), Length(max=200)])
    image = FileField('Фото', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    comfort = IntegerField('Оценка удобства (1-10)', validators=[NumberRange(min=1, max=10)])
    safety = IntegerField('Оценка безопасности (1-10)', validators=[NumberRange(min=1, max=10)])
    population = IntegerField('Оценка населенности (1-10)', validators=[NumberRange(min=1, max=10)])
    vegetation = IntegerField('Оценка растительности (1-10)', validators=[NumberRange(min=1, max=10)])
    submit = SubmitField('Добавить путешествие') 