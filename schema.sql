CREATE TABLE photos_kayttajat (id SERIAL PRIMARY KEY, tunnus TEXT, salasana TEXT, admin BOOLEAN);
CREATE TABLE photos_valokuvat (id SERIAL PRIMARY KEY, kayttaja_id INT, valokuvaaja_id INT, kuvausaika TIMESTAMP, paikka_id INT, tekstikuvaus TEXT, aikaleima TIMESTAMP);
CREATE TABLE photos_henkilot (id SERIAL PRIMARY KEY, nimi TEXT, syntymavuosi INT);
CREATE TABLE photos_valokuvienhenkilot (id SERIAL PRIMARY KEY, henkilo_id INT, valokuva_id INT);
CREATE TABLE photos_avainsanat (id SERIAL PRIMARY KEY, avainsana TEXT);
CREATE TABLE photos_valokuvienavainsanat (id SERIAL PRIMARY KEY, avainsana_id INT, valokuva_id INT);
