from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import get_authorization_header
from restaurant.utils import get_table_num_from_jwt, get_device_id_from_jwt
from rest_framework.exceptions import AuthenticationFailed  # Import the exception here
from restaurant.models import Table

class DeviceJWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = get_authorization_header(request).decode('utf-8')

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Get table number and device id from the JWT token
                table_num = get_table_num_from_jwt(token)
                device_id = get_device_id_from_jwt(token)
                
                # Attach them to the request for further use
                request.table_num = table_num
                request.device_id = device_id
                
                try:
                    request.table = Table.objects.get(table_num=table_num, device_id=device_id)
                except Table.DoesNotExist:
                    raise AuthenticationFailed("Invalid table or device ID")

            except AuthenticationFailed as e:
                # Log and raise Authentication error in case of an invalid token
                print(f"JWT Error: {e}")
                raise e