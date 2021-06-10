from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import datetime
import hashlib
import jwt
from datetime import datetime, timedelta

from bson import ObjectId


app = Flask(__name__)

SECRET_KEY = 'MOVIETALK'


client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.dbmovietalk



@app.route('/')
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        movies = list(db.movie.find({}))
        list_movies = []
        for movie in movies:
            movie_id = movie['_id']
            rmovies = list(db.movie.find({"_id": movie_id}))
            tempid = str(movie_id)
            comments = list(db.comment.find({"movieid": tempid}, {"_id": False}))
            print("코멘트")
            print(comments)
            for rmovie in rmovies:
                rmovie['comments'] = comments
                rmovie["_id"] = str(rmovie["_id"])
            list_movies.append(rmovies[0])
            print("dfdfd")
            print(list_movies)
        result = sorted(list_movies, key=lambda x:len(x['comments']), reverse=True)
        return render_template('index.html', movies=result, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="login_time_expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/detail/<id>')
def detail(id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        movie_info = db.movie.find_one({'_id' : ObjectId(id)})
        print(movie_info)
        comment_info = list(db.comment.find({'movieid': id}))

        return render_template("detail.html",  user_info=user_info, movie=movie_info, comments=comment_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/api/save_comment', methods=['POST'])
def save_comment():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    nickname = db.users.find_one({'username': payload["id"]})
    print(nickname["nickname"])
    # 댓글 저장하기
    comment_receive = request.form["comment_give"]
    id_receive = request.form["id_give"]
    doc= {'nickname':nickname["nickname"], 'comment': comment_receive, 'username': payload["id"], 'movieid': id_receive}
    db.comment.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '댓글 등록이 완료 되었습니다!'})

@app.route('/login')
def login():
    msg = request.args.get("msg")
    token_receive = request.cookies.get('mytoken')
    if token_receive is None or msg == "login_time_expired":
        return render_template('login.html')
    else:
        return redirect(url_for("main"))

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

@app.route('/search', methods=['GET'])
def search_no_keyword():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('search.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="login_time_expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/search/<keyword>', methods=['GET'])
def search(keyword):

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        r = requests.get(f"https://openapi.naver.com/v1/search/movie.json?query={keyword}&display=6",
                         headers={"X-Naver-Client-Id": "UvCC6ASMTNmD3iU0PkX9",
                                  "X-Naver-Client-Secret": "imP9_GWUAj"})
        result = r.json()
        movies = result['items']

        for movie in movies:

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
            data = requests.get(movie['link'], headers=headers)
            soup = BeautifulSoup(data.text, 'html.parser')
            desc = soup.select_one(
                "#content > div.article > div.section_group.section_group_frst > div:nth-child(1) > div > div > p")

            genre = soup.select_one(
                "#content > div.article > div.wide_info_area > div.mv_info > p > span:nth-child(1) > a")

            movie["director"] = movie["director"].rstrip("|")
            movie["actor"] = movie["actor"].rstrip("|")
            try:
                movie["desc"] = desc.text
                movie["genre"] = genre.text
            except Exception as e:
                continue
        return render_template('search.html', word=keyword, result=result, movies=movies, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="login_time_expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))


@app.route('/search/save', methods=['POST'])
def sendtoDB():

    title_receive = request.form['title_give'].replace('<b>', '').replace('</b>', '')
    director_receive = request.form['director_give']
    image_receive = request.form['image_give']
    pubDate_receive = request.form['pubDate_give']
    actor_receive = request.form['actor_give']
    desc_receive = request.form['desc_give']
    genre_receive = request.form['genre_give']

    print("#####TEST #####")
    print(title_receive)
    print(director_receive)
    print(image_receive)
    print(pubDate_receive)
    print(actor_receive)
    print(desc_receive)
    print(genre_receive)

    doc = {
        "title": title_receive,
        "director": director_receive,
        "date": pubDate_receive,
        "desc": desc_receive,
        "imgurl": image_receive,
        "star": actor_receive,
        "genre": genre_receive
    }

    movie_name = db.movie.find_one({'title': request.form['title_give']})

    if movie_name is None:
        db.movie.insert_one(doc)
        print(" DB 저장 완료 ")
    else:
        print(title_receive)
        return jsonify({'msg': '이미 추가된 영화입니다. 메인 페이지에서 확인해주세요'})




    youtube_link = 'https://www.youtube.com/results?search_query=' + title_receive
    db.movie.update_one({'title': title_receive}, {'$set': {'link': youtube_link}})
    return jsonify({'msg': '등록이 완료되었습니다!'})



if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)








