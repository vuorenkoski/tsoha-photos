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
    sql = "SELECT kayttaja_id,julkinen FROM photos_valokuvat WHERE photos_valokuvat.id=:id"
    data = db.session.execute(sql, {"id":photo_id}).fetchone()
    if data[1]:
        return True
    if "userid" in session:
        if data[0]==session["userid"]:
            return True
        sql = "SELECT kayttaja_id FROM photos_oikeudet WHERE valokuva_id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchall()
        if (session["userid"],) in data:
            return True
    return False

def get_userdata(username=None, id=None):
    if id==None:
        sql = "SELECT id, tunnus, salasana, admin FROM photos_kayttajat WHERE tunnus=:username"
        result = db.session.execute(sql, {"username":username})
        return result.fetchone()
    else:
        sql = "SELECT id, tunnus, salasana, admin FROM photos_kayttajat WHERE id=:id"
        result = db.session.execute(sql, {"id":id})
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

def set_password(password, username=None, id=None):
    if id==None:
        sql = "UPDATE photos_kayttajat SET salasana=:password WHERE tunnus=:username"
        db.session.execute(sql, {"username":username,"password":generate_password_hash(password)})
    else:
        sql = "UPDATE photos_kayttajat SET salasana=:password WHERE id=:id"
        db.session.execute(sql, {"id":id,"password":generate_password_hash(password)})
    db.session.commit()

def get_all_names():
    sql = "SELECT tunnus FROM photos_kayttajat ORDER BY tunnus ASC "
    return db.session.execute(sql).fetchall()

def get_all_data():
    sql = "SELECT photos_kayttajat.id, tunnus, count(photos_valokuvat.id) FROM photos_kayttajat " \
        "LEFT JOIN photos_valokuvat ON photos_kayttajat.id=photos_valokuvat.kayttaja_id " \
        "GROUP BY tunnus, photos_kayttajat.id ORDER BY tunnus ASC "
    return db.session.execute(sql).fetchall()

def remove(userid):
    sql = "DELETE FROM photos_kayttajat WHERE id=:id"
    db.session.execute(sql, {"id":userid})
    sql = "DELETE FROM photos_valokuvat WHERE kayttaja_id=:id"
    db.session.execute(sql, {"id":userid})
    sql = "DELETE FROM photos_oikeudet WHERE kayttaja_id=:id"
    db.session.execute(sql, {"id":userid})
    db.session.commit()
