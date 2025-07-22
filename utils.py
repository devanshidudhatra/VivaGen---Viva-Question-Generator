import csv
import os
from datetime import datetime
from flask import current_app
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import ast

# This list must match what you write AND read
SUBMISSION_FIELDS = [
    'submission_id', 'assignment_id', 'student_id',
    'questions', 'evaluation', 'submission_time'
]

def load_assignments(filename):
    assignments = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assignments[row['assignment_id']] = dict(row)
    return assignments

def save_assignment(filename, assignment_data):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['assignment_id', 'title', 'description', 'subject', 'deadline', 'grading_criteria'])
        if not file_exists:
            writer.writeheader()
        writer.writerow(assignment_data)
    upload_assignments_to_mongodb()

def save_submission(filename, submission_data):
    if 'submission_time' not in submission_data:
        submission_data['submission_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(submission_data['questions'], list):
        submission_data['questions'] = '|'.join(submission_data['questions'])
    # Ensure evaluation is always a dict
    if isinstance(submission_data['evaluation'], str):
        try:
            submission_data['evaluation'] = ast.literal_eval(submission_data['evaluation'])
        except (ValueError, SyntaxError):
            submission_data['evaluation'] = {}
    elif not isinstance(submission_data['evaluation'], dict):
        submission_data['evaluation'] = {}
    data = {k: submission_data.get(k) for k in SUBMISSION_FIELDS}
    # Convert evaluation to string for CSV
    data['evaluation'] = str(data['evaluation'])
    file_exists = os.path.isfile(filename)
    with open(filename, 'a+', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SUBMISSION_FIELDS)
        if not file_exists or os.path.getsize(filename) == 0:
            writer.writeheader()
        writer.writerow(data)
    upload_submissions_to_mongodb()

def update_submission(filename, submission_id, update_fields):
    submissions = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['submission_id'] == submission_id:
                for key, value in update_fields.items():
                    if key == 'questions' and isinstance(value, list):
                        row[key] = '|'.join(value)
                    elif key == 'evaluation' and isinstance(value, dict):
                        row[key] = str(value)
                    else:
                        row[key] = value
            # Ensure evaluation is a dict before saving
            try:
                row['evaluation'] = ast.literal_eval(row['evaluation']) if row['evaluation'] else {}
            except (ValueError, SyntaxError):
                row['evaluation'] = {}
            submissions.append(row)
    # Write back, converting evaluation to string
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SUBMISSION_FIELDS)
        writer.writeheader()
        writer.writerows([
            {k: str(v) if k == 'evaluation' and isinstance(v, dict) else v for k, v in s.items()}
            for s in submissions
        ])
    upload_submissions_to_mongodb()
    
def upload_assignments_to_mongodb():
    """Upload the contents of assignments.csv to MongoDB."""
    client = None  # Safe to close in finally even if try fails
    try:
        mongo_uri = current_app.config['MONGO_URI']
        db_name = current_app.config['DATABASE_NAME']
        client = MongoClient(mongo_uri)
        client.admin.command('ping')  # Check connection
        db = client[db_name]
        assignments_collection = db['assignments']
        assignments_collection.delete_many({})
        filename = 'data/assignments.csv'
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                assignments_collection.insert_one(row)
        print("Uploaded assignments to MongoDB")
    except ConnectionFailure as e:
        print(f"Connection to MongoDB failed: {e}")
    except Exception as e:
        print(f"Error uploading assignments to MongoDB: {e}")
    finally:
        if client:
            client.close()

# Do the same for upload_submissions_to_mongodb
def upload_submissions_to_mongodb():
    client = None
    try:
        mongo_uri = current_app.config['MONGO_URI']
        db_name = current_app.config['DATABASE_NAME']
        client = MongoClient(mongo_uri)
        db = client[db_name]
        submissions_collection = db['submissions']
        submissions_collection.delete_many({})
        filename = 'data/submissions.csv'
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                submissions_collection.insert_one(row)
        print("Uploaded submissions to MongoDB")
    except ConnectionFailure as e:
        print(f"Connection to MongoDB failed: {e}")
    except Exception as e:
        print(f"Error uploading submissions to MongoDB: {e}")
    finally:
        if client:
            client.close()