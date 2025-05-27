from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db, login_manager, csrf
from models import User, Travel
from forms import RegistrationForm, LoginForm, TravelForm
from flask_login import login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь уже существует', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверные имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_travel():
    form = TravelForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        travel = Travel(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            image_filename=filename,
            comfort=form.comfort.data,
            safety=form.safety.data,
            population=form.population.data,
            vegetation=form.vegetation.data,
            author=current_user
        )
        db.session.add(travel)
        db.session.commit()
        flash('Путешествие добавлено!', 'success')
        return redirect(url_for('index'))
    return render_template('add_travel.html', form=form)

@app.route('/')
def index():
    travels = Travel.query.order_by(Travel.date_posted.desc()).all()
    return render_template('index.html', travels=travels)

@app.route('/user/<username>')
def user_travels(username):
    user = User.query.filter_by(username=username).first_or_404()
    travels = Travel.query.filter_by(author=user).order_by(Travel.date_posted.desc()).all()
    return render_template('user_travels.html', travels=travels, user=user)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True) 