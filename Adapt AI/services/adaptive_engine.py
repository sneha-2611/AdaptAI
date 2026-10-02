import json
from database.db import get_db_connection

def evaluate_diagnostic(student_id, answers):
    """
    answers: dict mapping question_id (int or str) -> chosen_index (int)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, topic_id, topic_name, correct_index FROM diagnostic_questions")
    questions = cursor.fetchall()

    topic_stats = {}
    total_score = 0
    total_questions = len(questions)

    for q in questions:
        q_id = str(q['id'])
        t_id = q['topic_id']
        t_name = q['topic_name']
        correct_idx = q['correct_index']

        if t_id not in topic_stats:
            topic_stats[t_id] = {
                'name': t_name,
                'total': 0,
                'correct': 0
            }

        topic_stats[t_id]['total'] += 1
        chosen = answers.get(q_id)
        if chosen is not None and int(chosen) == correct_idx:
            topic_stats[t_id]['correct'] += 1
            total_score += 1

    percentage = round((total_score / total_questions) * 100, 1) if total_questions > 0 else 0

    # Knowledge level determination
    if percentage >= 80:
        knowledge_level = "Advanced"
    elif percentage >= 50:
        knowledge_level = "Intermediate"
    else:
        knowledge_level = "Beginner"

    # Identify strong and weak topics
    strong_topics = []
    weak_topics = []
    developing_topics = []

    for t_id, stats in topic_stats.items():
        score_pct = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        if score_pct >= 80:
            strong_topics.append(stats['name'])
        elif score_pct < 50:
            weak_topics.append(stats['name'])
        else:
            developing_topics.append(stats['name'])

    # If all or none fall strictly into weak or strong, ensure balanced feedback
    if not strong_topics and not weak_topics:
        developing_topics = [s['name'] for s in topic_stats.values()]

    # Save assessment result
    cursor.execute("""
        INSERT INTO assessment_results 
        (student_id, score, total_questions, percentage, knowledge_level, strong_topics, weak_topics)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id, total_score, total_questions, percentage, knowledge_level,
        json.dumps(strong_topics), json.dumps(weak_topics)
    ))

    # Update student's current level
    cursor.execute("UPDATE students SET current_level = ? WHERE id = ?", (knowledge_level, student_id))

    conn.commit()
    conn.close()

    # Generate personalised learning path based on assessment results
    generate_personalised_roadmap(student_id, knowledge_level, strong_topics, weak_topics)

    return {
        'student_id': student_id,
        'score': total_score,
        'total': total_questions,
        'percentage': percentage,
        'knowledge_level': knowledge_level,
        'strong_topics': strong_topics,
        'weak_topics': weak_topics,
        'developing_topics': developing_topics
    }

def generate_personalised_roadmap(student_id, knowledge_level, strong_topics, weak_topics):
    """
    Constructs a personalised learning path in student_learning_path:
    - Strong topics: mark completed (100%) or high initial progress
    - First weak or developing topic: marked 'recommended' and 'in_progress' with appropriate initial difficulty
    - Prerequisite-bound topics locked until previous are completed
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear any previous path for this student
    cursor.execute("DELETE FROM student_learning_path WHERE student_id = ?", (student_id,))

    cursor.execute("SELECT id, title, order_index, prerequisites FROM topics ORDER BY order_index ASC")
    all_topics = cursor.fetchall()

    recommended_assigned = False

    for idx, topic in enumerate(all_topics):
        t_id = topic['id']
        title = topic['title']
        order_idx = topic['order_index']

        is_strong = title in strong_topics
        is_weak = title in weak_topics

        # Initial difficulty based on profile
        if is_weak:
            diff = "easy"
        elif is_strong:
            diff = "hard"
        else:
            diff = "medium"

        # Determine status and progress
        if is_strong and knowledge_level in ["Intermediate", "Advanced"] and idx < 2:
            # Foundational strong topics can be marked completed as shown in PPT slide 3 mockup!
            status = "completed"
            progress = 100
            is_rec = 0
        elif not recommended_assigned and is_weak:
            # Found first weak topic -> Recommended Next!
            status = "in_progress"
            progress = 25
            is_rec = 1
            recommended_assigned = True
        elif not recommended_assigned:
            # If no weak topic found yet, make this first uncompleted topic Recommended Next
            status = "in_progress"
            progress = 30
            is_rec = 1
            recommended_assigned = True
        else:
            # Subsequent topics: either locked or ready to learn
            if order_idx > 4:
                status = "locked"
                progress = 0
                is_rec = 0
            else:
                status = "in_progress"
                progress = 0
                is_rec = 0

        cursor.execute("""
            INSERT INTO student_learning_path 
            (student_id, topic_id, order_index, status, progress_pct, difficulty, is_recommended)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, t_id, order_idx, status, progress, diff, is_rec))

    # If by chance no topic was marked recommended, pick the first in_progress one
    cursor.execute("SELECT id FROM student_learning_path WHERE student_id = ? AND is_recommended = 1", (student_id,))
    if not cursor.fetchone():
        cursor.execute("""
            UPDATE student_learning_path 
            SET is_recommended = 1, status = 'in_progress' 
            WHERE id = (SELECT id FROM student_learning_path WHERE student_id = ? AND status != 'completed' ORDER BY order_index ASC LIMIT 1)
        """, (student_id,))

    conn.commit()
    conn.close()

def get_student_roadmap(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT slp.*, t.title, t.description, t.category
        FROM student_learning_path slp
        JOIN topics t ON slp.topic_id = t.id
        WHERE slp.student_id = ?
        ORDER BY slp.order_index ASC
    """, (student_id,))
    roadmap = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return roadmap

def record_quiz_submission(student_id, topic_id, question_id, chosen_idx, current_difficulty):
    """
    Evaluates quiz question answer, records attempt, and applies adaptive difficulty adjustment.
    Adaptive Rule:
    - High recent performance (>= 80%) -> increase difficulty (easy->medium, medium->hard)
    - Medium performance (50-79%) -> maintain difficulty
    - Low performance (< 50%) -> decrease difficulty (hard->medium, medium->easy), revision advice
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get question details
    cursor.execute("SELECT correct_index, explanation, difficulty FROM quiz_questions WHERE id = ?", (question_id,))
    q_data = cursor.fetchone()

    if not q_data:
        conn.close()
        return None

    is_correct = 1 if int(chosen_idx) == q_data['correct_index'] else 0
    actual_diff = q_data['difficulty'] or current_difficulty

    # Record attempt
    cursor.execute("""
        INSERT INTO quiz_attempts (student_id, topic_id, question_id, chosen_index, is_correct, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, topic_id, question_id, chosen_idx, is_correct, actual_diff))
    conn.commit()

    # Calculate recent performance for this topic
    cursor.execute("""
        SELECT is_correct FROM quiz_attempts 
        WHERE student_id = ? AND topic_id = ?
        ORDER BY timestamp DESC LIMIT 5
    """, (student_id, topic_id))
    recent_attempts = cursor.fetchall()

    recent_correct = sum(a['is_correct'] for a in recent_attempts)
    recent_total = len(recent_attempts)
    performance_pct = (recent_correct / recent_total) * 100 if recent_total > 0 else 0

    # Determine adaptive difficulty transition
    diff_order = ["easy", "medium", "hard"]
    curr_diff_idx = diff_order.index(current_difficulty) if current_difficulty in diff_order else 1
    new_difficulty = current_difficulty
    adaptation_message = ""

    if performance_pct >= 80:
        if curr_diff_idx < 2:
            new_difficulty = diff_order[curr_diff_idx + 1]
            adaptation_message = f"Superb performance ({int(performance_pct)}%)! Adapting difficulty to '{new_difficulty.title()}' to challenge you."
        else:
            new_difficulty = "hard"
            adaptation_message = f"Mastery demonstrated ({int(performance_pct)}%)! Keeping maximum 'Hard' difficulty challenge."
    elif performance_pct < 50:
        if curr_diff_idx > 0:
            new_difficulty = diff_order[curr_diff_idx - 1]
            adaptation_message = f"Recent accuracy is {int(performance_pct)}%. Adjusting difficulty to '{new_difficulty.title()}' to reinforce core fundamentals."
        else:
            new_difficulty = "easy"
            adaptation_message = f"Focus on basics (accuracy {int(performance_pct)}%). We recommend reviewing key concepts with the AI Tutor."
    else:
        adaptation_message = f"Steady pace ({int(performance_pct)}% accuracy). Maintaining '{current_difficulty.title()}' difficulty."

    # Update topic progress and difficulty
    cursor.execute("""
        SELECT progress_pct, status FROM student_learning_path 
        WHERE student_id = ? AND topic_id = ?
    """, (student_id, topic_id))
    current_path = cursor.fetchone()

    new_progress = 0
    if current_path:
        old_progress = current_path['progress_pct']
        increment = 20 if is_correct else 5
        new_progress = min(100, old_progress + increment)
        new_status = "completed" if new_progress >= 90 else "in_progress"

        cursor.execute("""
            UPDATE student_learning_path 
            SET progress_pct = ?, difficulty = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE student_id = ? AND topic_id = ?
        """, (new_progress, new_difficulty, new_status, student_id, topic_id))

        # If completed, unlock next topic and make it recommended
        if new_status == "completed":
            cursor.execute("""
                SELECT id, topic_id FROM student_learning_path
                WHERE student_id = ? AND status IN ('locked', 'in_progress') AND topic_id != ?
                ORDER BY order_index ASC LIMIT 1
            """, (student_id, topic_id))
            next_topic = cursor.fetchone()
            if next_topic:
                # Clear previous recommendations
                cursor.execute("UPDATE student_learning_path SET is_recommended = 0 WHERE student_id = ?", (student_id,))
                cursor.execute("""
                    UPDATE student_learning_path 
                    SET status = 'in_progress', is_recommended = 1 
                    WHERE id = ?
                """, (next_topic['id'],))

    conn.commit()
    conn.close()

    return {
        'is_correct': bool(is_correct),
        'correct_index': q_data['correct_index'],
        'explanation': q_data['explanation'],
        'new_difficulty': new_difficulty,
        'adaptation_message': adaptation_message,
        'performance_pct': round(performance_pct, 1),
        'new_progress': new_progress
    }

def get_dashboard_data(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Student details
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return None

    student_data = dict(student)

    # Assessment Result
    cursor.execute("""
        SELECT * FROM assessment_results 
        WHERE student_id = ? 
        ORDER BY completed_at DESC LIMIT 1
    """, (student_id,))
    assessment_row = cursor.fetchone()
    assessment = dict(assessment_row) if assessment_row else None
    if assessment:
        assessment['strong_topics'] = json.loads(assessment['strong_topics'])
        assessment['weak_topics'] = json.loads(assessment['weak_topics'])

    # Learning Path / Topics
    cursor.execute("""
        SELECT slp.*, t.title, t.category 
        FROM student_learning_path slp
        JOIN topics t ON slp.topic_id = t.id
        WHERE slp.student_id = ?
        ORDER BY slp.order_index ASC
    """, (student_id,))
    topics_progress = [dict(r) for r in cursor.fetchall()]

    # Overall progress percentage (weighted/averaged across all topics)
    if topics_progress:
        overall_progress = round(sum(t['progress_pct'] for t in topics_progress) / len(topics_progress))
    else:
        overall_progress = 0

    # Recommended next topic
    cursor.execute("""
        SELECT slp.*, t.title, t.description 
        FROM student_learning_path slp
        JOIN topics t ON slp.topic_id = t.id
        WHERE slp.student_id = ? AND slp.is_recommended = 1
        LIMIT 1
    """, (student_id,))
    rec_row = cursor.fetchone()
    recommended_topic = dict(rec_row) if rec_row else (topics_progress[0] if topics_progress else None)

    # Quiz statistics
    cursor.execute("""
        SELECT COUNT(*) as total_attempts, 
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts
        FROM quiz_attempts
        WHERE student_id = ?
    """, (student_id,))
    quiz_stats_row = cursor.fetchone()
    total_q = quiz_stats_row['total_attempts'] or 0
    correct_q = quiz_stats_row['correct_attempts'] or 0
    quiz_accuracy = round((correct_q / total_q) * 100) if total_q > 0 else 0

    # Recent quiz activity
    cursor.execute("""
        SELECT qa.*, t.title as topic_title
        FROM quiz_attempts qa
        JOIN topics t ON qa.topic_id = t.id
        WHERE qa.student_id = ?
        ORDER BY qa.timestamp DESC LIMIT 6
    """, (student_id,))
    recent_activity = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        'student': student_data,
        'assessment': assessment,
        'topics_progress': topics_progress,
        'overall_progress': overall_progress,
        'recommended_topic': recommended_topic,
        'total_questions_attempted': total_q,
        'correct_questions': correct_q,
        'quiz_accuracy': quiz_accuracy,
        'recent_activity': recent_activity
    }
