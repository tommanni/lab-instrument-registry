"""
Production settings.
"""

from .base import *

""" 
Info for setting up the .env file with the key can be found in instructions
folder in file database.md
"""
SECRET_KEY = env("SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = ['met-metlabs.rd.tuni.fi', 'localhost', '127.0.0.1']