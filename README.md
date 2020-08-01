# Valokuvien jakopalvelu

Aineopintojen harjoitustyö: Tietokantasovellus (loppukesä)

## Idea

Pavelun avulla käyttäjät voivat jakaa ja katsella valokuvia. Valokuviin voi liittää erinäisiä tietoja kuten niiden ottajia, paikkoja, henkilöitä ja ottamispäivämäärä.

## Sovelluksen nykytilanne

Sovellukseen on toteuttu kaikki päätoiminnallisuudet. Paljon on vielä yksityiskohtia hiottavana.

## Sovelluksen testaaminen

### Heroku

Herokussa voi testata osoitteessa: https://tsoha-photos.herokuapp.com/. Ongelmana tässä on se, että jpg kuvat tallennetaan sql taulukkoon, joka jostain syystä tyhjenee lyhyen ajan päästä. Sovellus toimii muuten herokussa ok, mutta kovat sis poistuvat jonkun ajan kuluttua.

### Omalla palvelimella

Sovelusta voi testata myös omalta palvelimeltani: https://www.vuorenkoski.fi:7443/


## Tietokantataulukot

Kayttajat

- kayttaja_id (SERIAL PRIMARY KEY)
- tunnus (TEXT)
- salansa (TEXT)
- admin (BOOLEAN)

Valokuvat

- valokuva_id (SERIAL PRIMARY KEY)
- kayttaja (kayttaja_id, INT)
- tiedostonimi (TEXT)
- valokuvaaja (henkilo_id, INT)
- kuvausaika (TIMESTAMP)
- paikka_id (INT)
- tekstikuvaus (TEXT)
- aikaleima (TIMESTAMP)

Henkilöt

- henkilo_id (SERIAL PRIMARY KEY)
- nimi (TEXT)
- syntymavuosi (INT)

Valokuvien_henkilöt

- henkilo (henkilo_id, INT)
- valokuva (valokuva_id, INT)

Avainsanat

- avainsana_id (SERIAL PRIMARY KEY)
- avainsana (TEXT)

Valokuvien_avainsanat

- avainsana (avainsana_id, INT)
- valokuva (valukuva_id, INT)

Paikat

- paikka_id (SERIAL PRIMARY KEY)
- paikannimi (TEXT)
- maa (TEXT)
- alue (TEXT)
- kaupunki_kunta (TEXT)
- http (TEXT)

Oikeudet

- valokuva (valokuva_id, INT)
- kayttaja (kayttaja_id, INT)
