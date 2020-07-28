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
    if "userid" in session:
        sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, nimi FROM photos_valokuvat LEFT JOIN photos_henkilot ON valokuvaaja_id=photos_henkilot.id WHERE kayttaja_id=:userid"
        result = db.session.execute(sql, {"userid":session["userid"]})
        photos = result.fetchall()
        return render_template("index.html", photos=photos)
    else:
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
            date=date[0:4]+"-"+date[5:7]+"-"+date[8:] # exif standardi YYYY:MMM:DD HH:MM:SS
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
    sql = "SELECT kuvausaika, nimi, tekstikuvaus FROM photos_valokuvat LEFT JOIN photos_henkilot ON photos_valokuvat.valokuvaaja_id=photos_henkilot.id WHERE photos_valokuvat.id=:id"
    data = db.session.execute(sql, {"id":id}).fetchone()

    # Haetaan valokuvien henkilot
    sql = "SELECT nimi FROM photos_henkilot,photos_valokuvienhenkilot WHERE valokuva_id=:id AND photos_henkilot.id=henkilo_id"
    henkilot = db.session.execute(sql, {"id":id}).fetchall()
    henkilot = ", ".join(t[0] for t in henkilot)

    return render_template("addinfo.html", photoid=id, paivamaara=data[0].strftime("%Y-%m-%d"), aika=data[0].strftime("%H:%M"), tekstikuvaus=data[2], kuvaaja=data[1], henkilot=henkilot)

@app.route("/addinfo/<int:id>", methods=["POST"])
def addinfodata(id):
    kuvausaika = request.form["kuvauspaiva"] + " " + request.form["aika"]
    tekstikuvaus = request.form["tekstikuvaus"]

    kuvaajaid=lisaahenkilo(request.form["kuvaaja"])

    sql = "UPDATE photos_valokuvat SET kuvausaika=:kuvausaika, tekstikuvaus=:tekstikuvaus, valokuvaaja_id=:kuvaajaid WHERE id=:id;"
    db.session.execute(sql, {"id":id, "kuvausaika":kuvausaika, "tekstikuvaus":tekstikuvaus, "kuvaajaid":kuvaajaid})
    db.session.commit()
    return redirect("/")

@app.route("/addperson/<int:id>", methods=["GET"])
def addperson(id):
    # Haetaan valokuvien henkilot
    sql = "SELECT nimi FROM photos_henkilot,photos_valokuvienhenkilot WHERE valokuva_id=:id AND photos_henkilot.id=henkilo_id"
    henkilot = db.session.execute(sql, {"id":id}).fetchall()

    sql = "SELECT nimi FROM photos_henkilot"
    henkilot_kaikki = db.session.execute(sql)
    return render_template("addperson.html", persons=henkilot, allpersons=henkilot_kaikki, photoid=id) 

@app.route("/addperson/<int:id>", methods=["POST"])
def addpersondata(id):
    for k,v in request.form.items():
        print(k)
        print(v)
    hid = lisaahenkilo(request.form["henkilo"])
    sql = "SELECT COUNT(*) FROM photos_valokuvienhenkilot WHERE henkilo_id=:hid AND valokuva_id=:vid"
    if db.session.execute(sql, {"hid":hid, "vid":id}).fetchone()[0]==0:
        db.session.execute("INSERT INTO photos_valokuvienhenkilot (henkilo_id, valokuva_id) VALUES (:hid, :vid)", {"hid":hid, "vid":id})
        db.session.commit()
    return redirect("/addperson/"+str(id))

@app.route("/photos/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

# Lisää henkilön tietokantaan jollei sitä ole siellä aiemmin. Palauttaa henkilön id numeron.
def lisaahenkilo(nimi):
    if nimi=="" or nimi=="None":
        return None
    sql = "SELECT id FROM photos_henkilot WHERE LOWER(nimi)=LOWER(:nimi)"
    henkiloid = db.session.execute(sql, {"nimi":nimi}).fetchone()
    if henkiloid==None:
        sql = "INSERT INTO photos_henkilot (nimi, syntymavuosi) VALUES (:kuvaaja,0) RETURNING id;"
        henkiloid = db.session.execute(sql, {"kuvaaja":nimi}).fetchone()
        db.session.commit()
    return henkiloid[0]