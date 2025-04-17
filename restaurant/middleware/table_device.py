from restaurant.models import Table
from django.http import JsonResponse

class TableDeviceMiddleware:
    """Middleware to add the table to the request object based on device-id"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        device_id = request.headers.get('device-id')

        if device_id:
            try:
                table = Table.objects.get(device_id=device_id)
                request.table = table  # Associe la table à la requête
            except Table.DoesNotExist:
                request.table = None  # Si aucune table n'est trouvée, attribut `table` reste `None`
        else:
            request.table = None  # Si aucun device-id n'est présent, attribut `table` est `None`

        response = self.get_response(request)
        return response
