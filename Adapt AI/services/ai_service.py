import os
import json
import requests
from dotenv import load_dotenv
from database.db import get_db_connection

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()

# Rich fallback curriculum curated for each topic and learner level
CURATED_LESSONS = {
    "ai-fundamentals": {
        "title": "AI Fundamentals",
        "Beginner": {
            "explanation": "Artificial Intelligence is about building computer systems that can perform tasks that usually require human intelligence—like recognizing speech, identifying objects in photos, or making decisions. Unlike traditional computer software where a programmer writes down every single rule step-by-step, AI systems learn patterns directly from examples.",
            "example": "Think of spam filtering in your email. Instead of a human programmer writing a rule for every suspicious email in existence, the AI looks at thousands of emails marked 'spam' and 'not spam', discovering common patterns like urgent money transfer requests or suspicious sender addresses.",
            "key_points": [
                "Artificial Intelligence simulates human reasoning, learning, and problem solving.",
                "Narrow AI excels at a single task (like facial recognition or chess), whereas General AI (AGI) remains theoretical.",
                "AI systems rely on data, patterns, and optimization rather than static hardcoded logic."
            ]
        },
        "Intermediate": {
            "explanation": "At its architectural core, Artificial Intelligence has shifted from symbolic expert systems (rule-based inference engines and search trees) to statistical learning paradigms. In modern AI, an agent perceives its environment via sensors/inputs, processes internal state representations, and takes actions that maximize an objective utility function.",
            "example": "A pathfinding navigation agent (like Google Maps or A* search) models real-world road networks as weighted graphs, continuously calculating heuristic cost estimates to determine optimal transit paths in dynamic conditions.",
            "key_points": [
                "Distinguishes between symbolic heuristic reasoning (1960-1980s) and statistical machine learning (modern era).",
                "Rational Agents optimize an explicit utility or reward function subject to environmental constraints.",
                "Turing completeness vs statistical generalization: systems trade rigid deterministic guarantees for flexible probabilistic inference."
            ]
        },
        "Advanced": {
            "explanation": "Contemporary Artificial Intelligence is grounded in statistical decision theory, high-dimensional manifold learning, and probabilistic graphical models. Intelligence is formalized as minimizing expected risk over unknown data distributions via empirical risk minimization with inductive biases.",
            "example": "Reinforcement Learning agents in Markov Decision Processes (MDPs) balance exploration vs exploitation using Bellman optimality equations and temporal difference learning under non-stationary state transitions.",
            "key_points": [
                "Empirical Risk Minimization (ERM) subject to VC-dimension and Rademacher complexity bounds.",
                "Markov Decision Processes, state-space representations, and Bellman convergence guarantees.",
                "Information-theoretic limits of heuristic search, Bayesian updating, and representation learning."
            ]
        }
    },
    "ml-basics": {
        "title": "Machine Learning Basics",
        "Beginner": {
            "explanation": "Machine Learning is a branch of AI where computers learn from experience. Just like a child learns to identify dogs by seeing different dogs over time, an ML model adjusts its internal parameters by looking at thousands of examples until it can recognize patterns on its own.",
            "example": "Imagine teaching someone to bake cookies. If they add too much sugar, the cookies are too sweet. Next time, they reduce the sugar. Machine learning does this with math: it makes a guess, measures its mistake (called 'loss'), and tweaks its recipe until the cookies turn out just right.",
            "key_points": [
                "Machine Learning uses data and algorithms to imitate the way humans learn.",
                "Data is split into Training (to learn) and Testing (to verify) sets to prevent memorization.",
                "Overfitting happens when a model memorizes data rather than understanding underlying patterns."
            ]
        },
        "Intermediate": {
            "explanation": "Machine Learning algorithms optimize parameterized hypothesis functions f(x; θ) to map inputs x to outputs y. Training involves defining an objective loss function L(y, f(x; θ)) and updating parameters θ iteratively using optimization techniques such as Stochastic Gradient Descent (SGD).",
            "example": "In house price estimation, the model learns a vector of weights corresponding to square footage, bedrooms, and zip codes, minimizing the Mean Squared Error across a validation partition.",
            "key_points": [
                "Hyperparameter tuning vs model parameter optimization during backpropagation/training.",
                "The Bias-Variance tradeoff: Underfitting denotes high bias, while Overfitting denotes high variance.",
                "Cross-validation (k-fold) provides an unbiased estimate of generalization error."
            ]
        },
        "Advanced": {
            "explanation": "Machine learning formalizes generalization bounds through PAC (Probably Approximately Correct) learning theory. We minimize empirical risk while constraining model capacity via regularization (Tikhonov L2, Lasso L1) to navigate the double descent phenomenon in overparameterized regimes.",
            "example": "Spectral analysis of the Hessian matrix in loss landscapes demonstrates how stochastic noise in mini-batch SGD acts as implicit regularization, guiding optimization trajectories toward flatter minima.",
            "key_points": [
                "PAC learning guarantees, Rademacher complexity, and structural risk minimization.",
                "Loss surface topology, saddle point escapes, and convex vs non-convex optimization dynamics.",
                "Implicit regularization of gradient descent algorithms in high-dimensional parameter spaces."
            ]
        }
    },
    "supervised-learning": {
        "title": "Supervised Learning",
        "Beginner": {
            "explanation": "Supervised Learning is like learning with a teacher or an answer key. You feed the computer lots of questions along with their correct answers. After seeing enough paired examples, the model learns to answer new questions it hasn't seen before.",
            "example": "Predicting whether a student will pass an exam based on their study hours, attendance, and previous test scores. Because we have historical student records with both the hours studied AND whether they passed, the computer has direct supervision.",
            "key_points": [
                "Requires labeled datasets with inputs (features) and targets (labels).",
                "Divided into two main categories: Regression (numbers) and Classification (categories).",
                "Evaluated using clear ground truth metrics like Accuracy, Precision, and Recall."
            ]
        },
        "Intermediate": {
            "explanation": "Supervised learning models estimate the conditional probability distribution P(Y|X) or learn a direct mapping function f: X -> Y given training pairs D = {(x_i, y_i)}. Depending on whether the label space Y is discrete or continuous, the model is formulated as classification or regression.",
            "example": "Credit default scoring: Given financial histories (income, debt-to-income ratio, credit inquiries), a logistic regression or gradient-boosted decision tree outputs a calibrated probability of loan default.",
            "key_points": [
                "Discriminative models (e.g. Logistic Regression, SVM) vs Generative models (e.g. Naive Bayes).",
                "Loss formulations: Cross-Entropy for categorical outcomes vs MSE/MAE for continuous outcomes.",
                "Mitigating class imbalance using SMOTE, focal loss, and precision-recall trade-offs."
            ]
        },
        "Advanced": {
            "explanation": "In supervised learning, we analyze consistency, asymptotic normality of estimators, and uniform convergence of empirical processes. Maximum Likelihood Estimation (MLE) connects loss functions (e.g., negative log-likelihood) directly to assumed conditional error distributions (Gaussian for MSE, Bernoulli for Binary Cross-Entropy).",
            "example": "Kernel Support Vector Machines project input vectors into infinite-dimensional reproducing kernel Hilbert spaces (RKHS) via Mercer kernels, solving convex dual quadratic programs with Karush-Kuhn-Tucker (KKT) conditions.",
            "key_points": [
                "Maximum Likelihood Estimation and Maximum A Posteriori (MAP) equivalence to regularized loss.",
                "Reproducing Kernel Hilbert Spaces (RKHS) and dual optimization under KKT constraints.",
                "Generalization error bounds under covariate shift and out-of-distribution transfer."
            ]
        }
    },
    "unsupervised-learning": {
        "title": "Unsupervised Learning",
        "Beginner": {
            "explanation": "Unsupervised learning is like exploring an unfamiliar city without a map or a tour guide. The computer is given raw data with NO labels or right answers, and its job is to discover natural groupings, hidden patterns, or unusual outliers on its own.",
            "example": "A streaming platform like Netflix grouping millions of viewers into 'movie taste communities' without anyone explicitly labeling viewers. People who watch sci-fi thrillers naturally cluster together based on shared viewing history.",
            "key_points": [
                "Works on unlabeled data to find hidden structure.",
                "Common tasks: Clustering (grouping similar items) and Dimensionality Reduction (simplifying data).",
                "Key algorithm: K-Means Clustering partitions data into K groups based on distance."
            ]
        },
        "Intermediate": {
            "explanation": "Unsupervised algorithms model the marginal distribution P(X) to uncover latent variables or low-dimensional manifolds. Methods include centroid-based clustering (K-Means), density-based clustering (DBSCAN), hierarchical clustering, and linear projection techniques like Principal Component Analysis (PCA).",
            "example": "Customer segmentation in e-commerce: Computing customer RFM (Recency, Frequency, Monetary) vectors, standardizing distributions, and applying K-Means with silhouette score validation to identify high-value consumer cohorts.",
            "key_points": [
                "K-Means objective: Minimizing within-cluster sum of squares (inertia) using Lloyd's algorithm.",
                "DBSCAN detects arbitrary cluster geometries and labels sparse points as noise outliers.",
                "PCA decomposes the sample covariance matrix via Singular Value Decomposition (SVD)."
            ]
        },
        "Advanced": {
            "explanation": "Unsupervised learning extends to non-linear manifold estimation (t-SNE, UMAP), probabilistic latent variable models (Expectation-Maximization for Gaussian Mixture Models), and generative density estimation (Variational Autoencoders and Normalizing Flows).",
            "example": "Gaussian Mixture Models (GMM) formulate clustering as soft probabilistic assignments via Expectation-Maximization, maximizing the log-likelihood of mixture components under Jensen's inequality.",
            "key_points": [
                "Expectation-Maximization (EM) algorithm guarantees monotonic convergence of marginal likelihood lower bounds.",
                "Spectral clustering via graph Laplacians and Rayleigh quotient optimization.",
                "Topological data analysis and Riemannian manifold approximations via UMAP simplicial sets."
            ]
        }
    },
    "regression": {
        "title": "Regression",
        "Beginner": {
            "explanation": "Regression is an AI technique used whenever you want to predict a continuous number—such as temperature, price, height, or sales volume. A simple linear regression tries to draw the best straight line through scatter-plot data points so it can forecast future numbers.",
            "example": "Predicting the price of a house. If a 1,000 sq ft house is $200k and a 2,000 sq ft house is $350k, a regression line connects the data to estimate what a 1,500 sq ft house should cost.",
            "key_points": [
                "Regression predicts continuous numerical values, not categories.",
                "The equation y = mx + b determines the best-fitting trendline.",
                "Error is measured by how far the line is from actual data points (e.g. Mean Squared Error)."
            ]
        },
        "Intermediate": {
            "explanation": "Multiple Linear Regression models the relationship y = Xβ + ε, estimating the parameter vector β to minimize the sum of squared residuals. Optimization is solved analytically via the Normal Equation β = (X^T X)^(-1) X^T y or iteratively using Gradient Descent.",
            "example": "Predicting automobile fuel efficiency (miles per gallon) based on engine horsepower, vehicle weight, and aerodynamic drag coefficient using Polynomial Regression with L2 Ridge penalty.",
            "key_points": [
                "Ordinary Least Squares (OLS) assumptions: linearity, homoscedasticity, no multicollinearity, and normal residuals.",
                "Metrics: Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and R² (explained variance).",
                "Regularization: Ridge (L2 penalty) prevents coefficient explosion; Lasso (L1 penalty) enforces feature sparsity."
            ]
        },
        "Advanced": {
            "explanation": "Regression analysis bridges Gauss-Markov theorem conditions (BLUE: Best Linear Unbiased Estimator) with Generalized Linear Models (GLMs) that handle exponential dispersion families via link functions. Under multicollinearity, condition numbers of X^T X escalate, requiring singular value decomposition or elastic net penalization.",
            "example": "Quantile regression minimizes asymmetric tilted absolute loss, estimating conditional median or 95th percentile risk thresholds without assuming normal error distributions.",
            "key_points": [
                "Gauss-Markov theorem and asymptotic properties of maximum likelihood estimators.",
                "Elastic Net regularization combining L1 and L2 penalties under correlated covariate regimes.",
                "Heteroscedasticity-robust covariance matrix estimation (White-Huber sandwich estimators)."
            ]
        }
    },
    "classification": {
        "title": "Classification",
        "Beginner": {
            "explanation": "Classification is all about sorting things into categories or buckets. Is an email 'spam' or 'inbox'? Is an X-ray image 'healthy' or 'pneumonia'? The output is always a label or class, rather than a continuous number.",
            "example": "Sorting fruit at a grocery store checkout scanner: The camera looks at color, shape, and size, classifying whether the object is an Apple, an Orange, or a Banana.",
            "key_points": [
                "Classification predicts categorical labels (binary or multi-class).",
                "Logistic Regression uses an S-shaped Sigmoid curve to output a probability between 0% and 100%.",
                "Decision trees ask a series of yes/no questions to reach a classification."
            ]
        },
        "Intermediate": {
            "explanation": "Classification models partition feature space using decision boundaries. Logistic Regression maps linear combinations of features through the Sigmoid activation function σ(z) = 1 / (1 + e^(-z)), predicting class probabilities optimized via Binary Cross-Entropy loss.",
            "example": "Credit card fraud detection: Evaluating transactions using Random Forest and XGBoost classifiers, tuning threshold cutoffs to balance Precision (avoiding false alarms) against Recall (catching actual fraud).",
            "key_points": [
                "Evaluation matrices: Confusion Matrix, Precision, Recall, F1-Score, and ROC-AUC.",
                "Decision Trees split nodes based on Gini Impurity or Information Gain (Entropy reduction).",
                "Ensemble methods: Bagging (Random Forest) reduces variance; Boosting (XGBoost, LightGBM) reduces bias."
            ]
        },
        "Advanced": {
            "explanation": "Advanced classification formulates multi-class probabilistic boundaries via Softmax logit normalizations, optimizing Kullback-Leibler divergence. Non-parametric classification theorems establish that 1-Nearest Neighbor asymptotic risk is bounded by twice the Bayes error rate.",
            "example": "Support Vector Machines with non-linear radial basis function (RBF) kernels optimizing the dual soft-margin Lagrangian with slack variables under Mercer's condition.",
            "key_points": [
                "Bayes optimal classifier and theoretical lower bounds on classification error.",
                "Margin theory, soft-margin duality, and support vector sparsity.",
                "Calibration techniques (Platt scaling and isotonic regression) for posterior probability estimates."
            ]
        }
    },
    "deep-learning-basics": {
        "title": "Deep Learning Basics",
        "Beginner": {
            "explanation": "Deep Learning is a subset of machine learning inspired by the structure of the human brain. It uses 'Artificial Neural Networks' with multiple layers (hence 'deep'). By stacking these layers, the network can learn complicated concepts like understanding human speech or driving autonomous cars.",
            "example": "Recognizing a handwritten digit '8': The first layer detects simple edges and lines. The next layer combines lines to spot loops and curves. The final layer combines the loops to recognize the number 8.",
            "key_points": [
                "Uses multi-layered Artificial Neural Networks to learn representations from raw data.",
                "Neurons take inputs, multiply them by weights, add a bias, and pass through an activation function.",
                "Trained by measuring errors and adjusting millions of weights backwards (Backpropagation)."
            ]
        },
        "Intermediate": {
            "explanation": "Deep Neural Networks consist of an input layer, hidden representations, and output layers. Information passes forward via affine matrix transformations followed by non-linear activations (ReLU, GeLU). Learning proceeds by computing loss gradients via the chain rule (Backpropagation) and updating weights via Adam or SGD.",
            "example": "A Multi-Layer Perceptron (MLP) trained on MNIST image vectors (784 dimensions) using batch normalization, dropout (p=0.2), and cross-entropy loss, achieving 98%+ test accuracy.",
            "key_points": [
                "Non-linear activation functions (ReLU, LeakyReLU) prevent layer collapse and mitigate vanishing gradients.",
                "Loss backpropagation applies the differential chain rule backwards from loss to input weights.",
                "Modern optimizers (Adam, RMSProp) use adaptive per-parameter learning rates and momentum."
            ]
        },
        "Advanced": {
            "explanation": "Deep learning architectures represent parameterized compositions of function spaces f(x) = f_L(... f_2(f_1(x; W_1); W_2)...). The Universal Approximation Theorem proves that feedforward networks with non-linear activations can approximate any continuous function on compact subsets of R^n.",
            "example": "Residual connections (ResNets) create identity shortcuts that eliminate gradient vanishing in networks with hundreds of layers, facilitating smooth optimization landscapes and stable eigenvalue spectra.",
            "key_points": [
                "Universal Approximation Theorem, capacity limits, and width vs depth trade-offs.",
                "Vanishing and exploding gradients: Hessian condition numbers and dynamical isometry.",
                "Attention mechanisms, inductive biases, and self-supervised pre-training paradigms."
            ]
        }
    }
}

def generate_lesson_content(topic_id, student_level="Beginner", weak_topics=None):
    """
    Generates level-appropriate explanation, example, and key takeaways.
    If LLM API is configured, enriches with dynamic AI. Otherwise, seamlessly serves curated knowledge.
    """
    if weak_topics is None:
        weak_topics = []

    is_weak = False
    curated = CURATED_LESSONS.get(topic_id)
    if not curated:
        # Fallback to generic AI Fundamentals
        topic_id = "ai-fundamentals"
        curated = CURATED_LESSONS["ai-fundamentals"]

    level_key = student_level if student_level in curated else "Beginner"
    lesson_data = curated[level_key]
    topic_title = curated["title"]

    # Check if student was weak in this topic during diagnostic
    for w in weak_topics:
        if topic_title.lower() in w.lower() or w.lower() in topic_title.lower():
            is_weak = True
            break

    # If LLM API Key is configured, attempt live call
    if LLM_API_KEY:
        try:
            prompt = f"""
            You are AdaptAI, an expert AI tutor. 
            Topic: {topic_title}
            Learner Level: {student_level}
            Student Needs Reinforcement (Weak Area): {'Yes, explain extra clearly with helpful analogies' if is_weak else 'No, normal progression'}

            Generate a concise, highly educational lesson in strict JSON format:
            {{
                "explanation": "Clear explanation suited to {student_level} level",
                "example": "Relatable real-world practical example",
                "key_points": ["Point 1", "Point 2", "Point 3"]
            }}
            """
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are AdaptAI, an adaptive AI tutor. Always respond in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4
            }
            res = requests.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                data = res.json()
                content = data['choices'][0]['message']['content'].strip()
                # Parse JSON
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                parsed = json.loads(content)
                return {
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "difficulty_level": student_level,
                    "is_weak_revision": is_weak,
                    "explanation": parsed.get("explanation", lesson_data["explanation"]),
                    "example": parsed.get("example", lesson_data["example"]),
                    "key_points": parsed.get("key_points", lesson_data["key_points"]),
                    "source": "AdaptAI Live LLM"
                }
        except Exception:
            pass  # Fall through to guaranteed reliable fallback

    return {
        "topic_id": topic_id,
        "topic_title": topic_title,
        "difficulty_level": student_level,
        "is_weak_revision": is_weak,
        "explanation": lesson_data["explanation"],
        "example": lesson_data["example"],
        "key_points": lesson_data["key_points"],
        "source": "AdaptAI Adaptive Knowledge Engine (Demo Mode)"
    }

def ask_ai_tutor(student_id, topic_id, question_text, student_name="Student", student_level="Beginner"):
    """
    Answers a student's question in context of the topic and student level.
    Stores question & answer in database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get topic title
    cursor.execute("SELECT title FROM topics WHERE id = ?", (topic_id,))
    t_row = cursor.fetchone()
    topic_title = t_row['title'] if t_row else topic_id

    # Check for live LLM
    answer = None
    if LLM_API_KEY:
        try:
            prompt = f"""
            You are AdaptAI Tutor teaching '{topic_title}' to {student_name} whose level is {student_level}.
            The student asks: "{question_text}"

            Respond in a friendly, encouraging, and educational way.
            Adapt your depth, analogies, and vocabulary strictly to a {student_level} learner.
            Keep your answer focused, clear, and around 3-4 sentences.
            """
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": f"You are AdaptAI, a personalized AI tutor teaching {topic_title} at {student_level} level."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
            res = requests.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                answer = res.json()['choices'][0]['message']['content'].strip()
        except Exception:
            answer = None

    # High-quality fallback answers for common AI/ML questions
    if not answer:
        q_lower = question_text.lower()
        if "overfit" in q_lower or "overfitting" in q_lower:
            if student_level == "Beginner":
                answer = "Overfitting is like memorizing every single practice exam question word-for-word instead of learning the concepts. The student gets 100% on the practice test, but fails the real exam when questions are worded slightly differently!"
            else:
                answer = "Overfitting occurs when a model captures random noise and idiosyncrasies of the training distribution rather than the underlying data generating function. This leads to near-zero training error but high generalization error on unseen test data. You can mitigate it using regularization, dropout, and cross-validation."
        elif "underfit" in q_lower or "underfitting" in q_lower:
            answer = "Underfitting happens when your model is too simple to capture the relationship in the data—like trying to draw a flat line through a curved rollercoaster. The model performs poorly on both training and test data because it lacks expressive capacity."
        elif "gradient descent" in q_lower:
            answer = f"Imagine you are blindfolded on a foggy mountain and want to find the lowest valley. Gradient Descent feels the slope beneath your feet and takes a step in the steepest downward direction. At {student_level} level, remember that the 'learning rate' controls how big each step is: too big and you overshoot, too small and you take forever!"
        elif "difference" in q_lower and ("supervised" in q_lower or "unsupervised" in q_lower):
            answer = "The key difference is labels! Supervised learning uses input data paired with correct target answers (e.g. photos of cats labeled 'cat'). Unsupervised learning receives only raw data with zero labels, having to discover natural clusters and patterns on its own."
        elif "sigmoid" in q_lower:
            answer = "The Sigmoid function squashes any real number into a probability between 0 and 1. It looks like an 'S' curve, which makes it perfect for binary classification problems where you want to know the probability of an outcome being True or False."
        else:
            answer = f"Great question regarding {topic_title}! At the {student_level} level, always anchor your thinking back to the core concept: we want an algorithm that learns generalizable patterns from sample data rather than relying on brittle manual rules. Feel free to test your understanding in the practice quiz!"

    # Save to tutor_messages table
    cursor.execute("""
        INSERT INTO tutor_messages (student_id, topic_id, role, content)
        VALUES (?, ?, 'user', ?)
    """, (student_id, topic_id, question_text))
    cursor.execute("""
        INSERT INTO tutor_messages (student_id, topic_id, role, content)
        VALUES (?, ?, 'assistant', ?)
    """, (student_id, topic_id, answer))
    conn.commit()
    conn.close()

    return answer

def get_tutor_history(student_id, topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, timestamp 
        FROM tutor_messages 
        WHERE student_id = ? AND topic_id = ? 
        ORDER BY timestamp ASC
    """, (student_id, topic_id))
    history = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return history

def get_adaptive_quiz_question(student_id, topic_id, difficulty="medium", exclude_ids=None):
    """
    Selects or generates a question matching the target adaptive difficulty level for the topic.
    """
    if exclude_ids is None:
        exclude_ids = []

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query existing questions matching topic and difficulty
    placeholders = ','.join('?' for _ in exclude_ids) if exclude_ids else '0'
    query = f"""
        SELECT * FROM quiz_questions 
        WHERE topic_id = ? AND difficulty = ? AND id NOT IN ({placeholders})
        ORDER BY RANDOM() LIMIT 1
    """
    params = [topic_id, difficulty] + (exclude_ids if exclude_ids else [])
    cursor.execute(query, params)
    q_row = cursor.fetchone()

    # If no question in that specific difficulty, fallback to any available for topic
    if not q_row:
        query_any = f"""
            SELECT * FROM quiz_questions 
            WHERE topic_id = ? AND id NOT IN ({placeholders})
            ORDER BY RANDOM() LIMIT 1
        """
        cursor.execute(query_any, [topic_id] + (exclude_ids if exclude_ids else []))
        q_row = cursor.fetchone()

    conn.close()

    if q_row:
        q_dict = dict(q_row)
        q_dict['options'] = json.loads(q_dict['options'])
        return q_dict

    # Dynamic fallback question if all exhausted
    return {
        "id": 9999,
        "topic_id": topic_id,
        "question": f"In {topic_id.replace('-', ' ').title()}, what is the primary objective of model evaluation?",
        "options": [
            "To guarantee that training accuracy is 100%",
            "To measure how reliably the trained model generalizes to new unseen data",
            "To speed up the computer's CPU clock frequency",
            "To eliminate all mathematical formulas from the code"
        ],
        "correct_index": 1,
        "difficulty": difficulty,
        "explanation": "Model evaluation objectively verifies that the algorithm learned genuine patterns that apply to new data, rather than merely memorizing training examples."
    }
