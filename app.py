from flask import Flask, request, session, render_template, redirect
from os import getenv, path, urandom
import re

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.version = "25.8.2020"

from db import db, get_all_persons, get_all_keywords, add_person_todb
import users, photos, places

parse_photoid = re.compile(r"photo(\d+)(_thmb)?\.jpg\Z")

@app.route("/")
def index():
    session["page"] = "/"
    return render_template("index.html")

@app.route("/login",methods=["GET"])
def login():
    session["page"] = "/login"
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def login_data():
    user = users.get_userdata(username=request.form["username"])
    if user == None:
        return render_template("login.html", message="VIRHE: tunnusta ei ole olemassa")
    if users.check_password(user[2],request.form["password"]):
        session["userid"] = int(user[0])
        session["username"] = user[1]
        session["csrf_token"] = urandom(16).hex()
        session["admin"] = user[3]
        session["filters"] = None
        session["filtersOthers"] = None
        return redirect("/view")
    return render_template("login.html", message="VIRHE: salasana on väärin")

@app.route("/signup",methods=["GET"])
def signup():
    session["page"]="/signup"
    return render_template("signup.html")

@app.route("/signup",methods=["POST"])
def signup_data():
    username = request.form["username"]
    password = request.form["password"]
    if username == "" or password == "":
        return render_template("signup.html", error="tunnus tai salasana ei voi olla tyhjä")
    if len(username)>10:
        return render_template("signup.html", error="käyttäjänimi on liian pitkä")
    if users.username_exists(username):
        return render_template("signup.html", error="tunnus on jo käytössä")
    id = users.new_user(username,password)
    return render_template("login.html", message="Uusi tunnus luotu")

@app.route("/view", methods=["GET"])
def view():
    session["page"] = "/view"
    if "userid" in session:
        photodata = photos.get_users_photos(session["userid"], f=session["filters"])
        persons = [photos.get_persons(photo[0])[0] for photo in photodata]
        keywords = [photos.get_keywords(photo[0])[0] for photo in photodata]
        return render_template("view.html", photos=list(zip(photodata,persons,keywords)), all_places=places.get_all_names(), 
            all_keywords=get_all_keywords(), all_persons=get_all_persons(), filters=session["filters"], count=len(photodata))
    else:
        return render_template("view.html")

@app.route("/view", methods=["POST"])
def view_data():
    if "userid" in session:
        if "reset" in request.form:
            session["filters"] = None
        else:
            session["filters"] = request.form
    return redirect("/view")

@app.route("/viewothers", methods=["GET"])
def viewothers():
    session["page"] = "/viewothers"
    if "filtersOthers" not in session:
        session["filtersOthers"] = None
    if "userid" in session:
        photodata = photos.get_others_photos(session["userid"], f=session["filtersOthers"])
    else:
        photodata = photos.get_others_photos(None, f=session["filtersOthers"])
    persons = [photos.get_persons(photo[0])[0] for photo in photodata]
    keywords = [photos.get_keywords(photo[0])[0] for photo in photodata]
    return render_template("viewothers.html", photos=list(zip(photodata, persons, keywords)), all_places=places.get_all_names(), 
        all_users=users.get_all_names(), all_keywords=get_all_keywords(), all_persons=get_all_persons(), filters=session["filtersOthers"])

@app.route("/viewothers", methods=["POST"])
def viewothers_data():
    if "reset" in request.form:
        session["filtersOthers"] = None
    else:
        session["filtersOthers"] = request.form
    return redirect("/viewothers")

@app.route("/upload", methods=["GET"])
def upload_photo():
    session["page"] = "/upload"
    return render_template("upload.html", all_places=places.get_all_names(), all_persons=get_all_persons())

@app.route("/upload", methods=["POST"])
def upload_photo_data():
    if not "userid" in session or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    images = request.files.getlist("photo")
    if len(images) == 1:
        image = images[0]
        if image.filename == "":
            return render_template("upload.html", message="Virhe: tiedostoa ei ole valittu")
        if not image.filename.lower().endswith(".jpg"):
            return render_template("upload.html", message="Virhe: vain JPG tiedostoja")
        id = photos.save_photo(session["userid"], image, places.add(request.form["place"]), add_person_todb(request.form["photographer"]))
    else:
        count = 0
        for image in images:
            if image.filename.lower().endswith(".jpg"):
                count += 1
                photos.save_photo(session["userid"], image, places.add(request.form["place"]), add_person_todb(request.form["photographer"]))
        return render_template("upload.html", all_places=places.get_all_names(), all_persons=get_all_persons(), message="Ladattiin "+str(count)+" kuvaa")
    return redirect("/addinfo/"+str(id))

@app.route("/addinfo/<int:id>", methods=["GET"])
def addinfo(id):
    if not users.check_permission_to_modify(session, id):
        return "Ei oikeuksia"

    photo_attributes = photos.get_attributes(id)
    if photo_attributes[1] == None:
        photographer = ""
    else:
        photographer = photo_attributes[1]

    if photo_attributes[3]:
        public = "checked"
    else:
        public = ""

    personstr,persons = photos.get_persons(id)
    keywordstr,keywords = photos.get_keywords(id)
    place = photos.get_place(id)
    permissionstr,permissions = photos.get_permissions(id)
    previous_page = session["page"]
    session["page"] = "/addinfo"
    if photo_attributes[0]!=None:
        date = photo_attributes[0].strftime("%Y-%m-%d")
        time = photo_attributes[0].strftime("%H:%M")
    else:
        date = None
        time = None
    return render_template("addinfo.html", photo_id=id, date=date, time=time, 
        description=photo_attributes[2], photographer=photographer, personstr=personstr, persons=persons, all_persons=get_all_persons(), 
        keywordstr=keywordstr, keywords=keywords, all_keywords=get_all_keywords(), place=place, all_places=places.get_all_names(), 
        public=public, permissionstr=permissionstr, permissions=permissions, users=users.get_all_names(), previous_page=previous_page)

@app.route("/addinfo/<int:id>", methods=["POST"])
def addinfo_data(id):
    if not users.check_permission_to_modify(session, id) or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    exitPage = True

    if request.form["date"] != "":
        datetime = request.form["date"] + " " + request.form["time"]
    else:
        datetime = None
    description = request.form["description"]
    if len(description) > 60:
        description = description[:60]
    public = "public" in request.form
    photographer_id = add_person_todb(request.form["photographer"])
    place_id = places.add(request.form["place"])

    if request.form["addPerson"] != "":
        photos.add_person(id, request.form["addPerson"])
        exitPage = False
    if request.form["removePerson"] != "":
        photos.remove_person(id, request.form["removePerson"])
        exitPage = False
    if request.form["addKeyword"] != "":
        photos.add_keyword(id, request.form["addKeyword"])
        exitPage = False
    if request.form["removeKeyword"] != "":
        photos.remove_keyword(id, request.form["removeKeyword"])
        exitPage = False
    if request.form["addPermission"] != "":
        photos.add_permission(id, request.form["addPermission"])
        exitPage = False
    if request.form["removePermission"] != "":
        photos.remove_permission(id, request.form["removePermission"])
        exitPage = False
    photos.update_attributes(id, datetime, description, photographer_id, place_id, public)
    if exitPage:
        if request.form["previous_page"] == "/upload":
            return redirect("/upload") 
        return redirect("/view")
    else:
        return redirect("/addinfo/"+str(id))

@app.route("/remove/<int:id>", methods=["GET"])
def remove(id):
    if not users.check_permission_to_modify(session, id):
        return "Ei oikeuksia"
    return render_template("remove.html", photo_id=id)

@app.route("/remove/<int:id>", methods=["POST"])
def remove_data(id):
    if not users.check_permission_to_modify(session, id) or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    if request.form["removephoto"]==session["csrf_token"]:
        photos.remove(id)
    return redirect("/view")

@app.route("/places", methods=["GET"])
def placelist():
    if not "userid" in session:
        return "Ei oikeuksia"
    session["page"] = "/places"
    placesdata = places.get_all()
    counts = [places.count(place[0]) for place in placesdata]
    return render_template("places.html", places=list(zip(placesdata,counts)))

@app.route("/place/<int:id>", methods=["GET"])
def place(id):
    if not "userid" in session:
        return "Ei oikeuksia"
    place = places.get_attributes(id)
    session["page"] = "/places"
    return render_template("place.html", place_id=id, place=place[0], city=place[1], country=place[2], region=place[3], wwwpage=place[4])

@app.route("/place/<int:id>", methods=["POST"])
def place_data(id):
    if not "userid" in session or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    places.update(id, request.form["country"], request.form["region"], request.form["city"], request.form["wwwpage"])
    return redirect("/places")

@app.route("/placeinfo/<int:id>", methods=["GET"])
def placeinfo(id):
    place = places.get_attributes(id)
    session["page"] = "/placeinfo"
    return render_template("placeinfo.html", place_id=id, place=place[0], city=place[1], country=place[2], region=place[3], wwwpage=place[4])

@app.route("/photos/<filename>")
def show_photo(filename):
    r = parse_photoid.match(filename)
    if r != None:
        if not users.check_permission_to_view(session, int(r.group(1))):
            return "Ei oikeuksia"
        return photos.get_image(filename)
    return "kuvaa ei ole"

@app.route("/logout")
def logout():
    del session["username"]
    del session["userid"]
    del session["csrf_token"]
    del session["admin"]
    del session["filters"]
    del session["filtersOthers"]
    session["page"]="/logout"
    return redirect("/")

@app.route("/help")
def help():
    session["page"] = "/help"
    return render_template("help.html", version=app.version)

@app.route("/admin", methods=["GET"])
def admin():
    if not "userid" in session or not session["admin"]:
        return "Ei oikeuksia"
    session["page"] = "/admin"
    userdata = users.get_all_data()
    return render_template("admin.html", users=userdata, count=len(userdata))

@app.route("/admin/removeuser/<int:id>", methods=["GET"])
def remove_user(id):
    if not session["admin"]:
        return "Ei oikeuksia"
    if users.isadmin(id):
        return "Pääkäyttäjän tunnusta ei voi poistaa"
    return render_template("removeuser.html", userdata=users.get_userdata(id=id))

@app.route("/admin/removeuser/<int:id>", methods=["POST"])
def remove_user_data(id):
    if not session["admin"] or session["csrf_token"] != request.form["csrf_token"]:
        return "Ei oikeuksia"
    if users.isadmin(id):
        return "Pääkäyttäjän tunnusta ei voi poistaa"
    if request.form["removeuser"]==session["csrf_token"]:
        users.remove(id)
        userphotos = photos.get_users_photos(id)
        for photo in userphotos:
            photos.remove(photo[0])
    return redirect("/admin")

@app.route("/admin/resetpassword/<int:id>", methods=["GET"])
def reset_password(id):
    if session["admin"] or session["userid"] == id:
        return render_template("resetpassword.html", userdata=users.get_userdata(id=id), admin=session["admin"] and not users.isadmin(id))
    return "Ei oikeuksia"

@app.route("/admin/resetpassword/<int:id>", methods=["POST"])
def reset_password_data(id):
    if (session["admin"] or session["userid"] == id) and session["csrf_token"] == request.form["csrf_token"]:
        users.set_password(request.form["newpassword"], id=id)
        if session["userid"] == id:
            return redirect("/view")
        return redirect("/admin")
    return "Ei oikeuksia"

@app.route("/admin/removeplace", methods=["POST"])
def remove_place_data():
    if session["admin"] and session["csrf_token"] == request.form["csrf_token"]:
        if places.count(request.form["placeid"])>0:
            return "Mikään kuva ei voi olla merkitty poistettavaan paikkaan"
        places.remove(request.form["placeid"])
        return redirect("/places")
    return "Ei oikeuksia"
