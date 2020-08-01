from db import db
from werkzeug.security import generate_password_hash, check_password_hash

def checkPermissionToModify(session, valokuva_id):
    if "userid" in session:
        sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
        data = db.session.execute(sql, {"id":valokuva_id}).fetchone()
        if data[0]==session["userid"]:
            return True
    return False

def checkPermissionToView(session, valokuva_id):
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

def getUserData(tunnus):
    sql = "SELECT id, tunnus, salasana FROM photos_kayttajat WHERE tunnus=:tunnus"
    result = db.session.execute(sql, {"tunnus":tunnus})
    return result.fetchone()

def usernameExists(tunnus):
    sql = "SELECT tunnus FROM photos_kayttajat WHERE tunnus=:username"
    return db.session.execute(sql, {"username":tunnus}).fetchone()!=None

def newUser(tunnus, salasana):
    sql = "INSERT INTO photos_kayttajat (tunnus,salasana,admin) VALUES (:tunnus,:salasana,false) RETURNING id"
    id = db.session.execute(sql, {"tunnus":tunnus,"salasana":generate_password_hash(salasana)}).fetchone()[0]
    db.session.commit()
    return id

def checkPassword(hash, salasana):
    return check_password_hash(hash,salasana)
