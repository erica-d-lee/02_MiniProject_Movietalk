from flask import Flask, render_template
from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbmovietalk

@app.route('/main')
def home():
    movies = list(db.movies.find({}, {"_id": False}))
    for movie in movies:
        movie_title = movie['title']
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        driver = webdriver.Chrome('/Users/User/Desktop/chromedriver/chromedriver.exe', chrome_options=chrome_options)
        driver.implicitly_wait(3)
        driver.get('https://www.youtube.com/results?search_query='+movie_title)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        linkdata = soup.select_one('#contents > ytd-video-renderer:nth-child(1) > div:nth-child(1) > ytd-thumbnail:nth-child(1) > a:nth-child(1)')['href']
        movie['link'] = linkdata
        print(movie)
    return render_template('index.html', movies=movies)

@app.route('/Login')
def login():
    return render_template('Login.html')

@app.route('/search/')
def search():
    return render_template('search.html')

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)

