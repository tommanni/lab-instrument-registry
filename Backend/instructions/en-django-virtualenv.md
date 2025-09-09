## Activating and deactivating the virtual environment + Running Django

Using a command line tool move to the root of the project. (e.g. CMD when using Windows. I use Git Bash, which uses Linux commands even in Windows)

### On the first time:
This tutorial was made using Python 3.12.0.  
Create the virtual environment with the following command:  

**Windows**:  
  
    py -m venv virtualenv

**Linux**:  
  
    python -m venv virtualenv
 
#### !!! Next activate the virtual environment with the instructions a bit further down !!!
After activating install Django with the following command:  

**Windows**:  
 
    py -m pip install Django
 
**Linux**:  
  
    python -m pip install Django

Verify that the install succeeded with the command: 
 
    django-admin --version

If the response is some sort of a version number (e.g. 5.1.6) the installation was successful.  
 
### Activating and deactivating the virtual environment:  
**Windows**:  
Activation with the command: 
 
    virtualenv\Scripts\activate.bat
 
After activation you should see the text (virtualenv)on the command line.

Deactivation with the command: 

    virtualenv\Scripts\deactivate.bat
 
After that the command line returns to normal.
 
**Linux**:  

Activation with the command: 
   
    source virtualenv/Scripts/activate
 
After activation you should see the text (virtualenv)on the command line.

Deactivation with the command: 
    
    deactivate
 
After that the command line returns to normal.  
 
### Running the local Django server:  
After activating the virtual environment move to folder Backend/  
 
**The command on Windows**: 
    
    py manage.py runserver
 
**The command on Linux**: 
    
    python manage.py runserver

After the command you should see something in the url http://127.0.0.1:8000/  

 
Stop the server by pressing CTRL+C
 