# PostgreSQL:n asennus ja kannan luonti

Asenna PostgreSQL osoitteesta: https://www.postgresql.org/download/ Valitse uusin versio, omani on 17.3.  
 
Tämän jälkeen seuraa tämän tutoriaalin ohjeita, alla olevin lisäyksin: https://stackpython.medium.com/how-to-start-django-project-with-a-database-postgresql-aaa1d74659d8  
Skippaa kohdat 1-5.  
Ennen kohtaa 6 aktivoi virtuaaliympäristö ja anna seuraava komento kansiossa Backend/:  
 
`pip install -r requirements.txt`  
 
Näiden jälkeen luo tietokanta tutoriaalin kohdan 6 perusteella.  
 
Tämän jälkeen luo .env niminen tiedosto kansioon Backend/Backend  
.env-tiedosto pitää näyttää tältä:  
 
SECRET_KEY=django-insecure-jx(y9kh31r=)w7h_sn^9av$04%u%2+9x$w%t2v$@zjn41it_x^  
DB_NAME=<kannan_nimi> #minulla instrumentRegistry   
DB_USER=<user_name> #oletuksena postgres   
DB_PASSWORD=<password> #salasana jonka määrittelit postgres käyttäjälle pg adminissa  
DB_HOST=localhost  
DB_PORT=5432  
 
Tämän jälkeen siirry kansioon Backend/ ja anna seuraava komento:  
`python manage.py migrate`
 
# Backend-komennot

Backend tukee seuraavia peruskomentoja (anna ne Backend/-hakemistossa virtuaaliympäristö aktivoituna):

`python manage.py migrate` - Vie muutokset migraatiotiedostoista tietokantaan. Ei tarpeellinen, ellei muutoksia tehdä alustuksen jälkeen.

`python manage.py runserver` - Käynnistää backendin manuaalisesti. Palvelimen tulisi aina käynnistää backend uudelleen, kun se käynnistetään uudelleen, päivitetään jne.

`python manage.py createsuperuser` - Luo admin-käyttäjän tietokantaan manuaalisesti. Tarpeellinen vain alkuperäisen admin-tilin luomiseen; loput voidaan luoda käyttöliittymän kautta rekisteröintikoodeilla.

`python manage.py export_csv` - Luo .csv-tiedoston hakemistoon /Backend, nimellä "laiterekisteri_YYYY-MM-DD.csv", joka sisältää tietokannan nykyisen sisällön.

`python manage.py import_csv <filename>` - Lukee .csv-tiedoston nimellä <filename> hakemistosta Backend ja vie sen tietokantaan. Tiedoston tulisi olla seuraavassa muodossa:

- Rivi 1 tulee olla seuraava rivi: tay_numero;tuotenimi;merkki_ja_malli;sarjanumero;yksikko;kampus;rakennus;huone;vastuuhenkilo;toimituspvm;toimittaja;lisatieto;vanha_sijainti;tarkistettu;huoltosopimus_loppuu;edellinen_huolto;seuraava_huolto;tilanne
- Loput rivit sisältävät tietoa muodossa <tieto>;<tieto>;<tieto>; ..., ensimmäisen rivin järjestyksessä, käyttäen ";"-merkkiä erottimena. Esimerkki: 6440;keskuskello;WESTERSTRAND KVARZ W 24 VDC;;Lääketieteen ja biotieteiden tie;Kauppi;Arvo;ARVO-B111;;;;;213;;2025-05-03;;2025-05-15;Tarkistamatta
