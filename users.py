from db import db
from werkzeug.security import generate_password_hash, check_password_hash

def check_permission_to_modify(session, photo_id):
    if "userid" in session:
        sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchone()
        if data[0]==session["userid"]:
            return True
    return False

def check_permission_to_view(session, photo_id):
    if "userid" in session:
        sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchone()
        if data[0]==session["userid"] or data[1]:
            return True
        sql = "SELECT kayttaja_id FROM photos_oikeudet WHERE valokuva_id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchall()
        if (session["userid"],) in data:
            return True
    return False

def get_userdata(username):
    sql = "SELECT id, tunnus, salasana FROM photos_kayttajat WHERE tunnus=:username"
    result = db.session.execute(sql, {"username":username})
    return result.fetchone()

def username_exists(username):
    sql = "SELECT tunnus FROM photos_kayttajat WHERE tunnus=:username"
    return db.session.execute(sql, {"username":username}).fetchone()!=None

def new_user(username, password):
    sql = "INSERT INTO photos_kayttajat (tunnus,salasana,admin) VALUES (:username,:password,false) RETURNING id"
    id = db.session.execute(sql, {"username":username,"password":generate_password_hash(password)}).fetchone()[0]
    db.session.commit()
    return id

def check_password(hash, password):
    return check_password_hash(hash,password)
