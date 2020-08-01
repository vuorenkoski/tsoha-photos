from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

# Lisää henkilön tietokantaan jollei sitä ole siellä aiemmin. Palauttaa henkilön id numeron.
def add_person(nimi):
    if nimi=="" or nimi=="None":
        return None
    sql = "SELECT id FROM photos_henkilot WHERE LOWER(nimi)=LOWER(:nimi)"
    henkiloid = db.session.execute(sql, {"nimi":nimi}).fetchone()
    if henkiloid==None:
        sql = "INSERT INTO photos_henkilot (nimi, syntymavuosi) VALUES (:nimi,0) RETURNING id"
        henkiloid = db.session.execute(sql, {"nimi":nimi}).fetchone()
        db.session.commit()
    return henkiloid[0]

# Lisää avainsanan tietokantaan jollei sitä ole siellä aiemmin. Palauttaa avainsanan id numeron.
def add_keyword(avainsana):
    if avainsana=="" or avainsana=="None":
        return None
    sql = "SELECT id FROM photos_avainsanat WHERE LOWER(avainsana)=LOWER(:avainsana)"
    avainsanaid = db.session.execute(sql, {"avainsana":avainsana}).fetchone()
    if avainsanaid==None:
        sql = "INSERT INTO photos_avainsanat (avainsana) VALUES (:avainsana) RETURNING id"
        avainsanaid = db.session.execute(sql, {"avainsana":avainsana}).fetchone()
        db.session.commit()
    return avainsanaid[0]

def getAllPersons():
    sql = "SELECT nimi FROM photos_henkilot"
    return db.session.execute(sql).fetchall()

def getAllKeywords():
    sql = "SELECT avainsana FROM photos_avainsanat"
    return db.session.execute(sql).fetchall()

def getAllUsers():
    sql = "SELECT tunnus FROM photos_kayttajat"
    return db.session.execute(sql).fetchall()