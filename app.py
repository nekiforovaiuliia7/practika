from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import plotly
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///survey.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    responses = db.relationship('Response', backref='user', lazy=True)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON строка с вопросами
    responses = db.relationship('Response', backref='survey', lazy=True)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)  # JSON строка с ответами

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    surveys = Survey.query.all()
    return render_template('index.html', surveys=surveys)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/survey/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if request.method == 'POST':
        answers = request.form.to_dict()
        response = Response(
            user_id=current_user.id,
            survey_id=survey_id,
            answers=json.dumps(answers)
        )
        db.session.add(response)
        db.session.commit()
        flash('Спасибо за участие в опросе!')
        return redirect(url_for('index'))
    return render_template('survey.html', survey=survey)

@app.route('/admin/surveys')
@login_required
def admin_surveys():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    surveys = Survey.query.all()
    return render_template('admin/surveys.html', surveys=surveys)

@app.route('/admin/survey/new', methods=['GET', 'POST'])
@login_required
def new_survey():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        questions = request.form.getlist('questions[]')
        question_types = request.form.getlist('question_types[]')
        options = request.form.getlist('options[]')
        
        questions_data = []
        for i in range(len(questions)):
            q_data = {
                'text': questions[i],
                'type': question_types[i],
                'options': options[i].split(',') if question_types[i] in ['radio', 'checkbox'] else []
            }
            questions_data.append(q_data)
        
        survey = Survey(
            title=request.form['title'],
            questions=json.dumps(questions_data)
        )
        db.session.add(survey)
        db.session.commit()
        return redirect(url_for('admin_surveys'))
    return render_template('admin/new_survey.html')

@app.route('/admin/survey/<int:survey_id>/results')
@login_required
def survey_results(survey_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    survey = Survey.query.get_or_404(survey_id)
    responses = Response.query.filter_by(survey_id=survey_id).all()
    
    # Создаем графики для каждого вопроса
    graphs = []
    questions = json.loads(survey.questions)
    
    for i, question in enumerate(questions):
        if question['type'] in ['radio', 'checkbox']:
            answers = []
            for response in responses:
                resp_data = json.loads(response.answers)
                if f'question_{i}' in resp_data:
                    if question['type'] == 'checkbox':
                        answers.extend(resp_data[f'question_{i}'])
                    else:
                        answers.append(resp_data[f'question_{i}'])
            
            df = pd.DataFrame({'answer': answers})
            fig = px.histogram(df, x='answer', title=question['text'])
            graphs.append(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
    
    return render_template('admin/results.html', survey=survey, graphs=graphs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создаем администратора, если его нет
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True) 