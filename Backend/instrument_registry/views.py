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


"""
Instrument related views
"""
# This view returns all of the instruments in the database.
class InstrumentList(generics.ListCreateAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This view returns a single instrument.
class InstrumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This returns all the instruments that match the given filter
class InstrumentValueSet(APIView):
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        now = datetime.now().strftime('%G-%m-%d')
        filename = 'laiterekisteri_' + now + '.csv'
        source = model_to_csv(InstrumentCSVSerializer, Instrument.objects.all())
        response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
        copyfileobj(source, response)
        return response

class ServiceValueSet(APIView):
    authentication_classes = [TokenAuthentication]  # Add your authentication if needed
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

# This view returns a single user.
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RegistryUser.objects.all()
    serializer_class = RegistryUserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsSameUserOrReadOnly]
    
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

# This view creates an invite code and retunrs it.
class GenerateInviteCode(APIView):
    authentication_classes = [TokenAuthentication]
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

# These last views should be pretty self explanatory based on their names.
class Login(knox_views.LoginView):
    authentication_classes = [JSONAuthentication]
    permission_classes = [permissions.IsAuthenticated]

class Logout(knox_views.LogoutView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

class LogoutAll(knox_views.LogoutAllView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]