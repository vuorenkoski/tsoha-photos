from app import app
from db import db, add_person, add_keyword
from io import BytesIO
from PIL import Image
from flask import make_response

PHOTO_SIZE = (1600,800)
PHOTO_THUMB_SIZE = (100,100)
USE_PSQL_STORAGE_FOR_JPG = True
app.config["UPLOAD_FOLDER"] = "photos/"
app.config["MAX_CONTENT_PATH"] = 5000000000

def getUsersPhotos(kayttaja_id):
    sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id FROM photos_valokuvat " \
        "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id WHERE kayttaja_id=:kayttaja_id"
    result = db.session.execute(sql, {"kayttaja_id":kayttaja_id}).fetchall()
    return sorted(result, key=lambda tup: tup[1])

def getOthersPhotos(kayttaja_id):
    sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id, tunnus FROM photos_valokuvat " \
        "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id LEFT JOIN photos_kayttajat ON kayttaja_id=photos_kayttajat.id "\
        "WHERE photos_valokuvat.id IN (SELECT photos_valokuvat.id " \
        "FROM photos_valokuvat LEFT JOIN photos_oikeudet ON valokuva_id=photos_valokuvat.id " \
        "WHERE photos_oikeudet.kayttaja_id=:kayttaja_id OR julkinen=true AND photos_valokuvat.kayttaja_id!=:kayttaja_id)"
    result = db.session.execute(sql, {"kayttaja_id":kayttaja_id}).fetchall()
    return sorted(result, key=lambda tup: tup[1])

def savePhoto(kayttaja_id, kuva):
    image = Image.open(kuva)
    image.thumbnail(PHOTO_SIZE)
    paivays=image._getexif()[36867]
    if 36867 in image._getexif():
        paivays=image._getexif()[36867]
        paivays=paivays[0:4]+"-"+paivays[5:7]+"-"+paivays[8:] # exif standardi YYYY:MMM:DD HH:MM:SS
    else:
        paivays=None
    sql = "INSERT INTO photos_valokuvat (kayttaja_id, kuvausaika, aikaleima, tekstikuvaus, julkinen) VALUES (:kayttaja_id, :paivays, NOW(), :tekstikuvaus, false) RETURNING id"
    result=db.session.execute(sql, {"kayttaja_id":kayttaja_id, "paivays":paivays, "tekstikuvaus":""})
    id=result.fetchone()[0]
    db.session.commit()

    save_photo(image, "photo"+str(id)+".jpg")
    image.thumbnail(PHOTO_THUMB_SIZE)
    save_photo(image, "photo"+str(id)+"_thmb.jpg")
    return id

def save_photo(kuva, tiedostonimi):
    if USE_PSQL_STORAGE_FOR_JPG:
        f=BytesIO()
        kuva.save(f, format="jpeg")
        sql = "INSERT INTO photos_jpgkuva (tiedostonimi, kuva) VALUES (:tiedostonimi, :kuva)"
        db.session.execute(sql, {"tiedostonimi":tiedostonimi, "kuva":f.getvalue()})
        db.session.commit()
    else:
        kuva.save(path.join(app.config['UPLOAD_FOLDER'], tiedostonimi))

def getAttributes(valokuva_id):
    sql = "SELECT kuvausaika, nimi, tekstikuvaus, julkinen FROM photos_valokuvat " \
        "LEFT JOIN photos_henkilot ON photos_valokuvat.valokuvaaja_id=photos_henkilot.id WHERE photos_valokuvat.id=:valokuva_id"
    return db.session.execute(sql, {"valokuva_id":valokuva_id}).fetchone()

# Palauttaa valokuvassa esiintyvät henkilöt
def getPersons(valokuva_id):
    sql = "SELECT nimi FROM photos_henkilot,photos_valokuvienhenkilot WHERE valokuva_id=:id AND photos_henkilot.id=henkilo_id"
    henkilot = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    henkilostr = ", ".join(t[0] for t in henkilot)
    if henkilostr=="":
        henkilostr="--"
    return (henkilostr,henkilot)

# Palauttaa valokuvan avainsanat
def getKeywords(valokuva_id):
    sql = "SELECT avainsana FROM photos_avainsanat,photos_valokuvienavainsanat WHERE valokuva_id=:id AND photos_avainsanat.id=avainsana_id"
    avainsanat = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    avainsanastr = ", ".join(t[0] for t in avainsanat)
    if avainsanastr=="":
        avainsanastr="--"
    return (avainsanastr,avainsanat)

# Palauttaa valokuvan oikeudet
def getPermissions(valokuva_id):
    sql = "SELECT tunnus FROM photos_oikeudet,photos_kayttajat WHERE valokuva_id=:id AND photos_kayttajat.id=kayttaja_id"
    oikeudet = db.session.execute(sql, {"id":valokuva_id}).fetchall()
    oikeudetstr = ", ".join(t[0] for t in oikeudet)
    if oikeudetstr=="":
        oikeudetstr="--"
    return (oikeudetstr,oikeudet)

def getImage(tiedostonimi):
    if USE_PSQL_STORAGE_FOR_JPG:
        sql = "SELECT kuva FROM photos_jpgkuva WHERE tiedostonimi=:tiedostonimi"
        kuva = db.session.execute(sql, {"tiedostonimi":tiedostonimi}).fetchone()[0]
        response = make_response(bytes(kuva))
        response.headers.set("Content-Type", "image/jpeg")
        return response
    else:
        return send_from_directory(app.config["UPLOAD_FOLDER"], tiedostonimi)

def getPlace(valokuva_id):
    sql = "SELECT paikka FROM photos_valokuvat LEFT JOIN photos_paikat ON photos_valokuvat.paikka_id=photos_paikat.id WHERE photos_valokuvat.id=:valokuva_id"
    paikka = db.session.execute(sql, {"valokuva_id":valokuva_id}).fetchone()[0]
    if paikka==None:
        paikka=""
    return paikka

def addPerson(valokuva_id, henkilo):
    hid = add_person(henkilo)
    sql = "SELECT COUNT(*) FROM photos_valokuvienhenkilot WHERE henkilo_id=:hid AND valokuva_id=:vid"
    if db.session.execute(sql, {"hid":hid, "vid":valokuva_id}).fetchone()[0]==0:
        db.session.execute("INSERT INTO photos_valokuvienhenkilot (henkilo_id, valokuva_id) VALUES (:hid, :vid)", {"hid":hid, "vid":valokuva_id})
        db.session.commit()

def removePerson(valokuva_id, henkilo):
    sql = "SELECT photos_valokuvienhenkilot.id FROM photos_valokuvienhenkilot, photos_henkilot WHERE henkilo_id=photos_henkilot.id AND nimi=:nimi AND valokuva_id=:vid"
    linkid = db.session.execute(sql, {"nimi":henkilo, "vid":valokuva_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_valokuvienhenkilot WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def addKeyword(valokuva_id, avainsana):
    aid = add_keyword(avainsana)
    sql = "SELECT COUNT(*) FROM photos_valokuvienavainsanat WHERE avainsana_id=:aid AND valokuva_id=:vid"
    if db.session.execute(sql, {"aid":aid, "vid":valokuva_id}).fetchone()[0]==0:
        db.session.execute("INSERT INTO photos_valokuvienavainsanat (avainsana_id, valokuva_id) VALUES (:aid, :vid)", {"aid":aid, "vid":valokuva_id})
        db.session.commit()

def removeKeyword(valokuva_id, avainsana):
    sql = "SELECT photos_valokuvienavainsanat.id FROM photos_valokuvienavainsanat, photos_avainsanat WHERE avainsana_id=photos_avainsanat.id AND avainsana=:avainsana AND valokuva_id=:vid"
    linkid = db.session.execute(sql, {"avainsana":avainsana, "vid":valokuva_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_valokuvienavainsanat WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def addPermission(valokuva_id, henkilo):
    sql = "SELECT id FROM photos_kayttajat WHERE tunnus=:tunnus"
    kid = db.session.execute(sql, {"tunnus":henkilo}).fetchone()
    if kid!=None:
        sql = "SELECT COUNT(*) FROM photos_oikeudet WHERE kayttaja_id=:kid AND valokuva_id=:vid"
        if db.session.execute(sql, {"kid":kid[0], "vid":valokuva_id}).fetchone()[0]==0:
            db.session.execute("INSERT INTO photos_oikeudet (kayttaja_id, valokuva_id) VALUES (:kid, :vid)", {"kid":kid[0], "vid":valokuva_id})
            db.session.commit()

def removePermission(valokuva_id, henkilo):
    sql = "SELECT photos_oikeudet.id FROM photos_oikeudet, photos_kayttajat WHERE kayttaja_id=photos_kayttajat.id AND tunnus=:tunnus AND valokuva_id=:vid"
    linkid = db.session.execute(sql, {"tunnus":henkilo, "vid":valokuva_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_oikeudet WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def updateAttributes(valokuva_id, kuvausaika, tekstikuvaus, kuvaajaid, paikkaid, julkinen):
    sql = "UPDATE photos_valokuvat SET kuvausaika=:kuvausaika, tekstikuvaus=:tekstikuvaus, valokuvaaja_id=:kuvaajaid, paikka_id=:paikkaid, julkinen=:julkinen WHERE id=:id"
    db.session.execute(sql, {"id":valokuva_id, "kuvausaika":kuvausaika, "tekstikuvaus":tekstikuvaus, "kuvaajaid":kuvaajaid, "paikkaid":paikkaid, "julkinen":julkinen})
    db.session.commit()