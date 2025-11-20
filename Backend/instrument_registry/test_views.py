from django.test import TestCase
from parameterized import parameterized
from .models import InviteCode
from .serializers import RegistryUserSerializer

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


class TestRegisterView(TestCase):

    def test_register_view_password_mismatch(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "mismatch@example.com",
            "full_name": "Mismatch User",
            "password": "ValidPassword123",
            "password_again": "DifferentPassword123"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "Error validating password.")
        self.assertEqual(response.json().get("password_error"), "Passwords do not match")

    def test_register_view_password_too_short(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "short@example.com",
            "full_name": "Short Pass",
            "password": "short",
            "password_again": "short"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "Error validating password.")
        # Exact validator message may vary; assert translated mapping
        self.assertIn("Password", response.json().get("password_error", ""))

    def test_register_view_duplicate_email(self):
        # Create initial user
        serializer = RegistryUserSerializer(data={"email": "dup@example.com", "full_name": "Dup", "password": "ValidPassword123"})
        serializer.is_valid()
        serializer.save()
        # Attempt second registration with same email
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "dup@example.com",
            "full_name": "Dup 2",
            "password": "ValidPassword123",
            "password_again": "ValidPassword123"
        })
        self.assertEqual(response.status_code, 400)
        # Serializer error should include 'email' field
        self.assertIn("email", response.json())

    def test_register_view_removes_invite_code_on_success(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "remove@example.com",
            "full_name": "Invite Remove",
            "password": "ValidPassword123",
            "password_again": "ValidPassword123"
        })
        self.assertEqual(response.status_code, 200)
        # Invite code should be removed after successful registration
        from .models import InviteCode as InviteCodeModel
        self.assertFalse(InviteCodeModel.objects.filter(code=invite_code.code).exists())

    def test_register_view_password_entirely_numeric(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "numeric@example.com",
            "full_name": "Numeric Only",
            "password": "54394370018493123213123058919",
            "password_again": "54394370018493123213123058919"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "Error validating password.")
        self.assertEqual(response.json().get("password_error"), "Password cannot be entirely numeric")

    def test_register_view_password_too_common(self):
        invite_code = InviteCode.objects.create()
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": "common@example.com",
            "full_name": "Common Pass",
            "password": "password",
            "password_again": "password"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "Error validating password.")
        self.assertEqual(response.json().get("password_error"), "Password is too common")

    def test_register_view_password_too_similar_to_email(self):
        invite_code = InviteCode.objects.create()
        email = "johnsmith@example.com"
        # password very similar to part of email, should trigger similarity validator
        response = self.client.post("/api/register/", data={
            "invite_code": invite_code.code,
            "email": email,
            "full_name": "John Smith",
            "password": "johnsmith",
            "password_again": "johnsmith"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "Error validating password.")
        self.assertEqual(response.json().get("password_error"), "Password is too similar to the username")

    def test_register_view_invalid_invite_code_returns_400(self):
        # All fields valid except invite_code
        response = self.client.post("/api/register/", data={
            "invite_code": "INVALIDCODE",
            "email": "valid@example.com",
            "full_name": "Valid User",
            "password": "ValidPassword123",
            "password_again": "ValidPassword123"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("message"), "invite code is invalid or missing.")

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