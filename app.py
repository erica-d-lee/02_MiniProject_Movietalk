from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import datetime
import hashlib
import jwt
from datetime import datetime, timedelta
from selenium import webdriver

app = Flask(__name__)

SECRET_KEY = 'MOVIETALK'


client = MongoClient('localhost', 27017)
db = client.dbmovietalk


@app.route('/')
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        movies = list(db.movie.find({}, {"_id": False}))
        print(movies)
        return render_template('index.html', movies=movies, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="login_time_expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/detail')
def detail():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comments = list(db.comment.find({}, {"_id": False}))
        return render_template("detail.html", comments=comments, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="login_time_expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/api/save_comment', methods=['POST'])
def save_comment():
    # 댓글 저장하기
    comment_receive = request.form["comment_give"]
    doc = {"comment": comment_receive}
    db.comment.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '저장완료'})

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
        print(result)
        print(keyword)
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



    title_receive = request.form['title_give']
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
    print(movie_name)


    if movie_name is None:
        db.movie.insert_one(doc)
        print(" DB 저장 완료 ")

    else:
        print(title_receive)
        return jsonify({'msg': '이미 추가된 영화입니다. 메인 페이지에서 확인해주세요'})




    movie_title = title_receive
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome('/Users/skylerbang/Downloads/chromedriver',
                              chrome_options=chrome_options)
    driver.implicitly_wait(3)
    driver.get('https://www.youtube.com/results?search_query=' + movie_title)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    linkdata = soup.select_one(
        '#contents > ytd-video-renderer:nth-child(1) > div:nth-child(1) > ytd-thumbnail:nth-child(1) > a:nth-child(1)')[
        'href']

    youtube_link = "https://www.youtube.com"+linkdata


    db.movie.update_one({'title': title_receive}, {'$set': {'link': youtube_link}})
    return jsonify({'msg': 'POST 연결되었습니다!'})



if __name__ == '__main__':

   app.run('0.0.0.0',port=5000,debug=True)








