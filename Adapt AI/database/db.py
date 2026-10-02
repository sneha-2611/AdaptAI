import os
import sqlite3
import json
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def get_db_path():
    """Handle cloud serverless environments like Vercel with read-only root filesystems."""
    if os.environ.get('VERCEL'):
        tmp_path = '/tmp/adaptai.db'
        orig_path = os.path.join(BASE_DIR, 'adaptai.db')
        if not os.path.exists(tmp_path) and os.path.exists(orig_path):
            try:
                shutil.copyfile(orig_path, tmp_path)
            except Exception:
                pass
        return tmp_path
    return os.path.join(BASE_DIR, 'adaptai.db')

DB_PATH = get_db_path()

def get_db_connection():
    conn = sqlite3.connect(get_db_path(), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        initial_level TEXT NOT NULL,
        target_topic TEXT DEFAULT 'AI Fundamentals',
        current_level TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS topics (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        order_index INTEGER NOT NULL,
        description TEXT NOT NULL,
        prerequisites TEXT DEFAULT '[]'
    );

    CREATE TABLE IF NOT EXISTS diagnostic_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        question TEXT NOT NULL,
        options TEXT NOT NULL,
        correct_index INTEGER NOT NULL,
        difficulty TEXT NOT NULL,
        explanation TEXT NOT NULL,
        FOREIGN KEY (topic_id) REFERENCES topics (id)
    );

    CREATE TABLE IF NOT EXISTS assessment_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        percentage REAL NOT NULL,
        knowledge_level TEXT NOT NULL,
        strong_topics TEXT NOT NULL,
        weak_topics TEXT NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id)
    );

    CREATE TABLE IF NOT EXISTS student_learning_path (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        topic_id TEXT NOT NULL,
        order_index INTEGER NOT NULL,
        status TEXT NOT NULL, -- 'completed', 'in_progress', 'recommended', 'locked'
        progress_pct INTEGER NOT NULL DEFAULT 0,
        difficulty TEXT NOT NULL DEFAULT 'medium',
        is_recommended INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (topic_id) REFERENCES topics (id)
    );

    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL,
        question TEXT NOT NULL,
        options TEXT NOT NULL,
        correct_index INTEGER NOT NULL,
        difficulty TEXT NOT NULL, -- 'easy', 'medium', 'hard'
        explanation TEXT NOT NULL,
        FOREIGN KEY (topic_id) REFERENCES topics (id)
    );

    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        topic_id TEXT NOT NULL,
        question_id INTEGER,
        chosen_index INTEGER NOT NULL,
        is_correct INTEGER NOT NULL,
        difficulty TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (topic_id) REFERENCES topics (id)
    );

    CREATE TABLE IF NOT EXISTS tutor_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        topic_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id)
    );
    ''')

    conn.commit()
    conn.close()

    # Seed foundational data
    seed_initial_data()

def seed_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if topics exist
    cursor.execute("SELECT COUNT(*) as count FROM topics")
    if cursor.fetchone()['count'] == 0:
        topics = [
            ("ai-fundamentals", "AI Fundamentals", "Foundations", 1, "Core concepts of Artificial Intelligence, Turing tests, rule-based systems vs statistical systems.", "[]"),
            ("ml-basics", "Machine Learning Basics", "Core ML", 2, "Types of learning, training/validation/testing, overfitting, and evaluation metrics.", json.dumps(["ai-fundamentals"])),
            ("supervised-learning", "Supervised Learning", "Core ML", 3, "Learning with labeled data, features, targets, regression vs classification paradigms.", json.dumps(["ml-basics"])),
            ("unsupervised-learning", "Unsupervised Learning", "Core ML", 4, "Clustering, dimensionality reduction, K-Means, and discovering hidden patterns in unlabeled data.", json.dumps(["ml-basics"])),
            ("regression", "Regression", "Supervised ML", 5, "Predicting continuous numeric values, Linear Regression, Mean Squared Error, and Gradient Descent.", json.dumps(["supervised-learning"])),
            ("classification", "Classification", "Supervised ML", 6, "Categorizing data into classes, Logistic Regression, Decision Trees, Precision, Recall, and F1-Score.", json.dumps(["supervised-learning"])),
            ("deep-learning-basics", "Deep Learning Basics", "Advanced ML", 7, "Artificial Neural Networks, Perceptrons, activation functions, backpropagation, and deep layers.", json.dumps(["regression", "classification"]))
        ]
        cursor.executemany("INSERT INTO topics (id, title, category, order_index, description, prerequisites) VALUES (?, ?, ?, ?, ?, ?)", topics)

    # Check if diagnostic questions exist
    cursor.execute("SELECT COUNT(*) as count FROM diagnostic_questions")
    if cursor.fetchone()['count'] == 0:
        diag_questions = [
            (
                "ai-fundamentals", "AI Fundamentals",
                "What is the fundamental difference between traditional programming and Machine Learning?",
                json.dumps([
                    "Traditional programming uses rules + data to output answers; ML uses data + answers to discover rules",
                    "Machine learning does not require computer hardware to execute",
                    "Traditional programming only works on numbers, ML only works on images",
                    "Machine learning is completely deterministic without any statistical models"
                ]),
                0, "easy",
                "In traditional programming, humans write explicit logic/rules. In Machine Learning, models infer patterns and rules directly from example data and expected answers."
            ),
            (
                "ml-basics", "Machine Learning Basics",
                "What is 'overfitting' in machine learning models?",
                json.dumps([
                    "When a model performs poorly on training data and test data",
                    "When a model learns the noise and details of training data too well, failing to generalize to new unseen data",
                    "When a model trains in less than one second",
                    "When a dataset has too few features to train a model"
                ]),
                1, "medium",
                "Overfitting occurs when a model memorizes training samples including noise, resulting in high training accuracy but poor generalization to test data."
            ),
            (
                "supervised-learning", "Supervised Learning",
                "Which of the following problems is best solved using Supervised Learning?",
                json.dumps([
                    "Grouping online shoppers into market segments without prior tags",
                    "Predicting the resale price of a car given its mileage, age, and brand with historical sales records",
                    "Compressing high-dimensional sensor data to 2 dimensions for visualization",
                    "Detecting rare anomalies in server traffic without labeled historical incidents"
                ]),
                1, "easy",
                "Predicting car prices uses labeled historical examples (features + known sale prices), which is a classic supervised regression task."
            ),
            (
                "unsupervised-learning", "Unsupervised Learning",
                "Which algorithm is primarily used for Unsupervised Learning clustering?",
                json.dumps([
                    "Linear Regression",
                    "Support Vector Regression",
                    "K-Means Clustering",
                    "Decision Tree Classifier"
                ]),
                2, "easy",
                "K-Means Clustering is an unsupervised algorithm that partitions unlabeled data points into K distinct clusters based on feature similarity."
            ),
            (
                "regression", "Regression",
                "In Linear Regression, what does the Mean Squared Error (MSE) loss function measure?",
                json.dumps([
                    "The percentage of correctly classified categorical labels",
                    "The average of the squared differences between the predicted values and actual ground truth values",
                    "The time taken to compute gradient descent updates",
                    "The ratio of false positives to true negatives"
                ]),
                1, "medium",
                "MSE quantifies the magnitude of numeric prediction errors by averaging squared differences, heavily penalizing larger errors."
            ),
            (
                "classification", "Classification",
                "Which algorithm is commonly used for binary classification despite having 'Regression' in its name?",
                json.dumps([
                    "Linear Regression",
                    "Logistic Regression",
                    "Ridge Regression",
                    "Lasso Regression"
                ]),
                1, "easy",
                "Logistic Regression applies a sigmoid activation function to output probabilities between 0 and 1 for classification tasks."
            ),
            (
                "classification", "Classification",
                "When evaluating a model for cancer detection where missing a true positive is dangerous, which metric should be prioritized?",
                json.dumps([
                    "Accuracy alone",
                    "Recall (Sensitivity)",
                    "Precision alone",
                    "Execution Speed"
                ]),
                1, "medium",
                "Recall measures the proportion of actual positive cases detected. High recall minimizes dangerous false negatives."
            ),
            (
                "deep-learning-basics", "Deep Learning Basics",
                "What is the main role of an 'activation function' in an Artificial Neural Network?",
                json.dumps([
                    "To prevent the computer from overheating during matrix multiplication",
                    "To introduce non-linearity, allowing the network to learn complex non-linear patterns",
                    "To format the input images into grayscale values",
                    "To reset all weights back to zero after each training epoch"
                ]),
                1, "medium",
                "Without non-linear activation functions (e.g. ReLU, Sigmoid), stacking multiple neural network layers would merely collapse into a single linear transformation."
            ),
            (
                "deep-learning-basics", "Deep Learning Basics",
                "How does the 'Backpropagation' algorithm train neural network weights?",
                json.dumps([
                    "By computing the gradient of the loss with respect to each weight using the chain rule and adjusting weights backward",
                    "By randomly guessing new numbers until error reaches zero",
                    "By deleting neurons that make mistakes",
                    "By reversing the input data order on each epoch"
                ]),
                0, "hard",
                "Backpropagation calculates gradients of the loss function layer by layer from output to input via the calculus chain rule to update weights via gradient descent."
            ),
            (
                "ml-basics", "Machine Learning Basics",
                "Why is it essential to split a dataset into Training and Testing sets?",
                json.dumps([
                    "Because Python libraries cannot load an entire dataset at once",
                    "To objectively evaluate how well the trained model generalizes to unseen data",
                    "To ensure the model has 100% training accuracy",
                    "To double the size of the original dataset"
                ]),
                1, "easy",
                "A dedicated test set simulates real-world unseen data, verifying whether the model truly learned generalizable concepts rather than rote memorization."
            )
        ]
        cursor.executemany("""
            INSERT INTO diagnostic_questions (topic_id, topic_name, question, options, correct_index, difficulty, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, diag_questions)

    # Check if practice quiz questions exist
    cursor.execute("SELECT COUNT(*) as count FROM quiz_questions")
    if cursor.fetchone()['count'] == 0:
        practice_questions = [
            # AI Fundamentals
            ("ai-fundamentals", "What does 'Artificial General Intelligence' (AGI) refer to?", json.dumps(["A chess computer that only plays chess", "Hypothetical AI possessing the ability to understand and learn any intellectual task that a human can", "An algorithm that controls factory robot arms", "A database that stores SQL tables"]), 1, "easy", "AGI represents general human-level cognition across diverse domains, unlike Narrow AI which specializes in single tasks."),
            ("ai-fundamentals", "Which of the following is considered 'Narrow AI'?", json.dumps(["Spam email filtering in Gmail", "A sentient robot with human consciousness", "A system capable of writing poetry, fixing cars, and performing brain surgery interchangeably", "A fictional AI like HAL 9000"]), 0, "easy", "Email spam filtering is an example of Narrow AI tailored specifically for text classification."),
            ("ai-fundamentals", "What is the Alan Turing Test designed to evaluate?", json.dumps(["How fast a CPU runs mathematical calculations", "Whether a machine can exhibit intelligent behavior indistinguishable from a human", "How many gigabytes of memory an algorithm needs", "Whether an AI can generate computer hardware"]), 1, "medium", "The Turing Test assesses whether a human judge can reliably tell a machine's conversational output from that of a human."),
            ("ai-fundamentals", "What limitation led to the historical 'AI Winters' in the 1970s and 1980s?", json.dumps(["Lack of computational power, over-promising, and brittleness of symbolic rule systems", "Computers became too intelligent and had to be turned off", "The invention of the internet eliminated the need for computers", "Universities banned computer science departments"]), 0, "hard", "AI Winters were caused by unrealistic hype, compute constraints, and the failure of hand-coded expert systems to generalize."),

            # Machine Learning Basics
            ("ml-basics", "What is a 'feature' in machine learning terminology?", json.dumps(["An error or bug in the code", "An individual measurable property or characteristic of a phenomenon being observed", "The final score of the model", "The computer brand used for training"]), 1, "easy", "Features are input variables (columns in a dataset) used by the model to make predictions."),
            ("ml-basics", "Underfitting occurs when:", json.dumps(["The model is too complex and fits noise", "The model is too simple to capture the underlying structure of the data", "The dataset has too many training examples", "The test score is exactly 100%"]), 1, "medium", "Underfitting happens when a model lacks capacity or features, performing poorly on both training and test data."),
            ("ml-basics", "What is the role of the validation set during model development?", json.dumps(["To tune hyperparameters and detect overfitting before final test evaluation", "To act as the permanent training data", "To store user passwords", "To replace the training set completely"]), 0, "medium", "Validation data is held out during training to tune hyperparameters (like learning rate or tree depth) objectively."),
            ("ml-basics", "How does L2 Regularization (Ridge) help prevent overfitting?", json.dumps(["By penalizing the sum of squared weights, shrinking parameters toward zero", "By deleting half of the dataset randomly", "By adding more layers to the neural network", "By setting learning rate to zero"]), 0, "hard", "L2 regularization adds a penalty proportional to weight squares, discouraging extreme parameter values and reducing variance."),

            # Supervised Learning
            ("supervised-learning", "In supervised learning, what do we call the value we are trying to predict?", json.dumps(["Feature", "Target or Label", "Hyperparameter", "Weight"]), 1, "easy", "The target or label is the ground truth variable our model is trained to output."),
            ("supervised-learning", "Which problem is a regression problem, not classification?", json.dumps(["Predicting whether an email is spam or ham", "Predicting the temperature in Celsius tomorrow", "Predicting whether a transaction is fraudulent", "Predicting animal species: Cat, Dog, or Bird"]), 1, "easy", "Temperature is a continuous real number, making it a regression problem."),
            ("supervised-learning", "What is the Bias-Variance tradeoff?", json.dumps(["Balancing error from erroneous assumptions (bias) vs error from sensitivity to training fluctuations (variance)", "The cost of buying GPUs vs CPUs", "The speed difference between Python and C++", "The trade-off between battery life and screen brightness"]), 0, "medium", "High bias leads to underfitting; high variance leads to overfitting. Optimal models find the sweet spot minimizing total error."),
            ("supervised-learning", "Which metric is best when classes are heavily imbalanced (e.g. 99% negative, 1% positive)?", json.dumps(["Raw Accuracy", "Precision-Recall AUC / F1-Score", "Mean Absolute Error", "R-squared"]), 1, "hard", "Raw accuracy can be 99% by simply guessing negative every time; F1-score and PR-AUC properly reflect minority class performance."),

            # Unsupervised Learning
            ("unsupervised-learning", "Which characteristic defines unsupervised learning?", json.dumps(["Data has no predefined labels or targets", "Data must have human-verified labels", "The model only trains on GPU clusters", "The learning rate is always 1.0"]), 0, "easy", "Unsupervised algorithms learn intrinsic patterns, clusters, and structures from unlabeled datasets."),
            ("unsupervised-learning", "What is Principal Component Analysis (PCA) used for?", json.dumps(["Text translation", "Dimensionality reduction while preserving maximum variance", "Predicting stock prices", "Image generation from scratch"]), 1, "medium", "PCA projects high-dimensional data into orthogonal axes of maximal variance, reducing dimensions with minimal information loss."),
            ("unsupervised-learning", "What does the 'Elbow Method' help determine in K-Means clustering?", json.dumps(["The optimal number of clusters K", "The size of each data point", "The speed of the processor", "The accuracy of classification labels"]), 0, "medium", "The Elbow Method plots inertia (within-cluster sum of squares) against K to identify the point of diminishing returns."),
            ("unsupervised-learning", "How does DBSCAN differ from K-Means clustering?", json.dumps(["DBSCAN groups points based on density and can discover arbitrarily shaped clusters and identify noise outliers", "DBSCAN requires knowing K in advance", "DBSCAN can only work on 1-dimensional numbers", "DBSCAN is a supervised classifier"]), 0, "hard", "DBSCAN does not assume spherical clusters or require a fixed K; it isolates dense clusters and flags sparse points as noise."),

            # Regression
            ("regression", "What represents the 'slope' in the simple linear equation y = mx + b?", json.dumps(["b", "m", "y", "x"]), 1, "easy", "In y = mx + b, m is the slope (weight or coefficient) representing the rate of change."),
            ("regression", "What does R-squared (coefficient of determination) indicate?", json.dumps(["The proportion of variance in the dependent variable explained by the independent variables", "The execution time of the regression line", "The number of outliers removed", "The probability of classification error"]), 0, "medium", "R² ranges up to 1.0, showing what fraction of total outcome variance is explained by the regression model."),
            ("regression", "What happens if the learning rate in Gradient Descent is set excessively high?", json.dumps(["The algorithm converges instantly", "The loss may oscillate wildly and diverge away from the minimum", "The model automatically switches to a decision tree", "The weights freeze at 0.0"]), 1, "medium", "A high learning rate causes gradient descent to overshoot the global minimum, causing loss divergence."),
            ("regression", "What is the key difference between Lasso (L1) and Ridge (L2) regression?", json.dumps(["Lasso can shrink coefficients exactly to zero, performing automatic feature selection", "Ridge always sets coefficients to zero", "Lasso can only run on integers", "Ridge does not use any penalty term"]), 0, "hard", "L1 penalty has sharp corners in parameter space, driving less important feature coefficients strictly to zero."),

            # Classification
            ("classification", "What is the range of output values produced by the Sigmoid function?", json.dumps(["-Infinity to +Infinity", "0.0 to 1.0", "-1.0 to +1.0", "1 to 100"]), 1, "easy", "The Sigmoid function maps any real number into the open interval (0, 1), representing probabilities."),
            ("classification", "In a confusion matrix, what is a 'False Positive'?", json.dumps(["A negative instance incorrectly predicted as positive", "A positive instance correctly predicted as positive", "A negative instance correctly predicted as negative", "An unpredicted instance"]), 0, "easy", "A False Positive (Type I error) occurs when the model predicts positive, but the actual truth is negative."),
            ("classification", "What does 'Entropy' measure in a Decision Tree algorithm (like ID3 or C4.5)?", json.dumps(["The speed of leaf node splitting", "The degree of randomness or impurity in a sample of data", "The depth of the tree in levels", "The memory size of the tree"]), 1, "medium", "Entropy measures disorder or impurity; decision trees split on features that maximize Information Gain (entropy reduction)."),
            ("classification", "Why is ROC-AUC widely used to evaluate binary classifiers?", json.dumps(["It measures performance across all classification thresholds, independent of chosen cutoff", "It only works when accuracy is 100%", "It requires zero test data", "It measures how quickly the model runs on hardware"]), 0, "hard", "ROC-AUC plots True Positive Rate vs False Positive Rate across all probability thresholds, giving a threshold-agnostic quality measure."),

            # Deep Learning Basics
            ("deep-learning-basics", "What is a 'Perceptron'?", json.dumps(["The simplest unit or building block of an artificial neural network", "A type of quantum computer", "A database query language", "A brand of GPU graphics card"]), 0, "easy", "A Perceptron is an elementary artificial neuron that computes a weighted sum of inputs and passes it through an activation function."),
            ("deep-learning-basics", "Why is ReLU (Rectified Linear Unit) f(x) = max(0, x) preferred over Sigmoid in deep hidden layers?", json.dumps(["It helps mitigate the vanishing gradient problem and is computationally very fast", "It produces negative numbers to balance weights", "It converts images into text", "It eliminates the need for gradient descent"]), 0, "medium", "ReLU has a constant derivative of 1 for positive inputs, avoiding gradient saturation and vanishing in deep networks."),
            ("deep-learning-basics", "What is 'Dropout' in deep neural network training?", json.dumps(["Dropping out of school", "A regularization technique where random neurons are deactivated during training passes to prevent co-adaptation", "Deleting the test dataset", "Turning off the monitor while training"]), 1, "medium", "Dropout randomly sets a fraction of neuron outputs to zero on each training step, forcing robust redundant representations."),
            ("deep-learning-basics", "What problem occurs when gradients become exponentially small as they propagate backward through many layers?", json.dumps(["Exploding gradient problem", "Vanishing gradient problem", "Underfitting matrix collapse", "Dead processor state"]), 1, "hard", "Vanishing gradients cause earlier layers in deep architectures to update extremely slowly, hindering learning.")
        ]
        cursor.executemany("""
            INSERT INTO quiz_questions (topic_id, question, options, correct_index, difficulty, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, practice_questions)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized and seeded successfully.")
