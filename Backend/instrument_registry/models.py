from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import datetime, timedelta
from django.conf import settings
import string
import secrets

"""
The main model of the project. Corresponds to instruments that the customer is using.
The fields are based on the csv file that was used as the foundation of the project.
"""
class Instrument(models.Model):
    # allow blank because not all fields have data
    tay_numero = models.CharField(max_length=100, default="", blank=True)
    tuotenimi = models.CharField(max_length=100, default="", blank=True)
    merkki_ja_malli = models.CharField(max_length=100, default="", blank=True)
    sarjanumero = models.CharField(max_length=100, default="", blank=True)
    yksikko = models.CharField(max_length=100, default="", blank=True)
    kampus = models.CharField(max_length=100, default="", blank=True)
    rakennus = models.CharField(max_length=100, default="", blank=True)
    huone = models.CharField(max_length=100, default="", blank=True)
    vastuuhenkilo = models.CharField(max_length=100, default="", blank=True)
    toimituspvm = models.DateField(null=True, blank=True)
    toimittaja = models.CharField(max_length=100, default="", blank=True)
    lisatieto = models.CharField(max_length=1000, default="", blank=True)
    vanha_sijainti = models.CharField(max_length=100, default="", blank=True)
    tarkistettu = models.CharField(max_length=100, default="", blank=True)
    huoltosopimus_loppuu = models.DateField(null=True, blank=True)
    edellinen_huolto = models.DateField(null=True, blank=True)
    seuraava_huolto = models.DateField(null=True, blank=True)
    tilanne = models.CharField(max_length=100)
    history = HistoricalRecords()

# Manager model used for creating users
class RegistryUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **other_fields):
        if not email:
            raise ValueError('Email is mandatory!')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, full_name, password=None, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)
        return self.create_user(email, full_name, password, **other_fields)

# User model used for authentication
class RegistryUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    # add more fields if needed
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = RegistryUserManager()

# Manager model for handling of invite codes
class InviteCodeManager(models.Manager):
    def remove_expired_codes(self):
        self.model.objects.filter(expires__lt=datetime.now()).delete()
    
    def remove_code(self, code):
        self.model.objects.filter(code=code).delete()

    def is_valid_code(self, code):
        return self.model.objects.filter(code=code).exists()
    
    def validate_and_remove(self, code):
        self.remove_expired_codes()
        is_valid = self.is_valid_code(code)
        self.remove_code(code)
        return is_valid

# Model that is used in creation of new users
class InviteCode(models.Model):
    def default_expire_time():
        expire_delta = getattr(settings, 'INVITE_CODE_LIFETIME', timedelta(days=1))
        return datetime.now() + expire_delta

    def default_code():
        code_digits = getattr(settings, 'INVITE_CODE_DIGITS', 8)
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(code_digits))

    code = models.CharField(default=default_code, max_length=32)
    expires = models.DateTimeField(default=default_expire_time)

    objects = InviteCodeManager()
