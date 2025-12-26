from instrument_registry.models import Instrument, RegistryUser, InviteCode, InstrumentAttachment
from instrument_registry.serializers import InstrumentSerializer, InstrumentCSVSerializer, RegistryUserSerializer, InstrumentAttachmentSerializer
from instrument_registry.authentication import JSONAuthentication
from instrument_registry.util import model_to_csv, parse_date, should_translate_to_english, check_csv_duplicates, clean_whitespace
from instrument_registry.translations import translate_password_error
from instrument_registry.job_runner import run_precompute_subprocess
from simple_history.utils import bulk_create_with_history
from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from knox import views as knox_views
from knox.auth import TokenAuthentication
from django.http import HttpResponse, FileResponse
from django.conf import settings
from datetime import datetime
from django.db.models import Q
import csv
import io
import logging
from pgvector.django import CosineDistance
import requests
import json

logger = logging.getLogger(__name__)

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
    queryset = Instrument.objects.defer('embedding_en', 'enriched_description')
    serializer_class = InstrumentSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This view returns a single instrument.
class InstrumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Instrument.objects.defer('embedding_en', 'enriched_description')
    serializer_class = InstrumentSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# This view returns the history of a single instrument.
class InstrumentHistory(generics.RetrieveAPIView):
    queryset = Instrument.objects.defer('embedding_en', 'enriched_description')
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instrument = self.get_object()

        history_records = list(instrument.history.all().order_by('history_date'))

        if not history_records:
            return Response([])

        first_record = history_records[0]
        changes = []

        exclude_fields = ['embedding_fi', 'embedding_en', 'enriched_description']
        # Add first record as creation event
        changes.append({
            'history_date': first_record.history_date,
            'history_user': first_record.history_user.full_name if first_record.history_user else first_record.history_username,
            'history_type': first_record.get_history_type_display(),
            'changes': [
                {'field': f.name, 'old': None, 'new': getattr(first_record, f.name)}
                for f in first_record.instance._meta.get_fields()
                if f.concrete and not f.many_to_many and not f.auto_created and f.name not in exclude_fields
            ]
        })

        # Compare consecutive records and add diffs
        for i in range(len(history_records) - 1):
            current = history_records[i]
            next_record = history_records[i + 1]

            delta = next_record.diff_against(current)

            # Only add if there are actual changes (skip empty change events)
            if delta.changes:
                changes.append({
                    'history_date': next_record.history_date,
                    'history_user': next_record.history_user.full_name if next_record.history_user else next_record.history_username,
                    'history_type': next_record.get_history_type_display(),
                    'changes': [
                        {
                            'field': change.field,
                            'old': change.old,
                            'new': change.new
                        } for change in delta.changes
                    ]
                })

        # Add attachment history
        attachment_history = InstrumentAttachment.history.filter(
            instrument_id=instrument.id
        ).order_by('history_date')

        for att_record in attachment_history:
            history_type = att_record.get_history_type_display()
            user = att_record.history_user.full_name if att_record.history_user else att_record.history_username

            if history_type == 'Created':
                change_desc = f"Added attachment: {att_record.filename}"
            elif history_type == 'Deleted':
                change_desc = f"Deleted attachment: {att_record.filename}"
            else:
                change_desc = f"Modified attachment: {att_record.filename}"

            changes.append({
                'history_date': att_record.history_date,
                'history_user': user,
                'history_type': 'Attachment ' + history_type,
                'changes': [
                    {
                        'field': 'Attachment',
                        'old': None,
                        'new': change_desc
                    }
                ]
            })

        # Sort all changes by date
        changes.sort(key=lambda x: x['history_date'])

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
        instruments = Instrument.objects.defer('embedding_en', 'enriched_description')
        for i in instruments:
            unique_values.add(getattr(i, field_name))
        return Response({'data': list(unique_values)})

# This view returns all the data in Instrument table as a csv file.
class InstrumentCSVExport(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # only admins can export instruments
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'message': 'Not authorized.'}, status=403)

        now = datetime.now().strftime('%G-%m-%d')
        filename = 'laiterekisteri_' + now + '.csv'
        source = model_to_csv(InstrumentCSVSerializer, Instrument.objects.defer('embedding_en', 'enriched_description'))

        # Read the CSV content and add UTF-8 BOM for Excel compatibility
        csv_content = source.read()
        csv_bytes = '\ufeff' + csv_content  # Add UTF-8 BOM

        response = HttpResponse(csv_bytes.encode('utf-8'), content_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
        return response

# This view validates and previews CSV import before actually importing
class InstrumentCSVPreview(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        # only admins can import instruments
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'message': 'Not authorized.'}, status=403)

        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)

        csv_file = request.FILES['file']

        try:
            # Read and parse CSV
            content = csv_file.read().decode('utf-8-sig')
            csv_reader = csv.DictReader(io.StringIO(content), delimiter=';')
            rows = list(csv_reader)

            if not rows:
                return Response({'error': 'CSV file is empty'}, status=400)

            # Check for duplicates using shared helper function
            new_rows, duplicates, invalid_rows, new_count, duplicate_count, invalid_count = check_csv_duplicates(rows)

            return Response({
                'total_rows': len(rows),
                'new_count': new_count,
                'duplicate_count': duplicate_count,
                'invalid_count': invalid_count,
                'duplicates': duplicates,
                'invalid_rows': invalid_rows[:10],  # Show first 10 invalid rows
                'has_more_invalid': len(invalid_rows) > 10
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)


# This view actually imports the CSV after user confirmation
class InstrumentCSVImport(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # only admins can import instruments
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'message': 'Not authorized.'}, status=403)

        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)

        csv_file = request.FILES['file']
        duplicates_to_import_json = request.data.get('duplicates_to_import', '[]')

        try:
            duplicates_to_import = json.loads(duplicates_to_import_json)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid format for duplicates_to_import'}, status=400)

        try:
            # Read and parse CSV
            content = csv_file.read().decode('utf-8-sig')
            csv_reader = csv.DictReader(io.StringIO(content), delimiter=';')
            rows = list(csv_reader)

            if not rows:
                return Response({'error': 'CSV file is empty'}, status=400)

            # Filter out duplicates and invalid rows using shared helper function
            new_rows, _, _, _, _, _ = check_csv_duplicates(rows)

            # Combine new rows with selected duplicates
            rows_to_import = new_rows + duplicates_to_import

            if not rows_to_import:
                return Response({
                    'success': True,
                    'imported_count': 0,
                    'message': 'No new instruments to import'
                })

            # Clean the data (remove empty values and parse dates)
            date_fields = {'toimituspvm', 'huoltosopimus_loppuu', 'edellinen_huolto', 'seuraava_huolto'}
            data = []
            for row in rows_to_import:
                cleaned_row = {}
                for key, value in row.items():
                    trimmed_value = clean_whitespace(value)
                    if not trimmed_value:
                        continue
                    if key in date_fields:
                        parsed_value = parse_date(trimmed_value)
                        if parsed_value:
                            trimmed_value = parsed_value
                    cleaned_row[key] = trimmed_value
                data.append(cleaned_row)

            # Use Serializer for Validation & Cleaning
            serializer = InstrumentCSVSerializer(data=data, many=True)

            if not serializer.is_valid():
                return Response({'error': serializer.errors}, status=400)

            # Extract the cleaned data
            clean_rows = serializer.validated_data

            # Convert to Model Instances
            instrument_instances = [
                Instrument(**row)
                for row in clean_rows
            ]
            
            # Bulk create with simple history utility function
            if instrument_instances:
                bulk_create_with_history(instrument_instances, Instrument, batch_size=1000)    

            precompute_pid = None
            try:
                precompute_pid, log_path = run_precompute_subprocess(force=False) # Compute translations and embeddings
            except Exception as exc:
                logger.error(f'Embedding precompute subprocess failed: {exc}')

            return Response({
                'success': True,
                'imported_count': len(rows_to_import),
                'message': f'Successfully imported {len(rows_to_import)} instruments',
                'embedding_process_pid': precompute_pid,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)

# This view returns the status of translation and embedding processing
class EmbeddingStatus(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        pending_qs = Instrument.objects.filter(
            Q(embedding_en__isnull=True) &
            ~Q(tuotenimi_en__exact="Translation Failed")
        )
        pending_count = pending_qs.count()
        failed_count = Instrument.objects.filter(tuotenimi_en__exact="Translation Failed").count()
        return Response({
            'processing': pending_count > 0,
            'pending_count': pending_count,
            'failed_count': failed_count,
        })

# This view returns semantic search results
class InstrumentSearch(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    SERVICE_URL = getattr(settings, 'SEMANTIC_SERVICE_URL', 'http://semantic-search-service:8001')

    # Search term - search result cosine distance treshold
    # Distance of 0.0 is identical.
    MAX_DISTANCE_THRESHOLD = 0.5

    def get(self, request):
        search_term = request.query_params.get('q', '').strip()

        if not search_term:
            return Response({'message': 'search term not provided'}, status=400)

        embedding = self._fetch_query_embedding(search_term)

        if not embedding:
            return Response(
	            {'message': f'Failed to generate search embedding'},
	            status=500
            )

        # Start with base queryset
        instruments = (
            Instrument.objects
            .annotate(distance=CosineDistance('embedding_en', embedding))
            .filter(distance__lt=self.MAX_DISTANCE_THRESHOLD)
            .defer('embedding_en', 'enriched_description')
            .order_by('distance')[:60]
        )

        serializer = InstrumentSerializer(instruments, many=True)
        return Response(serializer.data)

    def _fetch_query_embedding(self, text):
        """
        Helper to handle the external semantic service logic.
        """
        try:
            # Determine endpoint and payload
            if should_translate_to_english(text):
                endpoint = f"{self.SERVICE_URL}/process_query"
                result_key = 'embedding_en'
            else:
                endpoint = f"{self.SERVICE_URL}/embed_query"
                result_key = 'embedding'

            response = requests.post(
                endpoint,
                json={"text": text},
                timeout=20.0
            )
            response.raise_for_status()

            payload = response.json()
            return payload.get(result_key)

        except requests.Timeout:
            logger.warning(f"Semantic search timeout for query: '{text}'")
            return None
        except requests.RequestException as e:
            logger.error(f"Semantic search connection error: {e}")
            return None
        except ValueError:
            logger.error("Semantic search returned invalid JSON")
            return None

class ServiceValueSet(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Instrument.objects.filter(
            Q(huoltosopimus_loppuu__isnull=False) |
            Q(seuraava_huolto__isnull=False) |
            Q(edellinen_huolto__isnull=False)
        ).defer('embedding_en', 'enriched_description')
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

    # Only admins can view the list of users
    def get(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied('Not authorized.')
        return super().get(request)

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
        request_user = self.request.user
        search_user = super().get_object()

        # only admins can view other users
        if not (request_user == search_user or request_user.is_staff or request_user.is_superuser):
            raise PermissionDenied("Not authorized.")

        return search_user


"""
Authentication related views
"""

# This view creates an invite code and returns it.
class GenerateInviteCode(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # only admins can create invite codes
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'message': 'Not authorized.'}, status=403)

        invite_code = InviteCode.objects.create()
        return Response({'invite_code': invite_code.code})

# This view allows for registering of new users using the invite code.
class Register(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.COOKIES.get('Language')
        password = request.data.get('password')
        password_again = request.data.get('password_again')
        invite_code = request.data.get('invite_code', None)

        validated = InviteCode.objects.is_valid_code(invite_code)

        if validated:
            email = request.data.get('email')
            full_name = request.data.get('full_name', '')
            user_candidate = RegistryUser(email=email, full_name=full_name)
            password_error = translate_password_error(password, password_again=password_again, lang=lang, user=user_candidate)
            if password_error:
                return Response({
                    'message': 'Error validating password.' if lang != 'fi' else 'Virhe salasanan vahvistuksessa.',
                    'password_error': password_error
                }, status=400)

            serializer = RegistryUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            InviteCode.objects.remove_code(invite_code)
            return Response({'message': 'user registered.'})
        else:
            if (lang == 'fi'):
                return Response({'message': 'kutsukoodi on virheellinen tai puuttuu.'}, status=400)
            return Response({'message': 'invite code is invalid or missing.'}, status=400)

# This view allows a logged in user to change their password.
class ChangePassword(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('id')
        new_password = request.data.get('new_password')
        lang = request.COOKIES.get('Language')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'message': 'User not found.'}, status=404)

        password_error = translate_password_error(password=new_password, lang=lang, user=user)
        if password_error:
            return Response({
                'message': 'Error validating password.' if lang != 'fi' else 'Virhe salasanan vahvistuksessa.',
                'password_error': password_error
            }, status=400)

        # only superadmins can change superadmin passwords
        if (not (request.user == user or request.user.is_staff or request.user.is_superuser)
            or (user.is_superuser and not request.user.is_superuser)):
            return Response({'message': 'Not authorized.'}, status=403)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password updated successfully.'})

# This view allows an superadmin user to add or remove admin rights to a user.
class ChangeAdminStatus(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # only superadmins can create new admins
        if not request.user.is_superuser:
            return Response({'message': 'Not authorized.'}, status=403)

        user_id = request.data.get('id')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'message': 'User not found.'}, status=404)

        if user.is_staff:
            user.is_staff = False
            user.is_superuser = False
            user.save()
            return Response({'message': 'Admin rights removed.', 'newAdminStatus': False})

        else:
            user.is_staff = True
            user.save()
            return Response({'message': 'Admin user created.', 'newAdminStatus': True})

# This view allows a superadmin user to add or remove superadmin rights to a user.
class ChangeSuperadminStatus(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # only superadmins can create new superadmins
        if not request.user.is_superuser:
            return Response({'message': 'Not authorized.'}, status=403)

        user_id = request.data.get('id')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'message': 'User not found.'}, status=404)

        if user.is_superuser:
            user.is_staff = False
            user.is_superuser = False
            user.save()
            return Response({'message': 'Admin rights removed', 'newSuperadminStatus': False})

        else:
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return Response({'message': 'Superadmin user created', 'newSuperadminStatus': True})

# This view allows a superadmin user to delete a user.
class DeleteUser(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # only superadmins can delete users
        if not request.user.is_superuser:
            return Response({'message': 'Not authorized.'}, status=403)

        user_id = request.data.get('id')

        try:
            user = RegistryUser.objects.get(pk=user_id)
        except RegistryUser.DoesNotExist:
            return Response({'message': 'User not found.'}, status=404)

        if user == request.user: # prevent self-deletion
            return Response({'message': 'You cannot delete your own account.'}, status=400)

        user.delete()

        return Response({'message': 'User deleted successfully.'})


# Attachment views
class InstrumentAttachmentList(APIView):
    """
    List all attachments for an instrument or upload a new attachment.
    Only authenticated users can view attachments.
    """
    authentication_classes = [CookieTokenAuthentication]

    def get_permissions(self):
        # All operations require authentication
        return [permissions.IsAuthenticated()]

    def get(self, request, instrument_id):
        """List all attachments for an instrument - only for authenticated users"""
        try:
            instrument = Instrument.objects.get(pk=instrument_id)
        except Instrument.DoesNotExist:
            return Response({'detail': 'Instrument not found.'}, status=404)

        attachments = InstrumentAttachment.objects.filter(instrument=instrument)
        serializer = InstrumentAttachmentSerializer(attachments, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, instrument_id):
        """Upload a new attachment"""
        try:
            instrument = Instrument.objects.get(pk=instrument_id)
        except Instrument.DoesNotExist:
            return Response({'detail': 'Instrument not found.'}, status=404)

        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided.'}, status=400)

        # Check disk space before accepting upload
        import shutil
        try:
            media_path = settings.MEDIA_ROOT
            disk_usage = shutil.disk_usage(media_path)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            if usage_percent >= 90:
                return Response({
                    'detail': 'Server storage is nearly full. Please contact IT support to resolve this issue before uploading files.'
                }, status=507)  # HTTP 507 Insufficient Storage
        except Exception as e:
            # If disk check fails, log but don't block upload
            print(f"Warning: Could not check disk space: {e}")

        # Validate file size using settings constant
        if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            return Response({'detail': 'File size exceeds 20MB limit.'}, status=400)

        # Create attachment
        attachment = InstrumentAttachment(
            instrument=instrument,
            file=file,
            filename=file.name,
            file_type=file.content_type,
            file_size=file.size,
            description=request.data.get('description', ''),
            uploaded_by=request.user if request.user.is_authenticated else None
        )
        attachment.save()

        serializer = InstrumentAttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data, status=201)


class InstrumentAttachmentDownload(APIView):
    """
    Download an attachment with Content-Disposition header to force download.
    Only authenticated users can download attachments.
    """
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Download an attachment"""
        try:
            attachment = InstrumentAttachment.objects.get(pk=pk)
        except InstrumentAttachment.DoesNotExist:
            return Response({'detail': 'Attachment not found.'}, status=404)

        if not attachment.file:
            return Response({'detail': 'File not found.'}, status=404)

        # Open the file
        file_handle = attachment.file.open('rb')

        # Create response with Content-Disposition header to force download
        response = FileResponse(file_handle, content_type=attachment.file_type or 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
        response['Content-Length'] = attachment.file_size

        return response


class InstrumentAttachmentDetail(APIView):
    """
    Retrieve, update, or delete an attachment.
    Only authenticated users can view attachments.
    """
    authentication_classes = [CookieTokenAuthentication]

    def get_permissions(self):
        # All operations require authentication
        return [permissions.IsAuthenticated()]

    def get(self, request, pk):
        """Retrieve an attachment - only for authenticated users"""
        try:
            attachment = InstrumentAttachment.objects.get(pk=pk)
        except InstrumentAttachment.DoesNotExist:
            return Response({'detail': 'Attachment not found.'}, status=404)

        serializer = InstrumentAttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update attachment description"""
        try:
            attachment = InstrumentAttachment.objects.get(pk=pk)
        except InstrumentAttachment.DoesNotExist:
            return Response({'detail': 'Attachment not found.'}, status=404)

        attachment.description = request.data.get('description', attachment.description)
        attachment.save()

        serializer = InstrumentAttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete an attachment"""
        try:
            attachment = InstrumentAttachment.objects.get(pk=pk)
        except InstrumentAttachment.DoesNotExist:
            return Response({'detail': 'Attachment not found.'}, status=404)

        # Delete the file from filesystem
        if attachment.file:
            try:
                attachment.file.delete()
            except Exception as e:
                # Log the error but continue with database deletion
                print(f"Error deleting file {attachment.filename}: {e}")

        # Delete the database record
        attachment.delete()

        return Response(status=204)


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
