from flask import Flask, render_template, request
import pickle
import re
import string
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
import nltk
import mysql.connector
from mysql.connector import Error

# === Download stopwords ===
nltk.download('stopwords')

# === Load model & vectorizer ===
with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

with open('models/spam_model.pkl', 'rb') as f:
    model = pickle.load(f)

# === Create Flask app ===
app = Flask(__name__)

# === Set up MySQL connection ===
try:
    db = mysql.connector.connect(
        host="localhost",
        user="ikbr",
        password="ikbr",
        database="spam_checker"
    )
    cursor = db.cursor()
except Error as e:
    print(f"Database connection failed: {e}")
    db = None
    cursor = None

# === Prepare stopwords ===
stop_words = set(stopwords.words('english'))

# === Text cleaning function ===
def clean_text(text):
    text = text.lower()

    # Remove email headers
    parts = text.split('\n\n', 1)
    text = parts[1] if len(parts) > 1 else parts[0]

    # Remove MIME/encoding lines
    text = re.sub(r'.*(multipart|content[-]?type|charset|boundary|content[-]?transfer[-]?encoding|nextpart|mime).*', '', text)

    # Strip HTML
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")

    # Remove URLs, emails, numbers, punctuation
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()

    # Filter words
    css_garbage = {'visited', 'none', 'textdecoration', 'bcolor', 'nodedah', 'nonedavisited'}
    words = text.split()
    words = [w for w in words if w not in css_garbage and len(w) > 2 and len(w) < 20 and not w.startswith(('btext', 'aactive')) and w not in stop_words]

    return ' '.join(words)

# === Predict spam ===
def predict_spam(email_body, threshold=0.5):
    cleaned = clean_text(email_body)
    vector = vectorizer.transform([cleaned])
    proba = model.predict_proba(vector)[0]
    spam_proba = proba[1]
    ham_proba = proba[0]

    if spam_proba >= threshold:
        label = 'SPAM'
        confidence = spam_proba * 100
    else:
        label = 'HAM'
        confidence = ham_proba * 100

    return label, confidence

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    confidence = None

    if request.method == 'POST':
        email_body = request.form['email_body']
        label, conf = predict_spam(email_body, threshold=0.4)
        result = label
        confidence = f"{conf:.2f}%"

        # Try to save to database safely
        if db and cursor:
            try:
                insert_query = "INSERT INTO predictions (email_body, label, confidence) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (email_body, label, conf))
                db.commit()
                print("Successfully saved to database!")
            except Error as e:
                print(f"Failed to save to database: {e}")
                print("Prediction done, but failed to save to database.")
        else:
            print("Prediction done, but database connection not available.")

    return render_template('index.html', result=result, confidence=confidence)

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

# === Run ===
if __name__ == '__main__':
    app.run(debug=True)