# Valokuvien jakopalvelu

Aineopintojen harjoitustyö: Tietokantasovellus (loppukesä)

## Idea

Pavelun avulla käyttäjät voivat jakaa ja katsella valokuvia. Valokuviin voi liittää erinäisiä tietoja kuten niiden ottajia, paikkoja, henkilöitä ja ottamispäivämäärä.

## Tietokantataulukot

Käyttäjät

- kayttaja_id (SERIAL PRIMARY KEY)
- tunnus (TEXT)
- salansa (TEXT)
- admin (BOOLEAN)

Valokuvat

- valokuva_id (SERIAL PRIMARY KEY)
- kayttaja (kayttaja_id, INT)
- tiedostonimi (TEXT)
- valokuvaaja (henkilo_id, INT)
- päivämäärä (TIMESTAMP)
- paikka_id (INT)
- tekstikuvaus (TEXT)
- syöttämisen aikaleima (TIMESTAMP)

Henkilöt

- henkilo_id (SERIAL PRIMARY KEY)
- nimi (TEXT)
- syntymavuosi (INT)

Valokuvien_henkilöt

- Henkilö (henkilo_if, INT)
- Valokuva (valokuva_id, INT)

Avainsanat

- avainsana_id (SERIAL PRIMARY KEY)
- avainsana (TEXT)

Valokuvien_avainsanat

- Avainsana (avainsana_id, INT)
- Valokuva (valukuva_id, INT)

Paikat

- paikka_id (SERIAL PRIMARY KEY)
- paikannimi (TEXT)
- maa (TEXT)
- alue (TEXT)
- kaupunki/kunta (TEXT)
- long (INTEGER)
- lat (INTEGER)
- http-linkki (TEXT)

Oikeuksien_jako

- Valokuva (valokuva_id, INT)
- Kayttaja (kayttaja_id, INT)
