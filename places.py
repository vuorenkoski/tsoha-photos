from db import db

def add(place):
    if place=="" or place=="None" or len(place)>30:
        return None
    sql = "SELECT id FROM photos_paikat WHERE LOWER(paikka)=LOWER(:place)"
    place_id = db.session.execute(sql, {"place":place}).fetchone()
    if place_id == None:
        sql = "INSERT INTO photos_paikat (paikka, maa, alue, kaupunki, wwwviite) VALUES (:place, '', '', '', '') RETURNING id"
        place_id = db.session.execute(sql, {"place":place}).fetchone()
        db.session.commit()
    return place_id[0]

def get_all_names():
    sql = "SELECT paikka FROM photos_paikat ORDER BY paikka ASC"
    return db.session.execute(sql).fetchall()

def get_all():
    sql = "SELECT id,paikka, maa, alue, kaupunki, wwwviite FROM photos_paikat ORDER BY paikka ASC"
    return db.session.execute(sql).fetchall()

def get_attributes(place_id):
    sql = "SELECT paikka, kaupunki, maa, alue, wwwviite FROM photos_paikat WHERE id=:id"
    return db.session.execute(sql, {"id":place_id}).fetchone()

def update(place_id, country, region, city, wwwpage):
    if len(country)>30 or len(region)>30 or len(city)>30 or len(wwwpage)>70:
        return
    sql = "UPDATE photos_paikat SET kaupunki=:city, maa=:country, alue=:region, wwwviite=:wwwpage WHERE id=:id"
    db.session.execute(sql, {"id":place_id, "country":country, "region":region, "city":city, "wwwpage":wwwpage})
    db.session.commit()

def count(place_id):
    sql = "SELECT count(id) FROM photos_valokuvat WHERE paikka_id=:place_id"
    return db.session.execute(sql, {"place_id":place_id}).fetchone()[0]

def remove(place_id):
    if count(place_id) == 0:
        sql = "DELETE FROM photos_paikat WHERE id=:id"
        db.session.execute(sql, {"id":place_id})
        db.session.commit()