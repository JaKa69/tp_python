import sqlite3
from pathlib import Path
import bcrypt
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


def hash_password(password):
    password_bytes = password.encode('utf-8')
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def init():
    if 'username' in session:
        return redirect(url_for("home"))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        userInDb = query_db('SELECT * FROM user WHERE username = ?', [username], one=True)
        if userInDb is None:
            flash('Invalid username or password')
        else:
            hashed_pw = userInDb['password'].encode('utf-8')
            if bcrypt.checkpw(password, hashed_pw):
                session['username'] = username
                session['user_id'] = userInDb['id']
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        userInDb = query_db('select * from user where username = ?', [username], one=True)
        if userInDb is None:
            userSaved = query_db('INSERT INTO user (username, password) VALUES (?, ?);', [username, password])
            get_db().commit()
            return render_template("register.html")
        else:
            flash('username already used')
    return render_template("register.html")


@app.route("/home")
def home():
    db = get_db()
    username = session['username']
    topScores = db.execute(
        'SELECT user.username, score.score FROM score JOIN user ON score.user_id = user.id  WHERE user.username = ? ORDER BY score.score DESC LIMIT 10',
        [username]).fetchall()
    return render_template("home.html", scores=topScores)


@app.route('/profile')
def profile():
    db = get_db()
    username = request.args.get('username', session['username'])
    scores = db.execute(
        'SELECT score.score, score.date FROM score JOIN user ON score.user_id = user.id WHERE user.username = ? ORDER BY score.score DESC',
        [username]
    ).fetchall()

    return render_template('profile.html', username=username, scores=scores)


@app.route("/add_score", methods=["POST"])
def add_score():
    if 'username' not in session:
        return redirect(url_for('login'))

    score = request.form['score']
    user_id = session['user_id']

    db = get_db()
    db.execute(
        'INSERT INTO score (user_id, score) VALUES (?, ?)',
        [user_id, score])
    db.commit()

    return "Score added successfully", 200


@app.route("/top_scores")
def top_scores():
    db = get_db()
    topScores = db.execute(
        'SELECT user.username, score.score FROM score JOIN user ON score.user_id = user.id ORDER BY score.score DESC LIMIT 10'
    ).fetchall()
    return render_template("top_scores.html", scores=topScores)


if not Path(DATABASE).exists():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
