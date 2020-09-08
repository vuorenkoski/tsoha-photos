from app import app
from db import db, add_person_todb, add_keyword_todb
from io import BytesIO
from PIL import Image
from flask import make_response, send_from_directory
import os, re

PHOTO_SIZE = (2400,1600)
PHOTO_THUMB_SIZE = (100,100)
USE_PSQL_STORAGE_FOR_JPG = False
app.config["UPLOAD_FOLDER"] = "photos/"
app.config["MAX_CONTENT_PATH"] = 5000000000

def get_users_photos(user_id, f=None):
    values, filters = set_filters(user_id, f)
    values["user_id"] = user_id
    sql = "SELECT photos_photos.id, datetime, description, place, place_id FROM photos_photos " \
        "LEFT JOIN photos_places ON place_id=photos_places.id WHERE user_id=:user_id " + " ".join(filters) + " ORDER BY datetime ASC NULLS FIRST"
    result = db.session.execute(sql, values).fetchall()
    return result

def get_others_photos(user_id, f=None):
    values, filters = set_filters(user_id, f)
    if user_id == None:
        sql = "SELECT photos_photos.id, datetime, description, place, place_id, username FROM photos_photos " \
            "LEFT JOIN photos_places ON place_id=photos_places.id LEFT JOIN photos_users ON user_id=photos_users.id "\
            "WHERE public=true " + " ".join(filters) + " ORDER BY datetime ASC NULLS FIRST"
    else:
        values["user_id"] = user_id
        sql = "SELECT photos_photos.id, datetime, description, place, place_id, username FROM photos_photos " \
            "LEFT JOIN photos_places ON place_id=photos_places.id LEFT JOIN photos_users ON user_id=photos_users.id "\
            "WHERE ((public=true AND photos_photos.user_id!=:user_id) OR photos_photos.id IN (SELECT photo_id FROM photos_permissions " \
            "WHERE user_id=:user_id)) " + " ".join(filters) + " ORDER BY datetime ASC NULLS FIRST"
    result = db.session.execute(sql, values).fetchall()
    return result

def set_filters(user_id, f):
    values = dict()
    filters = []
    if f != None:
        if "startdate" in f and f["startdate"] != "":
            values["startdate"]=f["startdate"]
            filters.append("AND photos_photos.datetime>=:startdate")
        if "enddate" in f and f["enddate"] != "":
            values["enddate"]=f["enddate"]+" 23:59"
            filters.append("AND photos_photos.datetime<=:enddate")
        if "place" in f and f["place"] != "":
            sql = "SELECT id FROM photos_places WHERE place=:place"
            result = db.session.execute(sql, {"place":f["place"]}).fetchone()
            if result != None:
                values["place_id"]=result[0]
                filters.append("AND photos_photos.place_id=:place_id")
        if "person" in f and f["person"] != "":
            sql = "SELECT id FROM photos_persons WHERE name=:person"
            result = db.session.execute(sql, {"person":f["person"]}).fetchone()
            if result != None:
                values["person_id"]=result[0]
                filters.append("AND photos_photos.id IN (SELECT photo_id FROM photos_photopersons WHERE person_id=:person_id)")
        if "keyqord" in f and f["keyword"] != "":
            sql = "SELECT id FROM photos_keywords WHERE keyword=:keyword"
            result = db.session.execute(sql, {"keyword":f["keyword"]}).fetchone()
            if result != None:
                values["keyword_id"]=result[0]
                filters.append("AND photos_photos.id IN (SELECT photo_id FROM photos_photokeywords WHERE keyword_id=:keyword_id)")    
        if "owner" in f and f["owner"] != "":
            sql = "SELECT id FROM photos_users WHERE username=:owner"
            result = db.session.execute(sql, {"owner":f["owner"]}).fetchone()
            if result != None:
                values["owner_id"]=result[0]
                filters.append("AND photos_photos.user_id=:owner_id") 
    return (values,filters)

def save_photo(user_id, photo, place_id, photographer_id, keyword):
    image = Image.open(photo)
    image.thumbnail(PHOTO_SIZE)
    if image._getexif() != None and (36867 in image._getexif()) and re.match(r"\d\d\d\d:\d\d:\d\d \d\d:\d\d:\d\d", image._getexif()[36867]):
        datetime = image._getexif()[36867]
        datetime = datetime[0:4]+"-"+datetime[5:7]+"-"+datetime[8:] # exif standardi YYYY:MM:DD HH:MM:SS
    else:
        datetime = None
    sql = "INSERT INTO photos_photos (user_id, datetime, timestamp, description, public, place_id, photographer_id) " \
        "VALUES (:user_id, :datetime, NOW(), :description, false, :place_id, :photographer_id) RETURNING id"
    result = db.session.execute(sql, {"user_id":user_id, "datetime":datetime, "description":"", "place_id":place_id, "photographer_id":photographer_id})
    id = result.fetchone()[0]
    add_keyword(id,keyword)
    db.session.commit()

    save_image(image, "photo"+str(id)+".jpg")
    image.thumbnail(PHOTO_THUMB_SIZE)
    save_image(image, "photo"+str(id)+"_thmb.jpg")
    return id

def save_image(image, filename):
    if USE_PSQL_STORAGE_FOR_JPG:
        f = BytesIO()
        image.save(f, format="jpeg")
        sql = "INSERT INTO photos_jpgimages (filename, image) VALUES (:filename, :image)"
        db.session.execute(sql, {"filename":filename, "image":f.getvalue()})
        db.session.commit()
    else:
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

def get_attributes(photo_id):
    sql = "SELECT datetime, name, description, public FROM photos_photos " \
        "LEFT JOIN photos_persons ON photos_photos.photographer_id=photos_persons.id WHERE photos_photos.id=:photo_id"
    return db.session.execute(sql, {"photo_id":photo_id}).fetchone()

def get_persons(photo_id):
    sql = "SELECT name FROM photos_persons,photos_photopersons WHERE photo_id=:id AND photos_persons.id=person_id"
    persons = db.session.execute(sql, {"id":photo_id}).fetchall()
    personstr = ", ".join(t[0] for t in persons)
    if personstr == "":
        personstr = "--"
    return (personstr,persons)

def get_keywords(photo_id):
    sql = "SELECT keyword FROM photos_keywords,photos_photokeywords WHERE photo_id=:id AND photos_keywords.id=keyword_id"
    keywords = db.session.execute(sql, {"id":photo_id}).fetchall()
    keywordstr = ", ".join(t[0] for t in keywords)
    if keywordstr == "":
        keywordstr = "--"
    return (keywordstr,keywords)

def get_permissions(photo_id):
    sql = "SELECT username FROM photos_permissions,photos_users WHERE photo_id=:id AND photos_users.id=user_id"
    permissions = db.session.execute(sql, {"id":photo_id}).fetchall()
    permissionstr = ", ".join(t[0] for t in permissions)
    if permissionstr == "":
        permissionstr = "--"
    return (permissionstr,permissions)

def get_image(filename):
    if USE_PSQL_STORAGE_FOR_JPG:
        sql = "SELECT image FROM photos_jpgimages WHERE filename=:filename"
        image = db.session.execute(sql, {"filename":filename}).fetchone()[0]
        response = make_response(bytes(image))
        response.headers.set("Content-Type", "image/jpeg")
        return response
    else:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

def get_place(photo_id):
    sql = "SELECT place FROM photos_photos LEFT JOIN photos_places ON photos_photos.place_id=photos_places.id WHERE photos_photos.id=:photo_id"
    place = db.session.execute(sql, {"photo_id":photo_id}).fetchone()[0]
    if place == None:
        place = ""
    return place

def add_person(photo_id, person):
    person_id = add_person_todb(person)
    if person_id == None:
        return
    sql = "SELECT COUNT(*) FROM photos_photopersons WHERE person_id=:person_id AND photo_id=:photo_id"
    if db.session.execute(sql, {"person_id":person_id, "photo_id":photo_id}).fetchone()[0] == 0:
        sql = "INSERT INTO photos_photopersons (person_id, photo_id) VALUES (:person_id, :photo_id)"
        db.session.execute(sql, {"person_id":person_id, "photo_id":photo_id})
        db.session.commit()

def remove_person(photo_id, person):
    sql = "SELECT photos_photopersons.id FROM photos_photopersons, photos_persons " \
        "WHERE person_id=photos_persons.id AND name=:person AND photo_id=:photo_id"
    linkid = db.session.execute(sql, {"person":person, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_photopersons WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def add_keyword(photo_id, keyword):
    keyword_id = add_keyword_todb(keyword)
    if keyword_id == None:
        return
    sql = "SELECT COUNT(*) FROM photos_photokeywords WHERE keyword_id=:keyword_id AND photo_id=:photo_id"
    if db.session.execute(sql, {"keyword_id":keyword_id, "photo_id":photo_id}).fetchone()[0]==0:
        sql = "INSERT INTO photos_photokeywords (keyword_id, photo_id) VALUES (:keyword_id, :photo_id)"
        db.session.execute(sql, {"keyword_id":keyword_id, "photo_id":photo_id})
        db.session.commit()

def remove_keyword(photo_id, keyword):
    sql = "SELECT photos_photokeywords.id FROM photos_photokeywords, photos_keywords " \
        "WHERE keyword_id=photos_keywords.id AND keyword=:keyword AND photo_id=:photo_id"
    linkid = db.session.execute(sql, {"keyword":keyword, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_photokeywords WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def add_permission(photo_id, username):
    sql = "SELECT id FROM photos_users WHERE username=:username"
    user_id = db.session.execute(sql, {"username":username}).fetchone()
    if user_id != None:
        sql = "SELECT COUNT(*) FROM photos_permissions WHERE user_id=:user_id AND photo_id=:photo_id"
        if db.session.execute(sql, {"user_id":user_id[0], "photo_id":photo_id}).fetchone()[0]==0:
            db.session.execute("INSERT INTO photos_permissions (user_id, photo_id) VALUES (:user_id, :photo_id)", {"user_id":user_id[0], "photo_id":photo_id})
            db.session.commit()

def remove_permission(photo_id, username):
    sql = "SELECT photos_permissions.id FROM photos_permissions, photos_users WHERE user_id=photos_users.id AND username=:username AND photo_id=:photo_id"
    linkid = db.session.execute(sql, {"username":username, "photo_id":photo_id}).fetchone()
    if linkid != None:
        db.session.execute("DELETE FROM photos_permissions WHERE id=:id", {"id":linkid[0]})
        db.session.commit()

def update_attributes(photo_id, datetime, description, photographer_id, place_id, public):
    sql = "UPDATE photos_photos SET datetime=:datetime, description=:description, " \
        "photographer_id=:photographer_id, place_id=:place_id, public=:public WHERE id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id, "datetime":datetime, "description":description, "photographer_id":photographer_id, "place_id":place_id, "public":public})
    db.session.commit()

def remove(photo_id):
    sql = "DELETE FROM photos_photos WHERE id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_photokeywords WHERE photo_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_photopersons WHERE photo_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})
    sql = "DELETE FROM photos_permissions WHERE photo_id=:photo_id"
    db.session.execute(sql, {"photo_id":photo_id})

    for filename in ["photo"+str(photo_id)+".jpg", "photo"+str(photo_id)+"_thmb.jpg"]:
        if USE_PSQL_STORAGE_FOR_JPG:
            sql = "DELETE FROM photos_jpgimages WHERE filename=:filename"
            db.session.execute(sql, {"filename":filename})
        else:
            os.remove(app.config["UPLOAD_FOLDER"] + filename)
    db.session.commit()
