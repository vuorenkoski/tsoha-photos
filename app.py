from flask import Flask, request, session, render_template, redirect, url_for, send_from_directory
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["UPLOAD_FOLDER"] = "photos/"
app.config["MAX_CONTENT_PATH"] = 5000000000
db = SQLAlchemy(app)
PHOTO_SIZE = (1600,800)
PHTO_THUMB_SIZE = (100,100)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login",methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def logindata():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT id, tunnus, salasana FROM photos_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        return render_template("login.html", error="tunnusta ei ole olemassa")
    if check_password_hash(user[2],password):
        session["userid"] = int(user[0])
        session["username"] = user[1]
        return redirect("/")

    return render_template("login.html", error="salasana on väärin")

@app.route("/signup",methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/signup",methods=["POST"])
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

@app.route("/upload", methods=["GET", "POST"])
def upload_photo():
    if request.method == 'POST':
        photo = request.files["photo"]
        if photo.filename == "":
            return render_template("upload.html", message="Virhe: tiedostoa ei ole valittu")
        if not photo.filename.lower().endswith(".jpg"):
            return render_template("upload.html", message="Virhe: vain JPG tiedostoja")
        img = Image.open(photo)
        img.thumbnail(PHOTO_SIZE)
        date=img._getexif()[36867]
        if date!="":
            date=date[0:4]+"-"+date[5:7]+"-"+date[8:] # exif standari YYYY:MMM:DD HH:MM:SS
        sql = "INSERT INTO photos_valokuvat (kayttaja_id, kuvausaika, aikaleima, tekstikuvaus) VALUES (:userid, :kuvausaika, NOW(), :tekstikuvaus) RETURNING id;"
        result=db.session.execute(sql, {"userid":session["userid"], "kuvausaika":date, "tekstikuvaus":"--"})
        id=result.fetchone()[0]
        db.session.commit()
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], "photo"+str(id)+".jpg"))
        img.thumbnail(PHTO_THUMB_SIZE)
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], "photo"+str(id)+"_thmb.jpg"))
        return redirect("/addinfo/"+str(id))
    return render_template("upload.html")

@app.route("/addinfo/<int:id>", methods=["GET"])
def addinfo(id):
    sql = "SELECT kuvausaika, valokuvaaja_id, tekstikuvaus FROM photos_valokuvat WHERE id=:id"
    data = db.session.execute(sql, {"id":id}).fetchone()
#    if data[1]!=None:
#        pass
    return render_template("addinfo.html", photoid=id, kuvausaika=data[0], tekstikuvaus=data[2])

@app.route("/addinfo/<int:id>", methods=["POST"])
def addinfodata(id):
    kuvausaika = request.form["kuvausaika"]
    tekstikuvaus = request.form["tekstikuvaus"]
    sql = "UPDATE photos_valokuvat SET kuvausaika=:kuvausaika, tekstikuvaus=:tekstikuvaus WHERE id=:id;"
    db.session.execute(sql, {"id":id, "kuvausaika":kuvausaika, "tekstikuvaus":tekstikuvaus})
    db.session.commit()
    return redirect("/")

@app.route("/photos/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")