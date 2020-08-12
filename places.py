from db import db

# Lisää paikan tietokantaan jollei sitä ole siellä aiemmin. Palauttaa paikan id numeron.
def add(place):
    if place=="" or place=="None":
        return None
    sql = "SELECT id FROM photos_paikat WHERE LOWER(paikka)=LOWER(:place)"
    place_id = db.session.execute(sql, {"place":place}).fetchone()
    if place_id==None:
        sql = "INSERT INTO photos_paikat (paikka, maa, alue, kaupunki, wwwviite) VALUES (:place, '', '', '', '') RETURNING id"
        place_id = db.session.execute(sql, {"place":place}).fetchone()
        db.session.commit()
    return place_id[0]

def get_all_names():
    sql = "SELECT paikka FROM photos_paikat"
    return db.session.execute(sql).fetchall()

def get_all():
    sql = "SELECT id,paikka, maa, alue, kaupunki, wwwviite FROM photos_paikat"
    return db.session.execute(sql).fetchall()

def get_attributes(place_id):
    sql = "SELECT paikka, kaupunki, maa, alue, wwwviite FROM photos_paikat WHERE id=:id"
    return db.session.execute(sql, {"id":place_id}).fetchone()

def update(place_id, country, region, city, wwwpage):
    sql = "UPDATE photos_paikat SET kaupunki=:city, maa=:country, alue=:region, wwwviite=:wwwpage WHERE id=:id"
    db.session.execute(sql, {"id":place_id, "country":country, "region":region, "city":city, "wwwpage":wwwpage})
    db.session.commit()