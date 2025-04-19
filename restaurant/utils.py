import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

def get_table_num_from_jwt(token):
    try:
        #print(f"Decoding token: {token}")  # Debug: Log token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        #print(f"Decoded payload: {payload}")  # Debug: Log decoded payload
        return payload.get("table_num")
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")
    except Exception as e:
        raise AuthenticationFailed(f"Token decoding error: {str(e)}")

def get_device_id_from_jwt(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        #print("exa", payload) 
        return payload.get("device_id")
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")