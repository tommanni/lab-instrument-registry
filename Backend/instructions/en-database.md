# Installation of PostgreSQL and creation of the database

Install PostgreSQL from the following url: https://www.postgresql.org/download/ Choose the newest version, mine is 17.3.  

Next follow this tutorial with the changes noted below: https://stackpython.medium.com/how-to-start-django-project-with-a-database-postgresql-aaa1d74659d8  
Skip parts 1-5.  
Before part 6 activate the virtual environment and give the following command inside folder Backend/:  
 
`pip install -r requirements.txt`  
 
After that create the database according to part 6 of the tutorial.  

Next create a file named .env in folder Backend/Backend/  
The contents of .env should look like this:   
 
SECRET_KEY=django-insecure-jx(y9kh31r=)w7h_sn^9av$04%u%2+9x$w%t2v$@zjn41it_x^  
DB_NAME=<name_of_db> #mine is instrumentRegistry   
DB_USER=<user_name> #default is postgres   
DB_PASSWORD=<password> #the password that you assigned to user postgres in pgAdmin  
DB_HOST=localhost  
DB_PORT=5432

Next move to folder Backend/ and give the following command:     
`python manage.py migrate`

## Backend Commands

The backends supports the following basic commands (give them under Backend/ with the virtual environment activated):

`python manage.py migrate` - Migrates changes from the migration files onto the database. Not necessary unless changes are made after initialization.

`python manage.py runserver` - Starts up the backend manually. The server should always reboot the backend upon being restarted, updated etc.

`python manage.py createsuperuser` - Manually creates an admin user into the database. Should only need to be used to create the original admin account; rest can be created using the UI with the sign-up codes.

`python manage.py export_csv` - Creates a .csv file under /Backend, of name "laiterekisteri_YYYY-MM-DD.csv", of the current database contents.

`python manage.py import_csv <filename>` - Reads a .csv file under Backend of name <filename> and imports it into the database. The file should be of format:

- Line 1 should contain the following line: "tay_numero;tuotenimi;merkki_ja_malli;sarjanumero;yksikko;kampus;rakennus;huone;vastuuhenkilo;toimituspvm;toimittaja;lisatieto;vanha_sijainti;tarkistettu;huoltosopimus_loppuu;edellinen_huolto;seuraava_huolto;tilanne"
- The rest of the lines should contains information in structure <information>;<information>;<information>; ..., in the order of the first line above, with ";" as the delimiter.
 