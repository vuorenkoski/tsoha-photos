from flask import Flask, request, session, render_template, redirect, url_for
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["PHOTOFOLDER"] = getenv("PHOTOFOLDER")
app.config["MAX_CONTENT_PATH"] = 5000000000
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logindata",methods=["POST"])
def logindata():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT tunnus, salasana FROM photos_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        return render_template("login.html", error="tunnusta ei ole olemassa")
    if check_password_hash(user[1],password):
        session["username"] = user[0]
        return redirect("/")

    return render_template("login.html", error="salasana on väärin")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signupdata",methods=["POST"])
def signupdata():
    username = request.form["username"]
    password = request.form["password"]
    if username == "" or password == "":
        return render_template("signup.html", error="tunnus tai salasana ei voi olla tyhjä")

    sql = "SELECT tunnus FROM photos_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user != None:
        return render_template("signup.html", error="tunnus on jo käytössä")
    
    hash_pw = generate_password_hash(password)
    sql = "INSERT INTO photos_kayttajat (tunnus,salasana,admin) VALUES (:username,:password,false)"
    db.session.execute(sql, {"username":username,"password":hash_pw})
    db.session.commit()

    session["username"] = username
    return redirect("/")

@app.route("/upload", methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        photo = request.files["photo"]
        if photo.filename == "":
#            flash('No selected file')
            return render_template("upload.html", message="Virhe: tiedostoa ei ole valittu")
        if not photo.filename.endswith(".jpg"):
            return render_template("upload.html", message="Virhe: vain JPG tiedostoja")
        img = Image.open(photo)
        img.thumbnail((800,600))
        img.save("static/"+app.config["PHOTOFOLDER"]+"2.jpg")
        return render_template("addinfo.html", filename=url_for("static", filename=app.config["PHOTOFOLDER"] + "2.jpg"), date=img._getexif()[36867])
    return render_template("upload.html")

@app.route("/addinfo", methods=['GET', 'POST'])
def addinfo():
    if request.method == 'POST':
        pass
    return render_template("addinfo.html")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

def limit_size(img):
    limit=max(img.shape[0]/600, img.shape[0]/800)
    if limit>1:
        return img.resize()
    return img
