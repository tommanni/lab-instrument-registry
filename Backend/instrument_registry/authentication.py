from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import authenticate
"""
A class that is used to authenticate user credentials that are given in
JSON format
"""
class JSONAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        email = request.data.get('email', None)
        password = request.data.get('password', None)
        if (not email) or (not password):
            raise exceptions.AuthenticationFailed(('Missing credentials.'))
        user = authenticate(request=request, email=email, password=password)
        if not user:
            raise exceptions.AuthenticationFailed(('Invalid credentials.'))
        return (user, None)