# Valokuvien jakopalvelu

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
- kayttaja (kayttaja_id)
- tiedostonimi (TEXT)
- valokuvaaja (henkilo_id)
- päivämäärä (DATE)
- paikka_id (INTEGER)
- tekstikuvaus (TEXT)
- syöttämisen aikaleima (DATE)

Henkilöt

- henkilo_id (SERIAL PRIMARY KEY)
- nimi (TEXT)
- syntymavuosi (INTEGER)

Valokuvien_henkilöt

- henkilo_id (INTEGER)
- valokuva_id (INTEGER)

Avainsanat

- avainsana_id (SERIAL PRIMARY KEY)
- avainsana (TEXT)

Valokuvien_avainsanat

- avainsana_id (INTEGER)
- valukuva_id (INTEGER)

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

- valokuva_id (INTEGER)
- kayttaja_id (INTEGER)
