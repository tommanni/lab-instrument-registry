from instrument_registry.models import Instrument, RegistryUser, InviteCode
from instrument_registry.serializers import InstrumentSerializer, InstrumentCSVSerializer, RegistryUserSerializer
from instrument_registry.authentication import JSONAuthentication
from instrument_registry.permissions import IsSameUserOrReadOnly
from instrument_registry.util import model_to_csv
from rest_framework.views import APIView
from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from knox import views as knox_views
from knox.auth import TokenAuthentication
from django.http import HttpResponse
from datetime import datetime
from shutil import copyfileobj
from knox.views import LoginView as KnoxLoginView
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# Custom authentication class to handle login tokens in HttpOnly cookies
class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('Authorization')
        if not token:
            return None
        else:
            return self.authenticate_credentials(token.encode('utf-8'))

"""
Instrument related views
"""
# This view returns all of the instruments in the database.
class InstrumentList(generics.ListCreateAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This view returns a single instrument.
class InstrumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This view returns the history of a single instrument.
class InstrumentHistory(generics.RetrieveAPIView):
    queryset = Instrument.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instrument = self.get_object()
        
        history_records = list(instrument.history.all().order_by('history_date'))

        if not history_records:
            return Response([])

        first_record = history_records[0]
        changes = []
        # Add first record as creation event
        changes.append({
            'history_date': first_record.history_date,
            'history_user': first_record.history_user.full_name if first_record.history_user else None,
            'history_type': first_record.get_history_type_display(),
            'changes': [
                {'field': f.name, 'old': None, 'new': getattr(first_record, f.name)}
                for f in first_record.instance._meta.get_fields()
                if f.concrete and not f.many_to_many and not f.auto_created
            ]
        })
        
        # Compare consecutive records and add diffs
        for i in range(len(history_records) - 1):
            current = history_records[i]
            next_record = history_records[i + 1]
            
            delta = next_record.diff_against(current)
            changes.append({
                'history_date': next_record.history_date,
                'history_user': next_record.history_user.full_name if next_record.history_user else None,
                'history_type': next_record.get_history_type_display(),
                'changes': [
                    {
                        'field': change.field,
                        'old': change.old,
                        'new': change.new
                    } for change in delta.changes
                ]
            })
        
        return Response(changes)

# This returns all the instruments that match the given filter
class InstrumentValueSet(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, field_name):
        field_names = [f.name for f in Instrument._meta.get_fields()]
        if field_name not in field_names:
            return Response({'message': 'no such field'}, status=400)
        unique_values = set()
        instruments = Instrument.objects.all()
        for i in instruments:
            unique_values.add(getattr(i, field_name))
        return Response({'data': list(unique_values)})

# This view returns all the data in Instrument table as a csv file.
class InstrumentCSV(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        now = datetime.now().strftime('%G-%m-%d')
        filename = 'laiterekisteri_' + now + '.csv'
        source = model_to_csv(InstrumentCSVSerializer, Instrument.objects.all())
        response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
        copyfileobj(source, response)
        return response

class ServiceValueSet(APIView):
    authentication_classes = [CookieTokenAuthentication]  # Add your authentication if needed
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Instrument.objects.filter(
            Q(huoltosopimus_loppuu__isnull=False) | 
            Q(seuraava_huolto__isnull=False) | 
            Q(edellinen_huolto__isnull=False)
        )
        serializer = InstrumentSerializer(queryset, many=True)
        return Response(serializer.data)

"""
User related views
"""

# This view returns all the users.
class UserList(generics.ListAPIView):
    queryset = RegistryUser.objects.all()
    serializer_class = RegistryUserSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

# This view returns a single user.
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RegistryUser.objects.all()
    serializer_class = RegistryUserSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # if the URL argument is 'me', return logged in user
        id = self.kwargs.get(self.lookup_field)
        if str(id) == 'me':
            return self.request.user
        # otherwise use default functionality (search by pk)
        return super().get_object()


"""
Authentication related views
"""

# This view creates an invite code and returns it.
class GenerateInviteCode(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invite_code = InviteCode.objects.create()
        return Response({'invite_code': invite_code.code})

# This view allows for registering of new users using the invite code.        
class Register(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        invite_code = request.data.get('invite_code', None)
        validated = InviteCode.objects.validate_and_remove(invite_code)
        if validated:
            serializer = RegistryUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'user registered'})
        else:
            return Response({'message': 'invite code invalid or missing'}, status=400)

# This view allows a logged in user to change their password.
class ChangePasswordView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user_id = request.data.get('id')
        new_password = request.data.get('new_password')
        
        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)

        #try:
        #    validate_password(new_password, user=user)
        #except ValidationError as e:
        #    return Response({'errors': e.messages}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password updated successfully.'})

# This view allows an admin user to add or remove admin rights to a user.
class ChangeAdminStatus(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser: # only superusers can create new admins
            return Response({'detail': 'Not authorized.'}, status=403)

        user_id = request.data.get('id')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        
        if user.is_superuser:
            user.is_staff = False
            user.is_superuser = False
            user.save()
            return Response({'message': 'Admin rights removed', 'newAdminStatus': False})

        else:
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return Response({'message': 'Admin user created', 'newAdminStatus': True})

# This view allows an admin user to inactivate or activate a user.
class ChangeActiveStatus(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser: # only superusers can inactivate/activate users
            return Response({'detail': 'Not authorized.'}, status=403)

        user_id = request.data.get('id')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        
        if user.is_active:
            user.is_active = False
            user.save()
            return Response({'message': 'User made inactive', 'newActiveStatus': False})

        else:
            user.is_active = True
            user.save()
            return Response({'message': 'User made active', 'newActiveStatus': True})

# These last views should be pretty self explanatory based on their names.
class Login(knox_views.LoginView):
    authentication_classes = [JSONAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        response = super().post(request, format=None)

        token = response.data.get('token')
        print("Token from Knox:", token)

        # Remove token from JSON response for added security
        response.data.pop('token', None)

        response.set_cookie(
            key='Authorization',
            value=token,
            httponly=True,
            #secure=True,        todo: Add secure=true and samesite for live build!!!
            #samesite='Strict',  
            max_age=2 * 60 * 60      # 2h, same as knox token
        )
        print("Set cookie with token:", token)
        return response

class Logout(knox_views.LogoutView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        response = super().post(request, format=None)

        # Delete the cookie
        response.delete_cookie('Authorization')
        return response

class LogoutAll(knox_views.LogoutAllView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
