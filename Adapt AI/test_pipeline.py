import sys
from app import app
from database.db import init_db, get_db_connection

def test_full_pipeline():
    print("=== STARTING ADAPTAI PIPELINE VERIFICATION ===")
    
    # 1. Initialize DB
    init_db()
    print("[PASS] Database initialized and seeded successfully.")
    
    client = app.test_client()

    # 2. Test Landing Page (Page A)
    res = client.get('/')
    assert res.status_code == 200, f"Landing failed with {res.status_code}"
    assert b"AdaptAI" in res.data
    assert b"Personalised AI Tutor for Learning AI" in res.data
    print("[PASS] Landing page loads correctly.")

    # 3. Test Student Setup (Page B)
    res = client.post('/setup', data={
        'name': 'Sneha Test',
        'initial_level': 'Intermediate',
        'target_topic': 'Regression'
    }, follow_redirects=False)
    assert res.status_code == 302, f"Setup post failed: {res.status_code}"
    print("[PASS] Student Setup redirects to assessment.")

    with client.session_transaction() as sess:
        student_id = sess.get('student_id')
        assert student_id is not None, "Student ID was not stored in session"
    print(f"[PASS] Active Student created with ID: {student_id}")

    # 4. Test Diagnostic Assessment (Page C)
    res = client.get('/assessment')
    assert res.status_code == 200
    assert b"Question 1 of" in res.data
    print("[PASS] Diagnostic Assessment page loaded questions.")

    # 5. Test Assessment Submission (Diagnostic Evaluation)
    # Simulate answering 7 out of 10 correctly
    sample_answers = {
        "1": 0, # correct
        "2": 1, # correct
        "3": 1, # correct
        "4": 2, # correct
        "5": 1, # correct
        "6": 1, # correct
        "7": 0, # incorrect
        "8": 1, # correct
        "9": 2, # incorrect
        "10": 0 # incorrect
    }
    res = client.post('/api/assessment/submit', json={
        'student_id': student_id,
        'answers': sample_answers
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'knowledge_level' in data['results']
    print(f"[PASS] Diagnostic evaluation completed. Assigned level: {data['results']['knowledge_level']}")

    # 6. Test Assessment Results Page (Page D)
    res = client.get(f'/results/{student_id}')
    assert res.status_code == 200
    assert b"Your Learning Profile" in res.data
    print("[PASS] Assessment Results page rendered profile.")

    # 7. Test Personalised Learning Path (Page E)
    res = client.get(f'/learning-path/{student_id}')
    assert res.status_code == 200
    assert b"Your Learning Path" in res.data
    assert b"Recommended Next" in res.data or b"In Progress" in res.data
    print("[PASS] Personalised Learning Path roadmap rendered.")

    # 8. Test AI Tutor Page (Page F)
    res = client.get(f'/tutor/{student_id}/regression')
    assert res.status_code == 200
    assert b"Regression" in res.data
    assert b"Concept Overview" in res.data
    print("[PASS] AI Tutor lesson module rendered.")

    # 9. Test Ask AI Tutor API (Q&A)
    res = client.post('/api/tutor/ask', json={
        'student_id': student_id,
        'topic_id': 'regression',
        'question': 'Explain overfitting in simple words'
    })
    assert res.status_code == 200
    ask_data = res.get_json()
    assert ask_data['success'] is True
    assert len(ask_data['answer']) > 10
    print(f"[PASS] AI Tutor Q&A response received: {ask_data['answer'][:60]}...")

    # 10. Test Adaptive Quiz (Page G)
    res = client.get(f'/quiz/{student_id}/regression')
    assert res.status_code == 200
    assert b"ADAPTIVE QUIZ" in res.data
    print("[PASS] Adaptive Quiz page rendered.")

    # 11. Test Adaptive Quiz Submission & Difficulty Adaptation
    # First submit a correct answer
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, correct_index FROM quiz_questions WHERE topic_id = 'regression' LIMIT 1")
    q_row = c.fetchone()
    conn.close()

    res = client.post('/api/quiz/submit', json={
        'student_id': student_id,
        'topic_id': 'regression',
        'question_id': q_row['id'],
        'chosen_index': q_row['correct_index'],
        'current_difficulty': 'medium'
    })
    assert res.status_code == 200
    quiz_res = res.get_json()
    assert quiz_res['success'] is True
    assert quiz_res['result']['is_correct'] is True
    print(f"[PASS] Quiz submission evaluated: correct={quiz_res['result']['is_correct']}, new_diff={quiz_res['result']['new_difficulty']}")

    # 12. Test Fetching Next Adaptive Question
    res = client.get(f'/api/quiz/next-question?student_id={student_id}&topic_id=regression&difficulty=hard')
    assert res.status_code == 200
    next_q = res.get_json()
    assert next_q['success'] is True
    assert 'question' in next_q['question']
    print(f"[PASS] Next adaptive question fetched successfully: {next_q['question']['question'][:50]}...")

    # 13. Test Progress Dashboard (Page H)
    res = client.get(f'/dashboard/{student_id}')
    assert res.status_code == 200
    assert b"Learning Analytics & Mastery" in res.data
    assert b"Overall Progress" in res.data
    assert b"topicRadarChart" in res.data
    print("[PASS] Progress Dashboard rendered with live analytics.")

    # 14. Test Hackathon Scenarios
    for s_num in [1, 2, 3]:
        res = client.get(f'/demo/scenario/{s_num}')
        assert res.status_code == 302, f"Scenario {s_num} redirect failed"
        print(f"[PASS] Hackathon demo scenario {s_num} executed successfully.")

    # 15. Test Custom 404 Error Page
    res = client.get('/nonexistent-route-for-testing')
    assert res.status_code == 404
    assert b"Page Not Found" in res.data
    print("[PASS] Custom 404 error handler rendered successfully.")

    print("\n=== ALL 15 PIPELINE TESTS PASSED WITH ZERO ERRORS! ===")

if __name__ == '__main__':
    test_full_pipeline()
