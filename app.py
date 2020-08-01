from flask import Flask, request, session, render_template, redirect, url_for, send_from_directory
from os import getenv, path, urandom
from flask_sqlalchemy import SQLAlchemy

from re import compile

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

from db import db, getAllPersons, getAllKeywords, getAllUsers, add_person
import users, photos, places

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login",methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def logindata():
    kayttaja = users.getUserData(request.form["tunnus"])
    if kayttaja == None:
        return render_template("login.html", error="tunnusta ei ole olemassa")
    if users.checkPassword(kayttaja[2],request.form["salasana"]):
        session["userid"] = int(kayttaja[0])
        session["username"] = kayttaja[1]
        session["csrf_token"] = urandom(16).hex()
        return redirect("/")
    return render_template("login.html", error="salasana on väärin")

@app.route("/signup",methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/signup",methods=["POST"])
def signupdata():
    tunnus = request.form["tunnus"]
    salasana = request.form["salasana"]
    if tunnus == "" or salasana == "":
        return render_template("signup.html", error="tunnus tai salasana ei voi olla tyhjä")
    if users.usernameExists(tunnus):
        return render_template("signup.html", error="tunnus on jo käytössä")
    id = users.newUser(tunnus,salasana)
    session["username"] = tunnus
    session["userid"] = id
    session["csrf_token"] = urandom(16).hex()
    return redirect("/")

@app.route("/view", methods=["GET"])
def view():
    if "userid" in session:
        kuvat = photos.getUsersPhotos(session["userid"])
        henkilot = [photos.getPersons(kuva[0])[0] for kuva in kuvat]
        avainsanat = [photos.getKeywords(kuva[0])[0] for kuva in kuvat]
        return render_template("view.html", kuvat=list(zip(kuvat,henkilot,avainsanat)))
    else:
        return render_template("view.html")

@app.route("/viewothers", methods=["GET"])
def viewothers():
    if "userid" in session:
        kuvat = photos.getOthersPhotos(session["userid"])
        henkilot = [photos.getPersons(kuva[0])[0] for kuva in kuvat]
        avainsanat = [photos.getKeywords(kuva[0])[0] for kuva in kuvat]
        return render_template("viewothers.html", kuvat=list(zip(kuvat,henkilot,avainsanat)))
    else:
        return render_template("viewothers.html")

@app.route("/upload", methods=["GET"])
def upload_photo():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_photodata():
    if not "userid" in session or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    kuva = request.files["kuva"]
    if kuva.filename == "":
        return render_template("upload.html", message="Virhe: tiedostoa ei ole valittu")
    if not kuva.filename.lower().endswith(".jpg"):
        return render_template("upload.html", message="Virhe: vain JPG tiedostoja")
    id = photos.savePhoto(session["userid"], kuva)
    return redirect("/addinfo/"+str(id))

@app.route("/addinfo/<int:id>", methods=["GET"])
def addinfo(id):
    if not users.checkPermissionToModify(session, id):
        return "Ei oikeuksia"

    kuva = photos.getAttributes(id)
    if kuva[1]==None:
        kuvaaja=""
    else:
        kuvaaja=kuva[1]

    if kuva[3]:
        julkinen="checked"
    else:
        julkinen=""

    henkilostr,henkilot = photos.getPersons(id)
    avainsanastr,avainsanat = photos.getKeywords(id)
    paikka = photos.getPlace(id)
    oikeudetstr,oikeudet = photos.getPermissions(id)
    return render_template("addinfo.html", valokuva_id=id, paivamaara=kuva[0].strftime("%Y-%m-%d"), aika=kuva[0].strftime("%H:%M"), 
        tekstikuvaus=kuva[2], kuvaaja=kuvaaja, henkilostr=henkilostr, henkilot=henkilot, kaikkiHenkilot=getAllPersons(), 
        avainsanastr=avainsanastr, avainsanat=avainsanat, kaikkiAvainsanat=getAllKeywords(), paikka=paikka, kaikkiPaikat=places.getAllNames(), 
        julkinen=julkinen, oikeudetstr=oikeudetstr, oikeudet=oikeudet, kayttajat=getAllUsers())

@app.route("/addinfo/<int:id>", methods=["POST"])
def addinfodata(id):
    if not users.checkPermissionToModify(session, id) or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    poistu = True
    kuvausaika = request.form["kuvauspaiva"] + " " + request.form["aika"]
    tekstikuvaus = request.form["tekstikuvaus"]
    julkinen = "julkinen" in request.form
    kuvaajaid=add_person(request.form["kuvaaja"])
    paikkaid=places.add(request.form["paikka"])

    if request.form["lisaaHenkilo"]!="":
        photos.addPerson(id, request.form["lisaaHenkilo"])
        poistu=False
    if request.form["poistaHenkilo"]!="":
        photos.removePerson(id, request.form["poistaHenkilo"])
        poistu=False
    if request.form["lisaaAvainsana"]!="":
        photos.addKeyword(id, request.form["lisaaAvainsana"])
        poistu=False
    if request.form["poistaAvainsana"]!="":
        photos.removeKeyword(id, request.form["poistaAvainsana"])
        poistu=False
    if request.form["lisaaOikeus"]!="":
        photos.addPermission(id, request.form["lisaaOikeus"])
        poistu=False
    if request.form["poistaOikeus"]!="":
        photos.removePermission(id, request.form["poistaOikeus"])
        poistu=False
    photos.updateAttributes(id, kuvausaika, tekstikuvaus, kuvaajaid, paikkaid, julkinen)

    if poistu:
        return redirect("/view")
    else:
        return redirect("/addinfo/"+str(id))


@app.route("/places", methods=["GET"])
def placelist():
    if not "userid" in session:
        return "Ei oikeuksia"
    return render_template("places.html", paikat=places.getAll())

@app.route("/place/<int:id>", methods=["GET"])
def place(id):
    if not "userid" in session:
        return "Ei oikeuksia"
    paikka = places.getAttributes(id)
    return render_template("place.html", paikkaid=id, paikka=paikka[0], kaupunki=paikka[1], maa=paikka[2], alue=paikka[3], wwwsivu=paikka[4])

@app.route("/place/<int:id>", methods=["POST"])
def placedata(id):
    if not "userid" in session or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    places.update(id, request.form["maa"], request.form["alue"], request.form["kaupunki"], request.form["wwwsivu"])
    return redirect("/places")

@app.route("/placeinfo/<int:id>", methods=["GET"])
def placeinfo(id):
    if not "userid" in session:
        return "Ei oikeuksia"
    paikka = places.getAttributes(id)
    return render_template("placeinfo.html", paikkaid=id, paikka=paikka[0], kaupunki=paikka[1], maa=paikka[2], alue=paikka[3], wwwsivu=paikka[4])

@app.route("/photos/<tiedostonimi>")
def show_photo(tiedostonimi):
    p=compile(r"\d+")
    if not users.checkPermissionToView(session, int(p.findall(tiedostonimi)[0])):
        return "Ei oikeuksia"
    return photos.getImage(tiedostonimi)

@app.route("/logout")
def logout():
    del session["username"]
    del session["userid"]
    del session["csrf_token"]
    return redirect("/")
