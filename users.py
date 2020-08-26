from db import db
from werkzeug.security import generate_password_hash, check_password_hash

def check_permission_to_modify(session, photo_id):
    if "userid" in session:
        sql = "SELECT user_id,public FROM photos_photos WHERE photos_photos.id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchone()
        if data[0] == session["userid"]:
            return True
    return False

def check_permission_to_view(session, photo_id):
    sql = "SELECT user_id,public FROM photos_photos WHERE photos_photos.id=:id"
    data = db.session.execute(sql, {"id":photo_id}).fetchone()
    if data[1]:
        return True
    if "userid" in session:
        if data[0] == session["userid"]:
            return True
        sql = "SELECT user_id FROM photos_permissions WHERE photo_id=:id"
        data = db.session.execute(sql, {"id":photo_id}).fetchall()
        if (session["userid"],) in data:
            return True
    return False

def get_userdata(username=None, id=None):
    if id == None:
        sql = "SELECT id, username, password, admin FROM photos_users WHERE username=:username"
        result = db.session.execute(sql, {"username":username})
        return result.fetchone()
    else:
        sql = "SELECT id, username, password, admin FROM photos_users WHERE id=:id"
        result = db.session.execute(sql, {"id":id})
        return result.fetchone()

def username_exists(username):
    sql = "SELECT username FROM photos_users WHERE username=:username"
    return db.session.execute(sql, {"username":username}).fetchone()!=None

def new_user(username, password):
    sql = "INSERT INTO photos_users (username,password,admin) VALUES (:username,:password,false) RETURNING id"
    id = db.session.execute(sql, {"username":username,"password":generate_password_hash(password)}).fetchone()[0]
    db.session.commit()
    return id

def check_password(hash, password):
    return check_password_hash(hash,password)

def set_password(password, username=None, id=None):
    if id==None:
        sql = "UPDATE photos_users SET password=:password WHERE username=:username"
        db.session.execute(sql, {"username":username,"password":generate_password_hash(password)})
    else:
        sql = "UPDATE photos_users SET password=:password WHERE id=:id"
        db.session.execute(sql, {"id":id,"password":generate_password_hash(password)})
    db.session.commit()

def get_all_names():
    sql = "SELECT username FROM photos_users ORDER BY username ASC "
    return db.session.execute(sql).fetchall()

def get_all_data():
    sql = "SELECT photos_users.id, username, count(photos_photos.id) FROM photos_users " \
        "LEFT JOIN photos_photos ON photos_users.id=photos_photos.user_id " \
        "GROUP BY username, photos_users.id ORDER BY username ASC "
    return db.session.execute(sql).fetchall()

def remove(userid):
    sql = "DELETE FROM photos_users WHERE id=:id"
    db.session.execute(sql, {"id":userid})
    db.session.commit()

def isadmin(userid):
    sql = "SELECT admin FROM photos_users WHERE id=:userid"
    return db.session.execute(sql, {"userid":userid}).fetchone()[0]
