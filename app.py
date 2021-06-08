from flask import Flask, render_template, request
from pymongo import MongoClient

<<<<<<< HEAD
client = MongoClient('localhost', 207017)
db = client.week2


db.users.insert_one


app = Flask(__name__)

=======
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbmovietalk
>>>>>>> 7c9fccb495475087da21d916e46dbbe8bad2b3b1

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/Login')
def login():
    return render_template('Login.html')

@app.route('/search/')
def search():
    return render_template('search.html')

<<<<<<< HEAD
=======
@app.route('/main/getlist', methods=['GET'])
def get_list():
    movies = list(db.movie.find({}, {'_id': False}))
    return jsonify({'all_movies': movies})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)
>>>>>>> 7c9fccb495475087da21d916e46dbbe8bad2b3b1








if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', port=5000, debug=True)