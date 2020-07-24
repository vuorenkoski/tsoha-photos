from flask import Flask, request, session, render_template, redirect
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logindata",methods=["POST"])
def logindata():
    if "error" in session:
        session.pop("error")
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT tunnus, salasana FROM photo_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        session["error"]="tunnusta ei ole olemassa"
        return redirect("/login")
    if check_password_hash(user[1],password):
        session["username"] = user[0]
        return redirect("/")

    session["error"]="salasana on väärin"
    return redirect("/login")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signupdata",methods=["POST"])
def signupdata():
    if "error" in session:
        session.pop("error")
    username = request.form["username"]
    password = request.form["password"]
    if username == "" or password == "":
        session["error"]="tunnus tai salasana ei voi olla tyhjä"
        return redirect("/signup")

    sql = "SELECT tunnus FROM photo_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user != None:
        session["error"]="tunnus on jo käytössä"
        return redirect("/signup")
    
    hash_pw = generate_password_hash(password)
    sql = "INSERT INTO photo_kayttajat (tunnus,salasana,admin) VALUES (:username,:password,false)"
    db.session.execute(sql, {"username":username,"password":hash_pw})
    db.session.commit()

    session["username"] = username
    return redirect("/")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")
