# VivaGen

**Automated Student Assignment Viva Platform**  
**Intelligent Assignment Viva: Streamlining Oral Examination for Modern Education**

## Overview

**VivaGen** is a modern educational platform designed to **streamline and simplify the oral examination (viva) process** for professors and students. It enables professors to **automatically generate viva questions** from student assignments, **evaluate answers interactively**, and provide instant feedback. Students can **view their submissions**, scores, and detailed feedback in a clear, user-friendly dashboard.

## Key Features

- **Role-Based Access**: Separate dashboards for professors and students.
- **Assignment Management**: Professors create assignments; students submit work electronically.
- **AI-Powered Question Generation**: Automatically generates viva questions from student submissions.
- **Interactive Evaluation**: Professors evaluate each answer, provide scores and feedback, and edit assessments.
- **Instant Result Calculation**: Automatic calculation of final scores as the average of question scores.
- **Continuous Evaluation**: Professors can update scores and feedback at any time.
- **Student Dashboard**: Students view their submissions, individual scores, and feedback.
- **Modern UI**: Clean, responsive interface with consistent branding.

## Technology Stack

- **Backend**: Python, Flask
- **Database**: MongoDB (assignment and user data), CSV (submissions backup)
- **Fontend**: HTML, CSS, Bootstrap
- **Authentication**: Role-based (student/professor)
- **Deployment**: Local development server (Flask)

## Setup Instructions

1. **Clone the repository** (if available).
2. **Install dependencies**:
   ```
   pip install flask pymongo werkzeug
   ```
3. **Set up MongoDB**:  
   - Install MongoDB and create a database named `assignment_db`.
   - Update the `MONGO_URI` in `app.py` to your MongoDB connection string.
4. **Create data directories**:
   ```
   mkdir -p data data/assignments
   ```
5. **Run the application**:
   ```
   python app.py
   ```
6. **Access the platform**:  
   Open your browser to `http://127.0.0.1:5000` and log in as a **professor** or **student**.

## Usage

- **Professors**: Create assignments, view submissions, generate viva questions, evaluate answers, and provide feedback.
- **Students**: Submit assignments, view their answered questions, scores, and feedback.

## Future Enhancements

- **Integration with Learning Management Systems**
- **Automated result notifications**
- **Enhanced analytics and reporting**
- **Support for multiple assignment formats**

## License

This project is for educational use and academic demonstration. **Not for commercial distribution.**

**VivaGen – Making oral assessments smarter, faster, and more transparent.**

If you want a **tech stack section** with specific package versions, or a **contribution guide**, just ask!  
Let me know if you’d like to add your **name**, **contact info**, or **institution** to the README.
