
import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from restaurant.models import Table  

class DeviceJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        #print("All headers:", request.headers)
        auth_header = request.headers.get('Authorization')
        #print(f"Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            #print(f"Decoded payload: {payload}")
            
            table = Table.objects.get(
                table_num=payload["table_num"],
                device_id=payload["device_id"]
            )
            
            return (table, {'device_id': payload["device_id"]})
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")
        except Table.DoesNotExist:
            raise AuthenticationFailed("Table not found or device ID mismatch")
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise AuthenticationFailed("Authentication failed")