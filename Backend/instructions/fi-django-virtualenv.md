# Virtuaaliympäristön käynnistäminen ja sammuttaminen + Djangon käynnistys
Siirry jollain komentorivityökalulla projektin juureen. (esim CMD/Komentokehote Windowsilla, Linuxilla taitaa olla shell, mutta oletan Linux-käyttäjän osaavan käyttää komentoriviä. Itse käytän Windowsilla Git Bashiä, joka toimii Linuxin komennoilla.)

## Ensimmäisellä kerralla:
Itselläni on asennettuna Python versio 3.12.0.
Virtuaaliympäristö luodaan komennolla:

**Windows**:  
  
    py -m venv virtualenv

**Linux**:  
  
    python -m venv virtualenv
 
### !!! Tämän jälkeen käynnistä virtuaaliympäristö alla olevilla ohjeilla !!!
Sen jälkeen asenna Django komennolla:

**Windows**:  
 
    py -m pip install Django
 
**Linux**:  
  
    python -m pip install Django
 
Voit varmistaa asennuksen onnistuneen komennolla:
 
    django-admin --version

Jos saat vastaukseksi jonkin versionumeron (esim. 5.1.6) asennus onnistui.
 
## Virtuaaliympäristön käynnistys ja sammutus:
**Windows**:  
Käynnistys komennolla: 
 
    virtualenv\Scripts\activate.bat
 
Käynnistyksen jälkeen komentorivillä lukee (virtualenv) 

Sammutus komennolla: 

    virtualenv\Scripts\deactivate.bat
 
Jonka jälkeen komentorivi palaa normaalin näköiseksi.
 
**Linux**:  
Nämä esimerkit on tehty Windowsilla, Git Bashillä, Linux voi näyttää erilaiselta, mutta komennot ovat samoja.

Käynnistys komennolla: 
   
    source virtualenv/Scripts/activate
 
Käynnistyksen jälkeen komentorivillä lukee (virtualenv)

Sammutus komennolla: 
    
    deactivate
 
Jonka jälkeen komentorivi palaa normaalin näköiseksi.
 
## Django-serverin käynnistys:
Käynnistä ensin virtuaaliympäristö. Siirry seuraavaksi kansioon Backend/
 
**Komento Windowsilla**: 
    
    py manage.py runserver
 
**Komento Linuxilla**: 
    
    python manage.py runserver

Tämän jälkeen osoitteessa http://127.0.0.1:8000/ pitäisi näkyä jotain

 
Serverin saa pysäytettyä komentorivillä näppäinyhdistelmällä CTRL+C
 