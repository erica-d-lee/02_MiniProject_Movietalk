from flask import Flask, render_template, request
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup



# 코딩 시작

app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbmovietalk


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/Login')
def login():
    return render_template('Login.html')


@app.route('/search/<keyword>', methods=['GET'])
def search(keyword):
    r = requests.get(f"https://openapi.naver.com/v1/search/movie.json?query={keyword}&display=20", headers={ "X-Naver-Client-Id": "UvCC6ASMTNmD3iU0PkX9",
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


        try:
            movie["desc"] = desc.text
        except Exception as e:
            continue

    print(movies[0])
    print(movies[1])


    return render_template('search.html', word=keyword, result=result, movies=movies)





@app.route('/main/getlist', methods=['GET'])
def get_list():
    movies = list(db.movie.find({}, {'_id': False}))
    return jsonify({'all_movies': movies})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)







