from flask import Flask, request, session, render_template, redirect, url_for, send_from_directory, make_response
from os import getenv, path
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from datetime import datetime
from io import BytesIO
import re

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["UPLOAD_FOLDER"] = "photos/"
app.config["MAX_CONTENT_PATH"] = 5000000000
db = SQLAlchemy(app)

PHOTO_SIZE = (1600,800)
PHOTO_THUMB_SIZE = (100,100)
USE_PSQL_STORAGE_FOR_JPG = True

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

@app.route("/view", methods=["GET"])
def view():
    if "userid" in session:
        sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id FROM photos_valokuvat LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id WHERE kayttaja_id=:userid"
        kuvat = db.session.execute(sql, {"userid":session["userid"]}).fetchall()
        henkilot = [getPersons(kuva[0])[0] for kuva in kuvat]
        avainsanat = [getKeywords(kuva[0])[0] for kuva in kuvat]
        return render_template("view.html", kuvat=list(zip(kuvat,henkilot,avainsanat)))
    else:
        return render_template("view.html")

@app.route("/viewothers", methods=["GET"])
def viewothers():
    if "userid" in session:
        sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id, tunnus FROM photos_valokuvat " \
        "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id LEFT JOIN photos_kayttajat ON kayttaja_id=photos_kayttajat.id "\
        "WHERE photos_valokuvat.id IN (SELECT photos_valokuvat.id " \
        "FROM photos_valokuvat LEFT JOIN photos_oikeudet ON valokuva_id=photos_valokuvat.id " \
        "WHERE photos_oikeudet.kayttaja_id=:userid OR julkinen=true AND photos_valokuvat.kayttaja_id!=:userid)"
        kuvat = db.session.execute(sql, {"userid":session["userid"]}).fetchall()
        henkilot = [getPersons(kuva[0])[0] for kuva in kuvat]
        avainsanat = [getKeywords(kuva[0])[0] for kuva in kuvat]
        return render_template("viewothers.html", kuvat=list(zip(kuvat,henkilot,avainsanat)))
    else:
        return render_template("viewothers.html")

@app.route("/upload", methods=["GET"])
def upload_photo():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_photodata():
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
    sql = "INSERT INTO photos_valokuvat (kayttaja_id, kuvausaika, aikaleima, tekstikuvaus, julkinen) VALUES (:userid, :kuvausaika, NOW(), :tekstikuvaus, false) RETURNING id"
    result=db.session.execute(sql, {"userid":session["userid"], "kuvausaika":date, "tekstikuvaus":""})
    id=result.fetchone()[0]
    db.session.commit()

    save_photo(img, "photo"+str(id)+".jpg")
    img.thumbnail(PHOTO_THUMB_SIZE)
    save_photo(img, "photo"+str(id)+"_thmb.jpg")
    return redirect("/addinfo/"+str(id))

@app.route("/addinfo/<int:id>", methods=["GET"])
def addinfo(id):
    if not checkPermissionToModify(id):
        return "Ei oikeuksia"
    sql = "SELECT kuvausaika, nimi, tekstikuvaus, julkinen FROM photos_valokuvat LEFT JOIN photos_henkilot ON photos_valokuvat.valokuvaaja_id=photos_henkilot.id WHERE photos_valokuvat.id=:id"
    data = db.session.execute(sql, {"id":id}).fetchone()

    # Haetaan valokuvien henkilot ja kaikki henkilöt
    henkilostr,henkilot = getPersons(id)
    sql = "SELECT nimi FROM photos_henkilot"
    kaikkiHenkilot = db.session.execute(sql)

    # Haetaan valokuvien avainsanat ja kaikki avainsanat
    avainsanastr,avainsanat = getKeywords(id)
    sql = "SELECT avainsana FROM photos_avainsanat"
    kaikkiAvainsanat = db.session.execute(sql)

    # Haetaan paikan nimi ja kaikki paikat
    sql = "SELECT paikka FROM photos_valokuvat LEFT JOIN photos_paikat ON photos_valokuvat.paikka_id=photos_paikat.id WHERE photos_valokuvat.id=:id"
    paikka = db.session.execute(sql, {"id":id}).fetchone()[0]
    if paikka==None:
        paikka=""
    sql = "SELECT paikka FROM photos_paikat"
    kaikkiPaikat = db.session.execute(sql)

    # Haetaan oikeudet ja kaikki käyttäjät
    oikeudetstr,oikeudet = getPermissions(id)
    sql = "SELECT tunnus FROM photos_kayttajat"
    kayttajat = db.session.execute(sql)

    if data[1]==None:
        kuvaaja=""
    else:
        kuvaaja=data[1]

    if data[3]:
        julkinen="checked"
    else:
        julkinen=""

    return render_template("addinfo.html", photoid=id, paivamaara=data[0].strftime("%Y-%m-%d"), aika=data[0].strftime("%H:%M"), 
        tekstikuvaus=data[2], kuvaaja=kuvaaja, henkilostr=henkilostr, henkilot=henkilot, kaikkiHenkilot=kaikkiHenkilot, 
        avainsanastr=avainsanastr, avainsanat=avainsanat, kaikkiAvainsanat=kaikkiAvainsanat, paikka=paikka, kaikkiPaikat=kaikkiPaikat, 
        julkinen=julkinen, oikeudetstr=oikeudetstr, oikeudet=oikeudet, kayttajat=kayttajat)

@app.route("/addinfo/<int:id>", methods=["POST"])
def addinfodata(id):
    if not checkPermissionToModify(id):
        return "Ei oikeuksia"
    poistu = True
    kuvausaika = request.form["kuvauspaiva"] + " " + request.form["aika"]
    tekstikuvaus = request.form["tekstikuvaus"]
    julkinen = "julkinen" in request.form
    kuvaajaid=add_person(request.form["kuvaaja"])
    paikkaid=add_place(request.form["paikka"])

    # Henkilöiden lisääminen ja poistaminen
    if request.form["lisaaHenkilo"]!="":
        hid = add_person(request.form["lisaaHenkilo"])
        sql = "SELECT COUNT(*) FROM photos_valokuvienhenkilot WHERE henkilo_id=:hid AND valokuva_id=:vid"
        if db.session.execute(sql, {"hid":hid, "vid":id}).fetchone()[0]==0:
            db.session.execute("INSERT INTO photos_valokuvienhenkilot (henkilo_id, valokuva_id) VALUES (:hid, :vid)", {"hid":hid, "vid":id})
            db.session.commit()
        poistu=False

    if request.form["poistaHenkilo"]!="":
        sql = "SELECT photos_valokuvienhenkilot.id FROM photos_valokuvienhenkilot, photos_henkilot WHERE henkilo_id=photos_henkilot.id AND nimi=:nimi AND valokuva_id=:vid"
        linkid = db.session.execute(sql, {"nimi":request.form["poistaHenkilo"], "vid":id}).fetchone()
        if linkid != None:
            db.session.execute("DELETE FROM photos_valokuvienhenkilot WHERE id=:id", {"id":linkid[0]})
            db.session.commit()
        poistu=False

    # Avainsanojen lisääminen ja poistaminen
    if request.form["lisaaAvainsana"]!="":
        aid = add_keyword(request.form["lisaaAvainsana"])
        sql = "SELECT COUNT(*) FROM photos_valokuvienavainsanat WHERE avainsana_id=:aid AND valokuva_id=:vid"
        if db.session.execute(sql, {"aid":aid, "vid":id}).fetchone()[0]==0:
            db.session.execute("INSERT INTO photos_valokuvienavainsanat (avainsana_id, valokuva_id) VALUES (:aid, :vid)", {"aid":aid, "vid":id})
            db.session.commit()
        poistu=False

    if request.form["poistaAvainsana"]!="":
        sql = "SELECT photos_valokuvienavainsanat.id FROM photos_valokuvienavainsanat, photos_avainsanat WHERE avainsana_id=photos_avainsanat.id AND avainsana=:avainsana AND valokuva_id=:vid"
        linkid = db.session.execute(sql, {"avainsana":request.form["poistaAvainsana"], "vid":id}).fetchone()
        if linkid != None:
            db.session.execute("DELETE FROM photos_valokuvienavainsanat WHERE id=:id", {"id":linkid[0]})
            db.session.commit()
        poistu=False

    # Oikeuksien lisääminen ja poistaminen
    if request.form["lisaaOikeus"]!="":
        sql = "SELECT id FROM photos_kayttajat WHERE tunnus=:tunnus"
        kid = db.session.execute(sql, {"tunnus":request.form["lisaaOikeus"]}).fetchone()[0]
        if kid!=None:
            sql = "SELECT COUNT(*) FROM photos_oikeudet WHERE kayttaja_id=:kid AND valokuva_id=:vid"
            if db.session.execute(sql, {"kid":kid, "vid":id}).fetchone()[0]==0:
                db.session.execute("INSERT INTO photos_oikeudet (kayttaja_id, valokuva_id) VALUES (:kid, :vid)", {"kid":kid, "vid":id})
                db.session.commit()
        poistu=False

    if request.form["poistaOikeus"]!="":
        sql = "SELECT photos_oikeudet.id FROM photos_oikeudet, photos_kayttajat WHERE kayttaja_id=photos_kayttajat.id AND tunnus=:tunnus AND valokuva_id=:vid"
        linkid = db.session.execute(sql, {"tunnus":request.form["poistaOikeus"], "vid":id}).fetchone()
        if linkid != None:
            db.session.execute("DELETE FROM photos_oikeudet WHERE id=:id", {"id":linkid[0]})
            db.session.commit()
        poistu=False

    sql = "UPDATE photos_valokuvat SET kuvausaika=:kuvausaika, tekstikuvaus=:tekstikuvaus, valokuvaaja_id=:kuvaajaid, paikka_id=:paikkaid, julkinen=:julkinen WHERE id=:id"
    db.session.execute(sql, {"id":id, "kuvausaika":kuvausaika, "tekstikuvaus":tekstikuvaus, "kuvaajaid":kuvaajaid, "paikkaid":paikkaid, "julkinen":julkinen})
    db.session.commit()

    if poistu:
        return redirect("/view")
    else:
        return redirect("/addinfo/"+str(id))


@app.route("/places", methods=["GET"])
def places():
    if not "userid" in session:
        return "Ei oikeuksia"
    sql = "SELECT id,paikka, maa, alue, kaupunki, wwwviite FROM photos_paikat"
    paikat = db.session.execute(sql).fetchall()
    return render_template("places.html", paikat=paikat)

@app.route("/place/<int:id>", methods=["GET"])
def placeinfo(id):
    if not "userid" in session:
        return "Ei oikeuksia"
    sql = "SELECT paikka, kaupunki, maa, alue, wwwviite FROM photos_paikat WHERE id=:id"
    data = db.session.execute(sql, {"id":id}).fetchone()
    return render_template("place.html", paikkaid=id, paikka=data[0], kaupunki=data[1], maa=data[2], alue=data[3], wwwsivu=data[4])

@app.route("/place/<int:id>", methods=["POST"])
def placeinfodata(id):
    if not "userid" in session:
        return "Ei oikeuksia"
    sql = "UPDATE photos_paikat SET kaupunki=:kaupunki, maa=:maa, alue=:alue, wwwviite=:wwwsivu WHERE id=:id"
    db.session.execute(sql, {"id":id, "maa":request.form["maa"], "alue":request.form["alue"], "kaupunki":request.form["kaupunki"], "wwwsivu":request.form["wwwsivu"]})
    db.session.commit()
    return redirect("/places")

@app.route("/photos/<tiedostonimi>")
def show_photo(tiedostonimi):
    p=re.compile(r"\d+")
    if not checkPermissionToView(int(p.findall(tiedostonimi)[0])):
        return "Ei oikeuksia"
    if USE_PSQL_STORAGE_FOR_JPG:
        sql = "SELECT kuva FROM photos_jpgkuva WHERE tiedostonimi=:tiedostonimi"
        kuva = db.session.execute(sql, {"tiedostonimi":tiedostonimi}).fetchone()[0]
        response = make_response(bytes(kuva))
        response.headers.set('Content-Type', 'image/jpeg')
        return response
        retun
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], tiedostonimi)

@app.route("/logout")
def logout():
    del session["username"]
    del session["userid"]
    return redirect("/")

# Lisää henkilön tietokantaan jollei sitä ole siellä aiemmin. Palauttaa henkilön id numeron.
def add_person(nimi):
    if nimi=="" or nimi=="None":
        return None
    sql = "SELECT id FROM photos_henkilot WHERE LOWER(nimi)=LOWER(:nimi)"
    henkiloid = db.session.execute(sql, {"nimi":nimi}).fetchone()
    if henkiloid==None:
        sql = "INSERT INTO photos_henkilot (nimi, syntymavuosi) VALUES (:nimi,0) RETURNING id"
        henkiloid = db.session.execute(sql, {"nimi":nimi}).fetchone()
        db.session.commit()
    return henkiloid[0]

# Lisää avainsanan tietokantaan jollei sitä ole siellä aiemmin. Palauttaa avainsanan id numeron.
def add_keyword(avainsana):
    if avainsana=="" or avainsana=="None":
        return None
    sql = "SELECT id FROM photos_avainsanat WHERE LOWER(avainsana)=LOWER(:avainsana)"
    avainsanaid = db.session.execute(sql, {"avainsana":avainsana}).fetchone()
    if avainsanaid==None:
        sql = "INSERT INTO photos_avainsanat (avainsana) VALUES (:avainsana) RETURNING id"
        avainsanaid = db.session.execute(sql, {"avainsana":avainsana}).fetchone()
        db.session.commit()
    return avainsanaid[0]

# Lisää paikan tietokantaan jollei sitä ole siellä aiemmin. Palauttaa paikan id numeron.
def add_place(paikka):
    if paikka=="" or paikka=="None":
        return None
    sql = "SELECT id FROM photos_paikat WHERE LOWER(paikka)=LOWER(:paikka)"
    paikkaid = db.session.execute(sql, {"paikka":paikka}).fetchone()
    if paikkaid==None:
        sql = "INSERT INTO photos_paikat (paikka, maa, alue, kaupunki, wwwviite) VALUES (:paikka, '', '', '', '') RETURNING id"
        paikkaid = db.session.execute(sql, {"paikka":paikka}).fetchone()
        db.session.commit()
    return paikkaid[0]

def getPersons(valokuva_id):
    sql = "SELECT nimi FROM photos_henkilot,photos_valokuvienhenkilot WHERE valokuva_id=:id AND photos_henkilot.id=henkilo_id"
    henkilot = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    henkilostr = ", ".join(t[0] for t in henkilot)
    if henkilostr=="":
        henkilostr="--"
    return (henkilostr,henkilot)

def getKeywords(valokuva_id):
    sql = "SELECT avainsana FROM photos_avainsanat,photos_valokuvienavainsanat WHERE valokuva_id=:id AND photos_avainsanat.id=avainsana_id"
    avainsanat = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    avainsanastr = ", ".join(t[0] for t in avainsanat)
    if avainsanastr=="":
        avainsanastr="--"
    return (avainsanastr,avainsanat)

def getPermissions(valokuva_id):
    sql = "SELECT tunnus FROM photos_oikeudet,photos_kayttajat WHERE valokuva_id=:id AND photos_kayttajat.id=kayttaja_id"
    oikeudet = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    oikeudetstr = ", ".join(t[0] for t in oikeudet)
    if oikeudetstr=="":
        oikeudetstr="--"
    return (oikeudetstr,oikeudet)

def save_photo(kuva, tiedostonimi):
    if USE_PSQL_STORAGE_FOR_JPG:
        f=BytesIO()
        kuva.save(f, format="jpeg")
        sql = "INSERT INTO photos_jpgkuva (tiedostonimi, kuva) VALUES (:tiedostonimi, :kuva)"
        db.session.execute(sql, {"tiedostonimi":tiedostonimi, "kuva":f.getvalue()})
        db.session.commit()
    else:
        kuva.save(path.join(app.config['UPLOAD_FOLDER'], tiedostonimi))

def checkPermissionToModify(valokuva_id):
    if "userid" in session:
        sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
        data = db.session.execute(sql, {"id":valokuva_id}).fetchone()
        if data[0]==session["userid"]:
            return True
    return False

def checkPermissionToView(valokuva_id):
    if "userid" in session:
        sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
        data = db.session.execute(sql, {"id":valokuva_id}).fetchone()
        if data[0]==session["userid"] or data[1]:
            return True
        sql = "SELECT kayttaja_id FROM photos_oikeudet WHERE valokuva_id=:id"
        data = db.session.execute(sql, {"id":valokuva_id}).fetchall()
        print(data)
        if (session["userid"],) in data:
            return True
    return False