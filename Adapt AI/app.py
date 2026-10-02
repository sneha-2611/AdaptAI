import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from database.db import get_db_connection, init_db
from services.adaptive_engine import (
    evaluate_diagnostic, 
    generate_personalised_roadmap, 
    get_student_roadmap, 
    record_quiz_submission, 
    get_dashboard_data
)
from services.ai_service import (
    generate_lesson_content, 
    ask_ai_tutor, 
    get_adaptive_quiz_question, 
    get_tutor_history,
    LLM_API_KEY
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "adaptai_super_secret_hackathon_key_2026")

# Initialize database on app startup
with app.app_context():
    init_db()

@app.context_processor
def inject_global_data():
    """Inject active student data and LLM status into all templates."""
    active_student = None
    student_id = session.get('student_id')
    if student_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        if row:
            active_student = dict(row)
        conn.close()

    return {
        'active_student': active_student,
        'has_api_key': bool(LLM_API_KEY),
        'llm_mode': "Live LLM API" if LLM_API_KEY else "Adaptive Knowledge Engine (Offline Demo)"
    }

# ==========================================
# PAGE ROUTES
# ==========================================

@app.route('/')
def index():
    """Landing Page (Page A)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY created_at DESC LIMIT 5")
    recent_students = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return render_template('index.html', recent_students=recent_students)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Student Setup (Page B)"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        initial_level = request.form.get('initial_level', 'Beginner')
        target_topic = request.form.get('target_topic', 'AI Fundamentals')

        if not name:
            name = "Student Learner"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (name, initial_level, target_topic, current_level)
            VALUES (?, ?, ?, ?)
        """, (name, initial_level, target_topic, initial_level))
        student_id = cursor.lastrowid
        conn.commit()
        conn.close()

        session['student_id'] = student_id
        return redirect(url_for('assessment'))

    return render_template('setup.html')

@app.route('/assessment')
def assessment():
    """Diagnostic Assessment (Page C)"""
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('setup'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, topic_id, topic_name, question, options, difficulty FROM diagnostic_questions ORDER BY id ASC")
    raw_questions = cursor.fetchall()
    conn.close()

    questions = []
    for q in raw_questions:
        q_dict = dict(q)
        q_dict['options'] = json.loads(q_dict['options'])
        questions.append(q_dict)

    return render_template('assessment.html', questions=questions, student_id=student_id)

@app.route('/api/assessment/submit', methods=['POST'])
def submit_assessment():
    """Handle assessment submission and compute results"""
    data = request.get_json() or {}
    student_id = data.get('student_id') or session.get('student_id')
    answers = data.get('answers', {})

    if not student_id:
        return jsonify({'error': 'No active student identified'}), 400

    results = evaluate_diagnostic(student_id, answers)
    return jsonify({
        'success': True,
        'redirect_url': url_for('results', student_id=student_id),
        'results': results
    })

@app.route('/results/<int:student_id>')
def results(student_id):
    """Assessment Results & Learning Profile (Page D)"""
    session['student_id'] = student_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM assessment_results 
        WHERE student_id = ? 
        ORDER BY completed_at DESC LIMIT 1
    """, (student_id,))
    res_row = cursor.fetchone()
    conn.close()

    if not student or not res_row:
        return redirect(url_for('setup'))

    res_data = dict(res_row)
    res_data['strong_topics'] = json.loads(res_data['strong_topics'])
    res_data['weak_topics'] = json.loads(res_data['weak_topics'])

    return render_template('results.html', student=dict(student), result=res_data)

@app.route('/learning-path/<int:student_id>')
def learning_path(student_id):
    """Personalised Learning Path Roadmap (Page E)"""
    session['student_id'] = student_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return redirect(url_for('setup'))

    roadmap = get_student_roadmap(student_id)
    if not roadmap:
        # If not generated yet, generate default based on current level
        generate_personalised_roadmap(student_id, student['current_level'], [], [])
        roadmap = get_student_roadmap(student_id)

    return render_template('learning_path.html', student=dict(student), roadmap=roadmap)

@app.route('/tutor/<int:student_id>/<topic_id>')
def tutor(student_id, topic_id):
    """AI Tutor Learning Page (Page F)"""
    session['student_id'] = student_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student_row = cursor.fetchone()

    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    topic_row = cursor.fetchone()

    # Get student's weak areas from diagnostic
    cursor.execute("""
        SELECT weak_topics FROM assessment_results 
        WHERE student_id = ? ORDER BY completed_at DESC LIMIT 1
    """, (student_id,))
    ar_row = cursor.fetchone()
    weak_topics = json.loads(ar_row['weak_topics']) if ar_row else []

    # Get topic progress and current difficulty
    cursor.execute("""
        SELECT difficulty, progress_pct, status 
        FROM student_learning_path 
        WHERE student_id = ? AND topic_id = ?
    """, (student_id, topic_id))
    path_row = cursor.fetchone()
    conn.close()

    if not student_row or not topic_row:
        return redirect(url_for('learning_path', student_id=student_id))

    student = dict(student_row)
    topic = dict(topic_row)
    topic_diff = path_row['difficulty'] if path_row else "medium"
    topic_progress = path_row['progress_pct'] if path_row else 0

    # Map difficulty to lesson level
    diff_to_level = {
        'easy': 'Beginner',
        'medium': student.get('current_level', 'Intermediate'),
        'hard': 'Advanced'
    }
    learner_level = diff_to_level.get(topic_diff, student.get('current_level', 'Intermediate'))

    # Generate tailored lesson content
    lesson = generate_lesson_content(topic_id, student_level=learner_level, weak_topics=weak_topics)

    # Fetch past tutor chat history
    chat_history = get_tutor_history(student_id, topic_id)

    return render_template(
        'tutor.html', 
        student=student, 
        topic=topic, 
        lesson=lesson, 
        topic_diff=topic_diff,
        topic_progress=topic_progress,
        chat_history=chat_history
    )

@app.route('/api/tutor/ask', methods=['POST'])
def tutor_ask():
    """Handle conversational question to AI Tutor"""
    data = request.get_json() or {}
    student_id = data.get('student_id') or session.get('student_id')
    topic_id = data.get('topic_id')
    question = data.get('question', '').strip()

    if not student_id or not topic_id or not question:
        return jsonify({'error': 'Missing parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, current_level FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    student_name = student['name'] if student else "Learner"
    student_level = student['current_level'] if student else "Intermediate"

    answer = ask_ai_tutor(student_id, topic_id, question, student_name, student_level)
    return jsonify({
        'success': True,
        'question': question,
        'answer': answer
    })

@app.route('/quiz/<int:student_id>/<topic_id>')
def quiz(student_id, topic_id):
    """Adaptive Quiz Page (Page G)"""
    session['student_id'] = student_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student_row = cursor.fetchone()

    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    topic_row = cursor.fetchone()

    cursor.execute("""
        SELECT difficulty, progress_pct FROM student_learning_path 
        WHERE student_id = ? AND topic_id = ?
    """, (student_id, topic_id))
    path_row = cursor.fetchone()
    conn.close()

    if not student_row or not topic_row:
        return redirect(url_for('learning_path', student_id=student_id))

    current_difficulty = path_row['difficulty'] if path_row else "medium"
    topic_progress = path_row['progress_pct'] if path_row else 0

    # Get first adaptive question
    first_question = get_adaptive_quiz_question(student_id, topic_id, difficulty=current_difficulty)

    return render_template(
        'quiz.html', 
        student=dict(student_row), 
        topic=dict(topic_row), 
        current_difficulty=current_difficulty,
        topic_progress=topic_progress,
        first_question=first_question
    )

@app.route('/api/quiz/submit', methods=['POST'])
def quiz_submit():
    """Submit a quiz answer, evaluate, and trigger adaptive difficulty update"""
    data = request.get_json() or {}
    student_id = data.get('student_id') or session.get('student_id')
    topic_id = data.get('topic_id')
    question_id = data.get('question_id')
    chosen_idx = data.get('chosen_index')
    current_difficulty = data.get('current_difficulty', 'medium')

    if not student_id or not topic_id or question_id is None or chosen_idx is None:
        return jsonify({'error': 'Invalid request parameters'}), 400

    result = record_quiz_submission(student_id, topic_id, question_id, chosen_idx, current_difficulty)
    if not result:
        return jsonify({'error': 'Question evaluation failed'}), 500

    return jsonify({
        'success': True,
        'result': result
    })

@app.route('/api/quiz/next-question')
def next_quiz_question():
    """Fetch next adaptive question based on updated difficulty"""
    student_id = request.args.get('student_id', type=int) or session.get('student_id')
    topic_id = request.args.get('topic_id')
    difficulty = request.args.get('difficulty', 'medium')
    exclude_ids_raw = request.args.get('exclude_ids', '')
    exclude_ids = [int(i) for i in exclude_ids_raw.split(',') if i.isdigit()]

    if not student_id or not topic_id:
        return jsonify({'error': 'Missing parameters'}), 400

    question = get_adaptive_quiz_question(student_id, topic_id, difficulty=difficulty, exclude_ids=exclude_ids)
    return jsonify({
        'success': True,
        'question': question
    })

@app.route('/dashboard/<int:student_id>')
def dashboard(student_id):
    """Progress Dashboard (Page H)"""
    session['student_id'] = student_id
    dash_data = get_dashboard_data(student_id)
    if not dash_data:
        return redirect(url_for('setup'))

    return render_template('dashboard.html', **dash_data)

@app.route('/select-student/<int:student_id>')
def select_student(student_id):
    """Switch active student"""
    session['student_id'] = student_id
    return redirect(url_for('dashboard', student_id=student_id))

# ==========================================
# DEMO & TESTING UTILITY ROUTES
# ==========================================

@app.route('/demo/scenario/<int:scenario_num>')
def load_scenario(scenario_num):
    """
    Directly sets up one of the 3 hackathon test scenarios requested in the prompt:
    Scenario 1: High assessment score (Advanced recommendation, hard practice)
    Scenario 2: Low assessment score (Beginner explanation, revision flagged, easy practice)
    Scenario 3: Learner initially low but improving (adaptive upgrade demo)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if scenario_num == 1:
        # High score learner
        cursor.execute("INSERT INTO students (name, initial_level, current_level, target_topic) VALUES ('Priya (Advanced)', 'Advanced', 'Advanced', 'Deep Learning Basics')")
        s_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO assessment_results (student_id, score, total_questions, percentage, knowledge_level, strong_topics, weak_topics)
            VALUES (?, 9, 10, 90.0, 'Advanced', '["AI Fundamentals", "Machine Learning Basics", "Supervised Learning", "Classification"]', '["Deep Learning Basics"]')
        """, (s_id,))
        conn.commit()
        conn.close()
        generate_personalised_roadmap(s_id, 'Advanced', ["AI Fundamentals", "Machine Learning Basics", "Supervised Learning", "Classification"], ["Deep Learning Basics"])
        session['student_id'] = s_id
        return redirect(url_for('dashboard', student_id=s_id))

    elif scenario_num == 2:
        # Low score learner
        cursor.execute("INSERT INTO students (name, initial_level, current_level, target_topic) VALUES ('Alex (Beginner)', 'Beginner', 'Beginner', 'AI Fundamentals')")
        s_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO assessment_results (student_id, score, total_questions, percentage, knowledge_level, strong_topics, weak_topics)
            VALUES (?, 3, 10, 30.0, 'Beginner', '[]', '["Machine Learning Basics", "Regression", "Deep Learning Basics"]')
        """, (s_id,))
        conn.commit()
        conn.close()
        generate_personalised_roadmap(s_id, 'Beginner', [], ["Machine Learning Basics", "Regression", "Deep Learning Basics"])
        session['student_id'] = s_id
        return redirect(url_for('dashboard', student_id=s_id))

    else:
        # Intermediate / developing learner
        cursor.execute("INSERT INTO students (name, initial_level, current_level, target_topic) VALUES ('Sneha (Intermediate)', 'Intermediate', 'Intermediate', 'Regression')")
        s_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO assessment_results (student_id, score, total_questions, percentage, knowledge_level, strong_topics, weak_topics)
            VALUES (?, 6, 10, 60.0, 'Intermediate', '["AI Fundamentals", "Classification"]', '["Regression", "Deep Learning Basics"]')
        """, (s_id,))
        conn.commit()
        conn.close()
        generate_personalised_roadmap(s_id, 'Intermediate', ["AI Fundamentals", "Classification"], ["Regression", "Deep Learning Basics"])
        session['student_id'] = s_id
        return redirect(url_for('dashboard', student_id=s_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
        error_code='404', 
        error_title='Page Not Found',
        error_message='The page or resource you are looking for does not exist.'
    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
        error_code='500', 
        error_title='Temporary Service Hiccup',
        error_message='An unexpected error occurred. Please return to your learning path or dashboard.'
    ), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
