import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
from werkzeug.utils import secure_filename
import csv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import ast
from extractor import (
    extract_text,
    allowed_file
)
from utils import load_assignments, save_assignment, save_submission, update_submission
from groq_handler import generate_evaluation_questions

# --- Authentication Decorator ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

app.config['MONGO_URI'] = 'mongodb+srv://heetdobariya07:uDR0Eeztg9NllZUy@cluster.yn4nj.mongodb.net/resume_analyzer?retryWrites=true&w=majority'
app.config['DATABASE_NAME'] = 'assignment_db'

try:
    client = MongoClient(app.config['MONGO_URI'])
    db = client[app.config['DATABASE_NAME']]
    client.admin.command('ping')
    print("Connected to MongoDB")
except ConnectionFailure as e:
    print(f"Connection to MongoDB failed: {e}")
    db = None

app.config['UPLOAD_FOLDER'] = 'data/assignments'
app.config['ASSIGNMENTS_FILE'] = 'data/assignments.csv'
app.config['SUBMISSIONS_FILE'] = 'data/submissions.csv'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
assignments = load_assignments(app.config['ASSIGNMENTS_FILE'])

@app.route('/')
def index():
    return redirect(url_for('login'))

# Login/Logout
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    users_collection = db['users']
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']

        if users_collection.find_one({'email': email}):
            return render_template('signup.html', error="Email already registered.")

        hashed_pw = generate_password_hash(password)
        user = {
            'email': email,
            'password': hashed_pw,
            'role': role
        }
        users_collection.insert_one(user)
        session['user_id'] = str(user['_id'])
        session['email'] = user['email']
        session['role'] = user['role']
        if role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    users_collection = db['users']
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']

        user = users_collection.find_one({'email': email, 'role': role})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user['role']
            if role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Teacher Routes ---
@app.route('/teacher')
@login_required(role='teacher')
def teacher_dashboard():
    return render_template('teacher/dashboard.html', assignments=assignments)

@app.route('/teacher/create_assignment', methods=['GET', 'POST'])
@login_required(role='teacher')
def create_assignment():
    if request.method == 'POST':
        assignment_id = str(uuid.uuid4())
        assignment_data = {
            'assignment_id': assignment_id,
            'title': request.form['title'],
            'description': request.form['description'],
            'subject': request.form['subject'],
            'deadline': request.form['deadline'],
            'grading_criteria': request.form['criteria']
        }
        save_assignment(app.config['ASSIGNMENTS_FILE'], assignment_data)
        assignments[assignment_id] = assignment_data
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher/create_assignment.html')

@app.route('/teacher/evaluate/<submission_id>', methods=['POST'])
@login_required(role='teacher')
def evaluate_submission(submission_id):
    evaluation_data = request.json
    update_submission(
        app.config['SUBMISSIONS_FILE'],
        submission_id,
        {'evaluation': evaluation_data}
    )
    return jsonify({'status': 'success'})

@app.route('/teacher/view_submissions/<assignment_id>')
def view_submissions(assignment_id):
    submissions = []
    with open(app.config['SUBMISSIONS_FILE'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['assignment_id'] == assignment_id:
                # Convert evaluation from string to dict
                try:
                    row['evaluation'] = eval(row['evaluation']) if row['evaluation'].strip() else {}
                except (SyntaxError, ValueError, AttributeError):
                    row['evaluation'] = {}
                submissions.append(row)
    assignment = next((a for id, a in assignments.items() if id == assignment_id), None)
    if not assignment:
        return "Assignment not found"
    return render_template('teacher/view_submissions.html', submissions=submissions, assignment=assignment)

# --- Student Routes ---
@app.route('/student')
@login_required(role='student')
def student_dashboard():
    return render_template('student/dashboard.html', assignments=assignments)

@app.route('/student/view_assignments/<assignment_id>')
@login_required(role='student')
def view_assignment(assignment_id):
    assignment = assignments.get(assignment_id)
    if assignment:
        return render_template('student/view_assignments.html', assignment=assignment)
    else:
        return "Assignment not found"  

@app.route('/student/submit_assignment/<assignment_id>', methods=['POST'])
@login_required(role='student')
def submit_assignment(assignment_id):
    student_id = session.get('user_id', 'test_student')  # Use logged-in student ID
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            assignment_text = extract_text(filepath)
            evaluation_questions = generate_evaluation_questions(assignment_text)
            if not evaluation_questions:
                return jsonify({'error': 'Could not generate evaluation questions'}), 500
            submission_data = {
                'submission_id': str(uuid.uuid4()),
                'assignment_id': assignment_id,
                'student_id': session.get('user_id'),
                'questions': evaluation_questions,
                'evaluation': {},
                'submission_time': datetime.now().isoformat()
            }
            save_submission(app.config['SUBMISSIONS_FILE'], submission_data)
            return jsonify({
                'submission_id': submission_data['submission_id'],
                'questions': evaluation_questions
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file type'}), 400


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
