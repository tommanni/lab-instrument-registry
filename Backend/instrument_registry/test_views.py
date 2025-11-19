from django.test import TestCase
from parameterized import parameterized
from .models import InviteCode
from .serializers import RegistryUserSerializer
import json

class TestViewsWithoutLogin(TestCase):

    def test_instruments_view_status(self):
        response = self.client.get("/api/instruments/")
        self.assertEqual(response.status_code, 200)
    
    def test_empty_instruments_view(self):
        response = self.client.get("/api/instruments/")
        self.assertEqual(str(response.content), "b'[]'")

    @parameterized.expand([
        "yksikko",
        "huone",
        "kampus",
        "rakennus",
        "vastuuhenkilo",
        "tilanne"
    ])
    def test_get_filters_valid(self, filter: str):
        response = self.client.get("/api/instruments/valueset/" + filter + "/")
        self.assertEqual(str(response.content), 'b\'{"data":[]}\'')
    
    def test_get_filters_invalid(self):
        filter = "whatever"
        response = self.client.get("/api/instruments/valueset/" + filter + "/")
        self.assertEqual(str(response.content), 'b\'{"message":"no such field"}\'')

    @parameterized.expand([
        "/api/instruments/csv/preview/",
        "/api/users/",
        "/api/users/me/",
        '/api/invite/'
    ])
    def test_auth_views(self, url: str):
        response = self.client.post(url) if url == "/api/instruments/csv/preview/" else self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_register_view_invalid(self):
        response = self.client.post("/api/register/", data={"invite_code": "whatever"})
        self.assertEqual(str(response.content), 'b\'{"message":"invite code is invalid or missing."}\'')

    def test_register_view_valid(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={"invite_code": invite_code.code, "email": "a@a.com", "full_name": "aa aa", "password": "ValidPassword123"})
        self.assertEqual(str(response.content), 'b\'{"message":"user registered."}\'')


class TestLoginView(TestCase):

    logindata = {"email": "a@a.com", "full_name": "aaaaa", "password": "a"}

    @classmethod
    def setUpTestData(cls):
        
        serializer = RegistryUserSerializer(data=cls.logindata)
        serializer.is_valid()
        serializer.save()

    def test_login_view_valid(self):
        response = self.client.post("/api/login/", data=self.logindata)
        self.assertEqual(response.status_code, 200)
        # ensure token was removed from response json and user is present
        body = json.loads(response.content)
        self.assertNotIn('token', body)
        self.assertIn('user', body)
        # cookie should be set
        self.assertIn('Authorization', response.cookies)
        morsel = response.cookies['Authorization']
        # HttpOnly attribute should be present
        self.assertTrue(morsel['httponly'])
        # Max-Age should match 2 hours (7200 seconds)
        self.assertIn(morsel['max-age'], ('7200', 7200))

    def test_login_view_invalid_email(self):
        response = self.client.post("/api/login/", data={"email": "in@valid.com", "password": "anything"})
        self.assertEqual(str(response.content), 'b\'{"detail":"Invalid credentials."}\'')

    def test_login_view_invalid_password(self):
        response = self.client.post("/api/login/", data={"email": "a@a.com", "password": "wrong"})
        self.assertEqual(str(response.content), 'b\'{"detail":"Invalid credentials."}\'')

    def test_login_view_no_credentials(self):
        response = self.client.post("/api/login/")
        self.assertEqual(str(response.content), 'b\'{"detail":"Missing credentials."}\'')

class TestViewsSignedIn(TestCase):

    logindata = {"email": "a@a.com", "full_name": "aaaaa", "password": "a"}

    @classmethod
    def setUpTestData(cls):
        serializer = RegistryUserSerializer(data=cls.logindata)
        serializer.is_valid()
        serializer.save()
        # todo sign in
        # not possible to make requests in this method so need to figure out how to do this properly