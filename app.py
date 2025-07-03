from flask import Flask, request, render_template, redirect
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['note']
    class_name = request.form['class']
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
