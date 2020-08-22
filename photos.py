from app import app
from db import db, add_person_todb, add_keyword_todb
from io import BytesIO
from PIL import Image
from flask import make_response, send_from_directory
import os, re

PHOTO_SIZE = (1600,800)
PHOTO_THUMB_SIZE = (100,100)
USE_PSQL_STORAGE_FOR_JPG = True
app.config["UPLOAD_FOLDER"] = "photos/"
app.config["MAX_CONTENT_PATH"] = 5000000000

def get_users_photos(user_id, f = None):
    values, filters = set_filters(user_id, f)
    values["user_id"] = user_id
    sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id FROM photos_valokuvat " \
        "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id WHERE kayttaja_id=:user_id " + " ".join(filters) + " ORDER BY kuvausaika ASC NULLS FIRST"
    result = db.session.execute(sql, values).fetchall()
    return result

def get_others_photos(user_id, f = None):
    values, filters = set_filters(user_id, f)
    if user_id==None:
        sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id, tunnus FROM photos_valokuvat " \
            "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id LEFT JOIN photos_kayttajat ON kayttaja_id=photos_kayttajat.id "\
            "WHERE julkinen=true " + " ".join(filters) + " ORDER BY kuvausaika ASC NULLS FIRST"
    else:
        values["user_id"] = user_id
        sql = "SELECT photos_valokuvat.id, kuvausaika, tekstikuvaus, paikka, paikka_id, tunnus FROM photos_valokuvat " \
            "LEFT JOIN photos_paikat ON paikka_id=photos_paikat.id LEFT JOIN photos_kayttajat ON kayttaja_id=photos_kayttajat.id "\
            "WHERE (julkinen=true OR photos_valokuvat.id IN (SELECT valokuva_id FROM photos_oikeudet " \
            "WHERE kayttaja_id=:user_id)) " + " ".join(filters) + " ORDER BY kuvausaika ASC NULLS FIRST"
    result = db.session.execute(sql, values).fetchall()
    return result

def set_filters(user_id, f):
    values = dict()
    filters = []
    if f!=None:
        if f["startdate"]!="":
            values["startdate"]=f["startdate"]
            filters.append("AND photos_valokuvat.kuvausaika>=:startdate")
        if f["enddate"]!="":
            values["enddate"]=f["enddate"]+" 23:59"
            filters.append("AND photos_valokuvat.kuvausaika<=:enddate")
        if f["place"]!="":
            sql = "SELECT id FROM photos_paikat WHERE paikka=:place"
            result = db.session.execute(sql, {"place":f["place"]}).fetchone()
            if result!=None:
                values["place_id"]=result[0]
                filters.append("AND photos_valokuvat.paikka_id=:place_id")
        if f["person"]!="":
            sql = "SELECT id FROM photos_henkilot WHERE nimi=:person"
            result = db.session.execute(sql, {"person":f["person"]}).fetchone()
            if result!=None:
                values["person_id"]=result[0]
                filters.append("AND photos_valokuvat.id IN (SELECT valokuva_id FROM photos_valokuvienhenkilot WHERE henkilo_id=:person_id)")
        if f["keyword"]!="":
            sql = "SELECT id FROM photos_avainsanat WHERE avainsana=:keyword"
            result = db.session.execute(sql, {"keyword":f["keyword"]}).fetchone()
            if result!=None:
                values["keyword_id"]=result[0]
                filters.append("AND photos_valokuvat.id IN (SELECT valokuva_id FROM photos_valokuvienavainsanat WHERE avainsana_id=:keyword_id)")    
        if "owner" in f and f["owner"]!="":
            sql = "SELECT id FROM photos_kayttajat WHERE tunnus=:owner"
            result = db.session.execute(sql, {"owner":f["owner"]}).fetchone()
            if result!=None:
                values["owner_id"]=result[0]
                filters.append("AND photos_valokuvat.kayttaja_id=:owner_id") 
    return (values,filters)

def save_photo(user_id, photo, place_id, photographer_id):
    image = Image.open(photo)
    image.thumbnail(PHOTO_SIZE)
    if image._getexif()!=None and (36867 in image._getexif()) and re.match(r"\d\d\d\d:\d\d:\d\d \d\d:\d\d:\d\d", image._getexif()[36867]):
        datetime=image._getexif()[36867]
        datetime=datetime[0:4]+"-"+datetime[5:7]+"-"+datetime[8:] # exif standardi YYYY:MM:DD HH:MM:SS
    else:
        datetime=None
    sql = "INSERT INTO photos_valokuvat (kayttaja_id, kuvausaika, aikaleima, tekstikuvaus, julkinen, paikka_id, valokuvaaja_id) " \
        "VALUES (:user_id, :datetime, NOW(), :description, false, :place_id, :photographer_id) RETURNING id"
    result=db.session.execute(sql, {"user_id":user_id, "datetime":datetime, "description":"", "place_id":place_id, "photographer_id":photographer_id})
    id=result.fetchone()[0]
    db.session.commit()

    save_image(image, "photo"+str(id)+".jpg")
    image.thumbnail(PHOTO_THUMB_SIZE)
    save_image(image, "photo"+str(id)+"_thmb.jpg")
    return id

def save_image(image, filename):
    if USE_PSQL_STORAGE_FOR_JPG:
        f=BytesIO()
        image.save(f, format="jpeg")
        sql = "INSERT INTO photos_jpgkuva (tiedostonimi, kuva) VALUES (:filename, :image)"
        db.session.execute(sql, {"filename":filename, "image":f.getvalue()})
        db.session.commit()
    else:
        image.save(path.join(app.config['UPLOAD_FOLDER'], tiedostonimi))

def get_attributes(photo_id):
    sql = "SELECT kuvausaika, nimi, tekstikuvaus, julkinen FROM photos_valokuvat " \
        "LEFT JOIN photos_henkilot ON photos_valokuvat.valokuvaaja_id=photos_henkilot.id WHERE photos_valokuvat.id=:photo_id"
    return db.session.execute(sql, {"photo_id":photo_id}).fetchone()

# Palauttaa valokuvassa esiintyvät henkilöt
def get_persons(photo_id):
    sql = "SELECT nimi FROM photos_henkilot,photos_valokuvienhenkilot WHERE valokuva_id=:id AND photos_henkilot.id=henkilo_id"
    persons = db.session.execute(sql, {"id":photo_id}).fetchall()
    personstr = ", ".join(t[0] for t in persons)
    if personstr=="":
        personstr = "--"
    return (personstr,persons)

# Palauttaa valokuvan avainsanat
def get_keywords(photo_id):
    sql = "SELECT avainsana FROM photos_avainsanat,photos_valokuvienavainsanat WHERE valokuva_id=:id AND photos_avainsanat.id=avainsana_id"
    keywords = db.session.execute(sql, {"id":photo_id}).fetchall()
    keywordstr = ", ".join(t[0] for t in keywords)
    if keywordstr=="":
        keywordstr = "--"
    return (keywordstr,keywords)

# Palauttaa valokuvan oikeudet
def get_permissions(photo_id):
    sql = "SELECT tunnus FROM photos_oikeudet,photos_kayttajat WHERE valokuva_id=:id AND photos_kayttajat.id=kayttaja_id"
    permissions = db.session.execute(sql, {"id":photo_id}).fetchall()
    permissionstr = ", ".join(t[0] for t in permissions)
    if permissionstr=="":
        permissionstr = "--"
    return (permissionstr,permissions)

def get_image(filename):
    if USE_PSQL_STORAGE_FOR_JPG:
        sql = "SELECT kuva FROM photos_jpgkuva WHERE tiedostonimi=:filename"
        image = db.session.execute(sql, {"filename":filename}).fetchone()[0]
        response = make_response(bytes(image))
        response.headers.set("Content-Type", "image/jpeg")
        return response
    else:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

def get_place(photo_id):
    sql = "SELECT paikka FROM photos_valokuvat LEFT JOIN photos_paikat ON photos_valokuvat.paikka_id=photos_paikat.id WHERE photos_valokuvat.id=:photo_id"
    place = db.session.execute(sql, {"photo_id":photo_id}).fetchone()[0]
    if place==None:
        place = ""
    return place

def add_person(photo_id, person):
    person_id = add_person_todb(person)
    sql = "SELECT COUNT(*) FROM photos_valokuvienhenkilot WHERE henkilo_id=:person_id AND valokuva_id=:photo_id"
    if db.session.execute(sql, {"person_id":person_id, "photo_id":photo_id}).fetchone()[0]==0:
        sql = "INSERT INTO photos_valokuvienhenkilot (henkilo_id, valokuva_id) VALUES (:person_id, :photo_id)"
        db.session.execute(sql, {"person_id":person_id, "photo_id":photo_id})
        db.session.commit()

def remove_person(photo_id, person):
    sql = "SELECT photos_valokuvienhenkilot.id FROM photos_valokuvienhenkilot, photos_henkilot " \
        "WHERE henkilo_id=photos_henkilot.id AND nimi=:person AND valokuva_id=:photo_id"
    linkid = db.session.execute(sql, {"person":person, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_valokuvienhenkilot WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def add_keyword(photo_id, keyword):
    keyword_id = add_keyword_todb(keyword)
    sql = "SELECT COUNT(*) FROM photos_valokuvienavainsanat WHERE avainsana_id=:keyword_id AND valokuva_id=:photo_id"
    if db.session.execute(sql, {"keyword_id":keyword_id, "photo_id":photo_id}).fetchone()[0]==0:
        sql = "INSERT INTO photos_valokuvienavainsanat (avainsana_id, valokuva_id) VALUES (:keyword_id, :photo_id)"
        db.session.execute(sql, {"keyword_id":keyword_id, "photo_id":photo_id})
        db.session.commit()

def remove_keyword(photo_id, keyword):
    sql = "SELECT photos_valokuvienavainsanat.id FROM photos_valokuvienavainsanat, photos_avainsanat " \
        "WHERE avainsana_id=photos_avainsanat.id AND avainsana=:keyword AND valokuva_id=:photo_id"
    linkid = db.session.execute(sql, {"keyword":keyword, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_valokuvienavainsanat WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def add_permission(photo_id, username):
    sql = "SELECT id FROM photos_kayttajat WHERE tunnus=:username"
    user_id = db.session.execute(sql, {"username":username}).fetchone()
    if user_id!=None:
        sql = "SELECT COUNT(*) FROM photos_oikeudet WHERE kayttaja_id=:user_id AND valokuva_id=:photo_id"
        if db.session.execute(sql, {"user_id":user_id[0], "photo_id":photo_id}).fetchone()[0]==0:
            db.session.execute("INSERT INTO photos_oikeudet (kayttaja_id, valokuva_id) VALUES (:user_id, :photo_id)", {"user_id":user_id[0], "photo_id":photo_id})
            db.session.commit()

def remove_permission(photo_id, username):
    sql = "SELECT photos_oikeudet.id FROM photos_oikeudet, photos_kayttajat WHERE kayttaja_id=photos_kayttajat.id AND tunnus=:username AND valokuva_id=:photo_id"
    linkid = db.session.execute(sql, {"username":username, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_oikeudet WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def update_attributes(photo_id, datetime, description, photographer_id, place_id, public):
    sql = "UPDATE photos_valokuvat SET kuvausaika=:datetime, tekstikuvaus=:description, " \
        "valokuvaaja_id=:photographer_id, paikka_id=:place_id, julkinen=:public WHERE id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id, "datetime":datetime, "description":description, "photographer_id":photographer_id, "place_id":place_id, "public":public})
    db.session.commit()

def remove(photo_id):
    sql = "DELETE FROM photos_valokuvat WHERE id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_valokuvienavainsanat WHERE valokuva_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_valokuvienhenkilot WHERE valokuva_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_oikeudet WHERE valokuva_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})

    for filename in ["photo"+str(photo_id)+".jpg", "photo"+str(photo_id)+"_thmb.jpg"]:
        if USE_PSQL_STORAGE_FOR_JPG:
            sql = "DELETE FROM photos_jpgkuva WHERE tiedostonimi=:filename"
            db.session.execute(sql, {"filename":filename})
        else:
            os.remove(app.config["UPLOAD_FOLDER"] + filename)
    db.session.commit()
