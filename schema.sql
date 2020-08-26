CREATE TABLE photos_users (id SERIAL PRIMARY KEY, username TEXT, password TEXT, admin BOOLEAN);
CREATE TABLE photos_photos (id SERIAL PRIMARY KEY, user_id INT, photographer_id INT, datetime TIMESTAMP, place_id INT, description TEXT, timestamp TIMESTAMP, public BOOLEAN);
CREATE TABLE photos_persons (id SERIAL PRIMARY KEY, name TEXT, year INT);
CREATE TABLE photos_photopersons (id SERIAL PRIMARY KEY, person_id INT, photo_id INT);
CREATE TABLE photos_keywords (id SERIAL PRIMARY KEY, keyword TEXT);
CREATE TABLE photos_photokeywords (id SERIAL PRIMARY KEY, keyword_id INT, photo_id INT);
CREATE TABLE photos_jpgimages (id SERIAL PRIMARY KEY, filename TEXT, image BYTEA);
CREATE TABLE photos_places (id SERIAL PRIMARY KEY, place TEXT, country TEXT, region TEXT, city TEXT, wwwpage TEXT);
CREATE TABLE photos_permissions (id SERIAL PRIMARY KEY, photo_id INT, user_id INT);