from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

def add_person_todb(name):
    if name == "" or name == "None" or len(name) > 30:
        return None
    sql = "SELECT id FROM photos_persons WHERE LOWER(name)=LOWER(:name)"
    person_id = db.session.execute(sql, {"name":name}).fetchone()
    if person_id == None:
        sql = "INSERT INTO photos_persons (name, year) VALUES (:name,0) RETURNING id"
        person_id = db.session.execute(sql, {"name":name}).fetchone()
        db.session.commit()
    return person_id[0]

def add_keyword_todb(keyword):
    if keyword == "" or keyword == "None" or len(keyword) > 20:
        return None
    sql = "SELECT id FROM photos_keywords WHERE LOWER(keyword)=LOWER(:keyword)"
    keyword_id = db.session.execute(sql, {"keyword":keyword}).fetchone()
    if keyword_id == None:
        sql = "INSERT INTO photos_keywords (keyword) VALUES (:keyword) RETURNING id"
        keyword_id = db.session.execute(sql, {"keyword":keyword}).fetchone()
        db.session.commit()
    return keyword_id[0]

def get_all_persons():
    sql = "SELECT name FROM photos_persons ORDER BY name ASC "
    return db.session.execute(sql).fetchall()

def get_all_keywords():
    sql = "SELECT keyword FROM photos_keywords ORDER BY keyword ASC "
    return db.session.execute(sql).fetchall()
