from flask import Flask, render_template, request, redirect, send_from_directory, session
import os, csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
EVENTS_FOLDER = 'user_events'
LIKE_FILE = 'likes.csv'
NOTES_FILE = 'notes.csv'
QUESTIONS_FILE = 'questions.csv'
ANSWER_FILE = 'answers.csv'
REVIEW_FILE = 'reviews.csv'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EVENTS_FOLDER, exist_ok=True)

# ===== ユーティリティ関数 =====

def read_likes():
    likes = {}
    if os.path.exists(LIKE_FILE):
        with open(LIKE_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) == 2:
                    likes[row[0]] = int(row[1])
    return likes

def save_likes(likes):
    with open(LIKE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for k, v in likes.items():
            writer.writerow([k, v])

def load_notes():
    notes = {}
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) == 2:
                    notes[row[0]] = row[1]
    return notes

def read_questions():
    questions = []
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    questions.append({'id': int(row[0]), 'title': row[1], 'content': row[2]})
    return questions

def delete_question(question_id, username):
    questions = read_questions()
    updated = [q for q in questions if q['id'] != question_id]
    with open(QUESTIONS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for q in updated:
            writer.writerow([q['id'], q['title'], q['content'], username])

def save_question(title, content):
    questions = read_questions()
    new_id = questions[-1]['id'] + 1 if questions else 1
    username = session.get('username', '匿名')
    with open(QUESTIONS_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([new_id, title, content, username])

def save_answer(qid, username, content):
    all_answers = read_all_answers()
    new_id = max([int(a['id']) for a in all_answers], default=0) + 1
    with open(ANSWER_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.path.getsize(ANSWER_FILE) == 0:
            writer.writerow(['id', 'question_id', 'username', 'content', 'votes'])
        writer.writerow([new_id, qid, username, content, 0])

def read_answers(qid):
    answers = []
    if os.path.exists(ANSWER_FILE):
        with open(ANSWER_FILE, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if int(row['question_id']) == qid:
                    answers.append({k: row[k] for k in row})
    return answers

def read_all_answers():
    if not os.path.exists(ANSWER_FILE): return []
    with open(ANSWER_FILE, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def get_event_file(username):
    return os.path.join(EVENTS_FOLDER, f"events_{username}.csv")

def read_events(username):
    events, path = [], get_event_file(username)
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                events.append({'id': row['id'], 'title': row['title'], 'start': row['date']})
    return events

def save_event(username, title, date):
    events = read_events(username)
    new_id = max([int(e['id']) for e in events], default=0) + 1
    path = get_event_file(username)
    file_exists = os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['id', 'title', 'date'])
        writer.writerow([new_id, title, date])

def delete_event(username, event_id):
    events = [e for e in read_events(username) if e['id'] != event_id]
    path = get_event_file(username)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'date'])
        for e in events:
            writer.writerow([e['id'], e['title'], e['start']])

def save_review(subject, username, rating, comment):
    file_exists = os.path.exists(REVIEW_FILE)
    with open(REVIEW_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['subject', 'username', 'rating', 'comment'])
        writer.writerow([subject, username, rating, comment])

def read_reviews(subject):
    reviews = []
    if os.path.exists(REVIEW_FILE):
        with open(REVIEW_FILE, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row['subject'] == subject:
                    reviews.append(row)
    return reviews

# ====== ルーティング ======

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/calendar')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/notes')
def notes():
    keyword = request.args.get('class', '')
    files = os.listdir(UPLOAD_FOLDER)
    notes = load_notes()
    likes = read_likes()
    if keyword:
        files = [f for f in files if keyword.lower() in notes.get(f, '').lower()]
    return render_template('notes.html', files=files, likes=likes, notes=notes, keyword=keyword)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['note']
    class_name = request.form['class']
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    with open(NOTES_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([file.filename, class_name])
    return redirect('/notes')

@app.route('/like/<filename>', methods=['POST'])
def like(filename):
    liked = session.get('liked_files', [])
    likes = read_likes()
    if filename in liked:
        likes[filename] = max(0, likes.get(filename, 1) - 1)
        liked.remove(filename)
    else:
        likes[filename] = likes.get(filename, 0) + 1
        liked.append(filename)
    session['liked_files'] = liked
    save_likes(likes)
    return redirect('/notes')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/questions')
def questions():
    return render_template('questions.html', questions=read_questions())

@app.route('/ask')
def ask():
    return render_template('ask.html')

@app.route('/submit_question', methods=['POST'])
def submit_question():
    save_question(request.form['title'], request.form['content'])
    return redirect('/questions')

@app.route('/question/<int:question_id>')
def question_detail(question_id):
    question = next((q for q in read_questions() if q['id'] == question_id), None)
    if not question:
        return "質問が見つかりません", 404
    return render_template('question_detail.html', question=question, answers=read_answers(question_id))

@app.route('/answer/<int:question_id>', methods=['POST'])
def answer(question_id):
    save_answer(question_id, session.get('username', '匿名'), request.form['content'])
    return redirect(f'/question/{question_id}')

@app.route('/vote_answer/<int:answer_id>', methods=['POST'])
def vote_answer(answer_id):
    voted = session.get('voted_answers', [])
    all_answers = read_all_answers()
    for answer in all_answers:
        if int(answer['id']) == answer_id:
            if answer_id in voted:
                answer['votes'] = str(max(0, int(answer['votes']) - 1))
                voted.remove(answer_id)
            else:
                answer['votes'] = str(int(answer['votes']) + 1)
                voted.append(answer_id)
            break
    session['voted_answers'] = voted
    with open(ANSWER_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'question_id', 'username', 'content', 'votes'])
        writer.writeheader()
        for a in all_answers:
            writer.writerow(a)
    return redirect(f"/question/{answer['question_id']}")

@app.route('/calendar')
def calendar():
    if 'username' not in session:
        return redirect('/login')
    return render_template('calendar.html', events=read_events(session['username']), username=session['username'])

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'username' not in session:
        return redirect('/login')
    save_event(session['username'], request.form['title'], request.form['date'])
    return redirect('/calendar')

@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event_route(event_id):
    if 'username' not in session:
        return redirect('/login')
    delete_event(session['username'], event_id)
    return redirect('/calendar')

@app.route('/review/<subject>', methods=['GET', 'POST'])
def review(subject):
    if request.method == 'POST':
        save_review(subject, session.get('username', '匿名'), int(request.form['rating']), request.form['comment'])
        return redirect(f'/reviews/{subject}')
    return render_template('review_form.html', subject=subject)

@app.route('/reviews/<subject>')
def reviews(subject):
    review_list = read_reviews(subject)
    avg = round(sum([int(r['rating']) for r in review_list]) / len(review_list), 1) if review_list else None
    return render_template('reviews.html', subject=subject, reviews=review_list, avg=avg)

@app.route('/reviews_redirect')
def reviews_redirect():
    subject = request.args.get('subject')
    return redirect(f'/reviews/{subject}')

# ===== メイン =====
if __name__ == '__main__':
    app.run(debug=True)
