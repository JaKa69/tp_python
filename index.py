import sqlite3
from pathlib import Path

from flask import Flask, render_template, g

app = Flask(__name__)

DATABASE = 'db/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

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
    for user in query_db('select * from user'):
        print(user['username'], 'has the id', user['id'])
    return render_template("home.html")


if not Path(DATABASE).exists():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()