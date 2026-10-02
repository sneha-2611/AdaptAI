# AdaptAI – Personalised AI Tutor for Learning AI
> **BFWAI/HACK 26 · AI Build Challenge 2026**  
> **Problem Statement: PS-03 · Personalised AI Tutor for Learning AI**  
> **Team:** Coders (Sneha J)

---

## 1. What is AdaptAI?

**AdaptAI** is an AI-powered adaptive learning platform engineered specifically for students learning Artificial Intelligence and Machine Learning.

Unlike generic conversational chatbots that simply generate uniform answers for every prompt, **AdaptAI acts as a personalized pedagogical system**. It assesses a student's existing knowledge, detects specific gaps and strengths, generates a tailored learning roadmap, teaches concepts calibrated to the learner's tier, and dynamically adjusts quiz difficulty in real time based on learner performance.

### Core Adaptive Flow:
$$\text{Assess} \longrightarrow \text{Analyse} \longrightarrow \text{Personalise} \longrightarrow \text{Learn} \longrightarrow \text{Practice} \longrightarrow \text{Adapt} \longrightarrow \text{Track}$$

---

## 2. The Problem It Solves

Students entering the AI/ML landscape face critical bottlenecks:
* **One-Size-Fits-All Material:** Generic textbooks and chatbots fail to calibrate to whether a learner is a beginner needing analogies or an advanced student seeking algorithmic rigor.
* **Hidden Knowledge Gaps:** Learners often don't know *which* concept is holding them back (e.g., struggling with neural networks because of weak regression foundations).
* **Static Quizzes:** Traditional quizzes do not adjust difficulty based on performance, leading to either boredom or frustration.
* **Lack of Clear Next Steps:** Students finish a tutorial with no intelligent recommendation on what to tackle next.

---

## 3. Key Features

| Feature | Description |
| :--- | :--- |
| **01 Knowledge Assessment** | Evaluates learner understanding across core AI/ML domains via a 10-question diagnostic quiz. |
| **02 Personalised Roadmap** | Dynamically constructs an ordered learning path based on identified strengths and weaknesses. |
| **03 Level-Adapted AI Tutor** | Generates lessons and answers ad-hoc questions tailored to the learner's tier (Beginner / Intermediate / Advanced). |
| **04 Adaptive Quiz Engine** | Real-time question difficulty transitions: $\ge 80\%$ performance increases difficulty; $< 50\%$ lowers difficulty and provides revision tips. |
| **05 Stored Progress Dashboard** | Real-time analytics, Chart.js proficiency radar, topic progress bars, and prioritized next-topic recommendations backed by SQLite. |
| **06 Zero-Crash Demo Mode** | Runs completely offline with curated knowledge logic when no LLM API key is provided, or connects to live LLMs seamlessly. |

---

## 4. Technology Stack

* **Frontend:** HTML5, Vanilla CSS3 (Custom Design System matching BFWAI/HACK 26 Idea Deck), Vanilla JavaScript, Chart.js.
* **Backend:** Python 3.13+, Flask 3.1.
* **Database:** SQLite3 (Persistent local storage, no external server setup required).
* **AI Engine:** Structured LLM API integration (OpenAI / OpenRouter / Gemini compatible) + Built-in Adaptive Knowledge Fallback Engine.

---

## 5. Project Architecture & File Organization

```
Adapt AI/
│
├── app.py                      # Main Flask application, page routes & API endpoints
├── requirements.txt            # Python dependencies (flask, python-dotenv, requests)
├── .env.example                # Environment variable template
├── .env                        # Local environment configuration
├── README.md                   # Complete documentation & run guide
│
├── database/
│   ├── __init__.py
│   └── db.py                   # SQLite schema initialization, connections, and seed data
│
├── services/
│   ├── __init__.py
│   ├── adaptive_engine.py      # Core deterministic personalisation & difficulty logic
│   └── ai_service.py           # Level-aware AI tutoring, Q&A reasoning, and question curation
│
├── static/
│   └── css/
│       └── style.css           # Modern dark UI design system matching the presentation
│
└── templates/
    ├── base.html               # Base layout, navbar, active profile pill, and footer
    ├── index.html              # Landing Page (Page A)
    ├── setup.html              # Student Setup (Page B)
    ├── assessment.html         # Diagnostic Assessment (Page C)
    ├── results.html            # Assessment Results & Learning Profile (Page D)
    ├── learning_path.html      # Personalised Learning Path Roadmap (Page E)
    ├── tutor.html              # AI Tutor / Learning Page with Q&A (Page F)
    ├── quiz.html               # Adaptive Quiz with Real-time Difficulty (Page G)
    └── dashboard.html          # Progress Dashboard with Chart.js (Page H)
```

---

## 6. Where the Important Logic Lives

1. **Personalisation & Adaptive Engine:** [`services/adaptive_engine.py`](file:///c:/Users/Hp/OneDrive/Desktop/Adapt%20AI/services/adaptive_engine.py)
   * `evaluate_diagnostic()`: Scores diagnostic questions, categorizes topics as **Strong** ($\ge 80\%$) or **Weak / Needs Improvement** ($< 50\%$), and sets initial knowledge tier.
   * `generate_personalised_roadmap()`: Dynamically configures the curriculum path, granting completion credits to mastered topics, prioritizing weak topics with the **"Recommended Next"** flag, and locking advanced modules whose prerequisites are not yet met.
   * `record_quiz_submission()`: Evaluates answers in real time, computes rolling accuracy, and triggers adaptive difficulty transitions (**Easy $\leftrightarrow$ Medium $\leftrightarrow$ Hard**).
   * `get_dashboard_data()`: Pulls live stats from SQLite to drive progress bars and analytics.

2. **AI Tutor & Lesson Adaptation:** [`services/ai_service.py`](file:///c:/Users/Hp/OneDrive/Desktop/Adapt%20AI/services/ai_service.py)
   * `generate_lesson_content()`: Crafts lesson overviews, real-world analogies, and takeaways suited strictly to the learner's tier (Beginner vs Intermediate vs Advanced).
   * `ask_ai_tutor()`: Answers student questions (e.g., *"Explain overfitting in simple words"*) in context of the topic and experience level.
   * `get_adaptive_quiz_question()`: Supplies questions matching the student's active difficulty.

3. **Application Routing & State Management:** [`app.py`](file:///c:/Users/Hp/OneDrive/Desktop/Adapt%20AI/app.py)
   * Manages student sessions, diagnostic submissions, quiz scoring endpoints, and evaluator test scenario shortcuts.

---

## 7. How to Add Your LLM API Key

AdaptAI works **out-of-the-box in Demo/Mock Mode without any API key**.

If you wish to use a live LLM (OpenAI, OpenRouter, or Gemini):

1. Open the [`.env`](file:///c:/Users/Hp/OneDrive/Desktop/Adapt%20AI/.env) file located in the root directory:
   ```ini
   LLM_API_KEY=your_actual_api_key_here
   LLM_MODEL=gpt-4o-mini
   LLM_BASE_URL=https://api.openai.com/v1
   ```
2. Save the file and restart the Flask app. AdaptAI will automatically switch to **"Live LLM API"** mode. If the key is invalid or times out, it gracefully falls back without crashing.

---

## 8. Installation & How to Run

### Step 1: Open PowerShell or Terminal in the project folder
```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Adapt AI"
```

### Step 2: Install dependencies
```powershell
py -m pip install -r requirements.txt
```

### Step 3: Run the Flask application
```powershell
py app.py
```

### Step 4: Open in your browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 9. How to Test the 3 Hackathon Demo Scenarios

You can test the entire learner journey organically or click the **Hackathon Evaluator Quick-Test** buttons on the landing page:

* **Scenario 1: High Assessment Score (Advanced Learner)**
  * Go to `http://127.0.0.1:5000/demo/scenario/1`
  * Pre-loads an advanced student with 90% diagnostic score.
  * Verified: Foundational topics are auto-completed, difficulty is set to **Hard**, and advanced topics are recommended.
* **Scenario 2: Low Assessment Score (Beginner Learner)**
  * Go to `http://127.0.0.1:5000/demo/scenario/2`
  * Pre-loads a beginner student with 30% diagnostic score.
  * Verified: Foundation topics prioritized, difficulty set to **Easy**, and targeted revision prompts enabled.
* **Scenario 3: Developing Learner with Adaptive Promotion**
  * Go to `http://127.0.0.1:5000/demo/scenario/3`
  * Start an adaptive quiz on Regression or Classification.
  * Answer questions correctly $\to$ Observe live transition to **Hard** difficulty, mastery increase, and next module unlock.
