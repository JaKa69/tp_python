import sqlite3
from pathlib import Path
from flask import Flask, render_template, g, request, flash, session, redirect, url_for

app = Flask(__name__)
app.secret_key = '8A8kWA0gTvi72Qw1Xs5KLuWF06vZjRhdsFfJ9CDTGGi8XI7MHyX4lgWQGhK0gavXpqiq2Qe6g2bZrJAB3wRPmbQmOtwSRIil2XtpAqkUSv96rVEtfqs2hMFsx8FuWYJdvtSrAMt40LUI7yI6reWXPiifRSTowGplxRBOQvuY0E7BaKOYEEH3tBDfpMkptgApcOwGM2QrTciSorffdmBxffEgMa9HgQuXuUHWOY3h6uygAUk4EHiEPGAUiqYhdZZF'

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        userInDb = query_db('select * from user where username = ?', [username], one=True)
        if userInDb is None:
            flash('Invalid username or password')
        if username == userInDb['username'] and password == userInDb['password']:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/snake')
def snake():
    return render_template('snake.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        userInDb = query_db('select * from user where username = ?', [username], one=True)
        if userInDb is None:
            userSaved = query_db('INSERT INTO user (username, password) VALUES (?, ?);', [username, password])
            get_db().commit()
            return render_template("register.html")
        else:
            flash('username already used')
    return render_template("register.html")

@app.route("/")
def init():
    if 'username' in session:
        return redirect(url_for("home"))
    return redirect(url_for('login'))

@app.route("/home")
def home():
    return render_template("home.html")

if not Path(DATABASE).exists():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()