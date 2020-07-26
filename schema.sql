CREATE TABLE photos_kayttajat (id SERIAL PRIMARY KEY, tunnus TEXT, salasana TEXT, admin BOOLEAN);
CREATE TABLE photos_valokuvat (id SERIAL PRIMARY KEY, kayttaja_id INT, valokuvaaja_id INT, kuvausaika TIMESTAMP, paikka_id INT, tekstikuvaus TEXT, aikaleima TIMESTAMP);
