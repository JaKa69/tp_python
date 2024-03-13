from flask import Flask, render_template

app = Flask(__name__)

@app.route("/login")
def login():
    return render_template('login.html')
@app.route("/")
def create_app():
    return render_template("home.html")