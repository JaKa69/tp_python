import sqlite3
from flask import Flask, render_template, g

app = Flask(__name__)

DATABASE = 'db/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/login")
def login():
    return render_template('login.html')
@app.route("/")
def create_app():
    cur = get_db().cursor()
    return render_template("home.html")