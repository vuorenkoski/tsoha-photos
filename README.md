# Valokuvien jakopalvelu

Aineopintojen harjoitustyö: Tietokantasovellus (loppukesä)

## Idea

Pavelun avulla käyttäjät voivat jakaa ja katsella valokuvia. Valokuviin voi liittää erinäisiä tietoja kuten niiden ottajia, paikkoja, henkilöitä ja ottamispäivämäärä.

## Sovelluksen nykytilanne

Sovellukseen on toteuttu kaikki päätoiminnallisuudet. Paljon on vielä yksityiskohtia hiottavana.

Toteutetut toiminnallisuudet:

- tunnuksen luominen
- sisään- ja uloskirjautuminen
- valokuvan tallentaminen
- omien kuvien katselu
- muiden jakamien kuvien katselu
- kuvan tietojen päivittäminen
- paikkojen tietojen päivittäminen
- Kuvien selaamiseen toiminnallisuus, jolla voi rajata listalle tulevat kuvat päivämäärän, paikan, avainsanojen ja/tai kuvassa esiintyvän henkilön mukaan.

Sovelluksesta vielä puutuu:

- kuvien lukumäärän näyttäminen
- useamman kuvaan lataamisessa "xx ladattu onnistuneesti"
- kunnolliset ohjeet
- Admin käyttäjälle mahdollisuus hallinnoida käyttäjätietoja ja muita tietoja
- Ulkoasun virittäminen paremmaksi

## Sovelluksen testaaminen

Sovellukseen voi testaamista varten voi luoda oman tunnuksen.


### Heroku

Herokussa voi testata osoitteessa: https://tsoha-photos.herokuapp.com/. 

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
- julkinen (BOOLEAN)

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
