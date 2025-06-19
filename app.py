
from flask import Flask, render_template, request, redirect, send_from_directory, session
import os
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
LIKE_FILE = 'likes.csv'
NOTES_FILE = 'notes.csv'
QUESTIONS_FILE = 'questions.csv'
REVIEW_FILE = 'reviews.csv'
EVENTS_FOLDER = 'user_events'
ANSWER_FILE = 'answers.csv'


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EVENTS_FOLDER, exist_ok=True)

# ======= ユーティリティ関数 =======

def read_likes():
    likes = {}
    if os.path.exists(LIKE_FILE):
        with open(LIKE_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    likes[row[0]] = int(row[1])
    return likes

def save_likes(likes):
    with open(LIKE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for filename, count in likes.items():
            writer.writerow([filename, count])

def load_notes():
    notes = {}
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    notes[row[0]] = row[1]
    return notes

def read_questions():
    questions = []
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 3:
                    questions.append({
                        'id': int(row[0]),
                        'title': row[1],
                        'content': row[2]
                    })
    return questions

def delete_question(question_id, username):
    questions = read_questions()
    updated = [q for q in questions if int(q['id']) != int(question_id) or q['username'] != username]
    with open(QUESTIONS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'content', 'username'])  # ヘッダー
        for q in updated:
            writer.writerow([q['id'], q['title'], q['content'], q['username']])


def save_question(title, content):
    questions = read_questions()
    new_id = questions[-1]['id'] + 1 if questions else 1
    username = session.get('username', '匿名')
    with open(QUESTIONS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([new_id, title, content, username])


ANSWER_FILE = 'answers.csv'

def save_answer(question_id, username, content):
    answers = read_all_answers()
    new_id = max([int(a['id']) for a in answers], default=0) + 1
    with open(ANSWER_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.path.getsize(ANSWER_FILE) == 0:
            writer.writerow(['id', 'question_id', 'username', 'content', 'votes'])
        writer.writerow([new_id, question_id, username, content, 0])

def read_answers(question_id):
    answers = []
    if os.path.exists(ANSWER_FILE):
        with open(ANSWER_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['question_id']) == int(question_id):
                    answers.append({
                        'id': int(row['id']),
                        'username': row['username'],
                        'content': row['content'],
                        'votes': int(row['votes'])
                    })
    return answers

def read_all_answers():
    answers = []
    if os.path.exists(ANSWER_FILE):
        with open(ANSWER_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                answers.append(row)
    return answers

def get_event_file(username):
    return os.path.join(EVENTS_FOLDER, f"events_{username}.csv")

def read_events(username):
    events = []
    filepath = get_event_file(username)
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append({
                    'id': row['id'],
                    'title': row['title'],
                    'start': row['date']
                })
    return events

def save_event(username, title, date):
    events = read_events(username)
    new_id = max([int(e['id']) for e in events], default=0) + 1
    filepath = get_event_file(username)
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['id', 'title', 'date'])
        writer.writerow([new_id, title, date])

def delete_event(username, event_id):
    events = read_events(username)
    updated = [e for e in events if e['id'] != event_id]
    filepath = get_event_file(username)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'date'])
        for e in updated:
            writer.writerow([e['id'], e['title'], e['start']])

# 口コミの保存と読み込み
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
            reader = csv.DictReader(f)
            for row in reader:
                if row['subject'] == subject:
                    reviews.append({
                        'username': row['username'],
                        'rating': int(row['rating']),
                        'comment': row['comment']
                    })
    return reviews

# ======= ルーティング =======

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
    session.pop('username', None)
    return redirect('/')

@app.route('/notes')
def notes():
    keyword = request.args.get('class', '')
    files = os.listdir(UPLOAD_FOLDER)
    likes = read_likes()
    notes = load_notes()
    if keyword:
        files = [f for f in files if keyword.lower() in notes.get(f, '').lower()]
    return render_template('notes.html', files=files, likes=likes, notes=notes, keyword=keyword)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['note']
    class_name = request.form['class']
    filename = file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    with open(NOTES_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([filename, class_name])
    return redirect('/notes')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/like/<filename>', methods=['POST'])
def like(filename):
    if 'liked_files' not in session:
        session['liked_files'] = []

    liked_files = session['liked_files']
    likes = read_likes()

    if filename in liked_files:
        # いいね取り消し
        likes[filename] = max(0, likes.get(filename, 1) - 1)
        liked_files.remove(filename)
    else:
        # いいね追加
        likes[filename] = likes.get(filename, 0) + 1
        liked_files.append(filename)

    session['liked_files'] = liked_files
    save_likes(likes)
    return redirect('/notes')  # または request.referrer で戻る


@app.route('/questions')
def questions():
    question_list = read_questions()
    return render_template('questions.html', questions=question_list)

@app.route('/ask')
def ask():
    return render_template('ask.html')

@app.route('/submit_question', methods=['POST'])
def submit_question():
    title = request.form['title']
    content = request.form['content']
    save_question(title, content)
    return redirect('/questions')

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question_route(question_id):
    if 'username' not in session:
        return redirect('/login')
    delete_question(question_id, session['username'])
    return redirect('/questions')


@app.route('/question/<int:question_id>')
def question_detail(question_id):
    questions = read_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    if not question:
        return "質問が見つかりません", 404
    answers = read_answers(question_id)
    return render_template('question_detail.html', question=question, answers=answers)

@app.route('/answer/<int:question_id>', methods=['POST'])
def answer(question_id):
    username = session.get('username', '匿名')
    content = request.form['content']
    save_answer(question_id, username, content)
    return redirect(f'/question/{question_id}')

@app.route('/vote_answer/<int:answer_id>', methods=['POST'])
def vote_answer(answer_id):
    if 'voted_answers' not in session:
        session['voted_answers'] = []

    voted = session['voted_answers']
    all_answers = read_all_answers()

    for answer in all_answers:
        if int(answer['id']) == answer_id:
            # 投票済みなら取り消す
            if answer_id in voted:
                answer['votes'] = str(max(0, int(answer['votes']) - 1))
                voted.remove(answer_id)
            else:
                answer['votes'] = str(int(answer['votes']) + 1)
                voted.append(answer_id)
            break

    # 保存
    with open(ANSWER_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'question_id', 'username', 'content', 'votes'])
        writer.writeheader()
        for ans in all_answers:
            writer.writerow(ans)

    session['voted_answers'] = voted
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
    title = request.form['title']
    date = request.form['date']
    save_event(session['username'], title, date)
    return redirect('/calendar')

@app.route('/events')
def events():
    if 'username' not in session:
        return []
    return read_events(session['username'])

@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event_route(event_id):
    if 'username' not in session:
        return redirect('/login')
    delete_event(session['username'], event_id)
    return redirect('/calendar')

@app.route('/review/<subject>', methods=['GET', 'POST'])
def review(subject):
    if request.method == 'POST':
        username = session.get('username', '匿名')
        rating = int(request.form['rating'])
        comment = request.form['comment']
        save_review(subject, username, rating, comment)
        return redirect(f'/reviews/{subject}')
    return render_template('review_form.html', subject=subject)

@app.route('/reviews/<subject>')
def reviews(subject):
    review_list = read_reviews(subject)
    avg_rating = round(sum([r['rating'] for r in review_list]) / len(review_list), 1) if review_list else None
    return render_template('reviews.html', subject=subject, reviews=review_list, avg=avg_rating)


@app.route('/reviews_redirect')
def reviews_redirect():
    subject = request.args.get('subject')
    return redirect(f'/reviews/{{subject}}')

@app.route('/subjects')
def subjects():
    subject_list = [
        "数学基礎",
        "プログラミング入門",
        "データ解析",
        "英語表現法",
        "コンピュータアーキテクチャ"
    ]
    return render_template('subjects.html', subjects=subject_list)


@app.route('/subject/<subject>', methods=['GET', 'POST'])
def subject_detail(subject):
    if request.method == 'POST':
        username = session.get('username', '匿名')
        rating = int(request.form['rating'])
        comment = request.form['comment']
        save_review(subject, username, rating, comment)
        return redirect(f'/subject/{subject}')

    review_list = read_reviews(subject)
    avg_rating = round(sum([r['rating'] for r in review_list]) / len(review_list), 1) if review_list else None
    return render_template('subject_detail.html', subject=subject, reviews=review_list, avg=avg_rating)

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/reviews_redirect')
def reviews_redirect():
    subject = request.args.get('subject')
    return redirect(f'/reviews/{subject}')

@app.route('/subjects')
def subjects():
    # 仮の授業リスト（本来はCSVやDBから読み取ってもOK）
    subject_list = [
        "数学基礎",
        "プログラミング入門",
        "データ解析",
        "英語表現法",
        "コンピュータアーキテクチャ"
    ]
    return render_template('subjects.html', subjects=subject_list)

