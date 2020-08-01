from db import db

# Lisää paikan tietokantaan jollei sitä ole siellä aiemmin. Palauttaa paikan id numeron.
def add(paikka):
    if paikka=="" or paikka=="None":
        return None
    sql = "SELECT id FROM photos_paikat WHERE LOWER(paikka)=LOWER(:paikka)"
    paikkaid = db.session.execute(sql, {"paikka":paikka}).fetchone()
    if paikkaid==None:
        sql = "INSERT INTO photos_paikat (paikka, maa, alue, kaupunki, wwwviite) VALUES (:paikka, '', '', '', '') RETURNING id"
        paikkaid = db.session.execute(sql, {"paikka":paikka}).fetchone()
        db.session.commit()
    return paikkaid[0]

def getAllNames():
    sql = "SELECT paikka FROM photos_paikat"
    return db.session.execute(sql).fetchall()

def getAll():
    sql = "SELECT id,paikka, maa, alue, kaupunki, wwwviite FROM photos_paikat"
    return db.session.execute(sql).fetchall()

def getAttributes(paikka_id):
    sql = "SELECT paikka, kaupunki, maa, alue, wwwviite FROM photos_paikat WHERE id=:id"
    return db.session.execute(sql, {"id":paikka_id}).fetchone()

def update(paikka_id, maa, alue, kaupunki, wwwsivu):
    sql = "UPDATE photos_paikat SET kaupunki=:kaupunki, maa=:maa, alue=:alue, wwwviite=:wwwsivu WHERE id=:id"
    db.session.execute(sql, {"id":paikka_id, "maa":maa, "alue":alue, "kaupunki":kaupunki, "wwwsivu":wwwsivu})
    db.session.commit()