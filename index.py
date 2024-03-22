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

def check_and_notify_new_highscore(score, user_id):
    db = get_db()
    highest_score = db.execute('SELECT MAX(score) as max_score FROM score').fetchone()

    # Vérifiez si le score maximal actuel existe et si le nouveau score le dépasse
    if highest_score['max_score'] is None or score > highest_score['max_score']:
        users = db.execute('SELECT id FROM user').fetchall()
        for user in users:
            if user['id'] != user_id:  # Ne pas notifier l'utilisateur ayant battu le record
                message = 'Un nouveau record a été établi: ' + str(score) + 'pts' if highest_score['max_score'] is not None else 'Le premier score a été enregistré: ' + str(score) + 'pts'
                db.execute('INSERT INTO notification (user_id, message) VALUES (?, ?)',
                           (user['id'], message))
        db.commit()


def get_unread_notifications_count():
    user_id = session['user_id']
    db = get_db()
    unread_count = db.execute(
        'SELECT COUNT(*) FROM notification WHERE user_id = ? AND read = 0',
        (user_id,)
    ).fetchone()[0]
    return unread_count

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
    unread_notifications_count = get_unread_notifications_count()
    topScores = db.execute(
        'SELECT user.username, score.score FROM score JOIN user ON score.user_id = user.id  WHERE user.username = ? ORDER BY score.score DESC LIMIT 10',
        [username]).fetchall()
    return render_template("home.html", scores=topScores, unread_notifications_count=unread_notifications_count)


@app.route('/profile')
def profile():
    db = get_db()
    username = request.args.get('username', session['username'])
    unread_notifications_count = get_unread_notifications_count()
    scores = db.execute(
        'SELECT score.score, score.date FROM score JOIN user ON score.user_id = user.id WHERE user.username = ? ORDER BY score.score DESC',
        [username]
    ).fetchall()

    return render_template('profile.html', username=username, scores=scores, unread_notifications_count=unread_notifications_count)


@app.route("/add_score", methods=["POST"])
def add_score():
    score = request.form['score']
    user_id = session['user_id']

    check_and_notify_new_highscore(int(score), user_id)
    db = get_db()
    db.execute(
        'INSERT INTO score (user_id, score) VALUES (?, ?)',
        [user_id, score])
    db.commit()

    return redirect(url_for('home'))


@app.route("/top_scores")
def top_scores():
    db = get_db()
    unread_notifications_count = get_unread_notifications_count()
    topScores = db.execute(
        'SELECT user.username, score.score FROM score JOIN user ON score.user_id = user.id ORDER BY score.score DESC LIMIT 10'
    ).fetchall()
    return render_template("top_scores.html", scores=topScores, unread_notifications_count= unread_notifications_count)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        if new_password != confirm_new_password:
            flash('Les nouveaux mots de passe ne correspondent pas.')
            return redirect(url_for('change_password'))

        db = get_db()
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.execute('UPDATE user SET password = ? WHERE username = ?', (hashed_password, username))
            db.commit()
            flash('Le mot de passe a été changé avec succès.')
            return redirect(url_for('login'))
        else:
            flash('Nom d’utilisateur ou mot de passe actuel incorrect.')

    return render_template('change_password.html')

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = session['username']
    db = get_db()
    db.execute('DELETE FROM score WHERE user_id = (SELECT id FROM user WHERE username = ?)', (username,))
    db.execute('DELETE FROM user WHERE username = ?', (username,))
    db.commit()
    session.clear()
    flash('Votre compte a été supprimé avec succès.')
    return redirect(url_for('login'))


@app.route('/notifications')
def notifications():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user_id = session['user_id']
    notifications = db.execute('SELECT id, message, read, timestamp FROM notification WHERE user_id = ? ORDER BY timestamp DESC', (user_id,)).fetchall()
    return render_template('notifications.html', notifications=notifications)

@app.route('/mark_notification_as_read', methods=['POST'])
def mark_notification_as_read():
    notification_id = request.form['notification_id']
    db = get_db()
    db.execute('UPDATE notification SET read = 1 WHERE id = ?', (notification_id,))
    db.commit()
    return redirect(url_for('notifications'))


@app.route('/delete_notification', methods=['POST'])
def delete_notification():
    notification_id = request.form.get('notification_id')
    if notification_id:
        db = get_db()
        db.execute('DELETE FROM notification WHERE id = ?', (notification_id,))
        db.commit()
        flash('Notification supprimée avec succès.')
    else:
        flash('Erreur lors de la suppression de la notification.')

    return redirect(url_for('notifications'))


if not Path(DATABASE).exists():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
