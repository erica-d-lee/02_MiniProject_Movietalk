from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import datetime
import hashlib
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)

SECRET_KEY = 'MOVIETALK'

client = MongoClient('localhost', 27017)
db = client.dbmovietalk

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/detail')
def detail():
    # DB에서 저장된 단어 찾아서 HTML에 나타내기
    comments = list(db.comment.find({}, {"_id": False}))
    return render_template("detail.html", comments=comments)

@app.route('/api/save_comment', methods=['POST'])
def save_comment():
    # 댓글 저장하기
    comment_receive = request.form["comment_give"]
    doc = {"comment": comment_receive}
    db.comment.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '저장완료'})

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "nickname": nickname_receive
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/search/')
def search():
    return render_template('search.html')

@app.route('/main/getlist', methods=['GET'])
def get_list():
    movies = list(db.movie.find({}, {'_id': False}))
    return jsonify({'all_movies': movies})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)