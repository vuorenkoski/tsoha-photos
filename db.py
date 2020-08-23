from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

def add_person_todb(name):
    if name=="" or name=="None" or len(name)>30:
        return None
    sql = "SELECT id FROM photos_henkilot WHERE LOWER(nimi)=LOWER(:name)"
    person_id = db.session.execute(sql, {"name":name}).fetchone()
    if person_id==None:
        sql = "INSERT INTO photos_henkilot (nimi, syntymavuosi) VALUES (:name,0) RETURNING id"
        person_id = db.session.execute(sql, {"name":name}).fetchone()
        db.session.commit()
    return person_id[0]

def add_keyword_todb(keyword):
    if keyword=="" or keyword=="None" or len(keyword)>20:
        return None
    sql = "SELECT id FROM photos_avainsanat WHERE LOWER(avainsana)=LOWER(:keyword)"
    keyword_id = db.session.execute(sql, {"keyword":keyword}).fetchone()
    if keyword_id==None:
        sql = "INSERT INTO photos_avainsanat (avainsana) VALUES (:keyword) RETURNING id"
        keyword_id = db.session.execute(sql, {"keyword":keyword}).fetchone()
        db.session.commit()
    return keyword_id[0]

def get_all_persons():
    sql = "SELECT nimi FROM photos_henkilot ORDER BY nimi ASC "
    return db.session.execute(sql).fetchall()

def get_all_keywords():
    sql = "SELECT avainsana FROM photos_avainsanat ORDER BY avainsana ASC "
    return db.session.execute(sql).fetchall()
