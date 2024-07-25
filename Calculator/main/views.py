from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Number
from .serializers import NumberSerializer
import requests
import logging

logger = logging.getLogger(__name__)

class NumbersView(APIView):
    window_size = 10
    test_server_base_url = "http://20.244.56.144/test"
    auth_header = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzIxODg3NjI2LCJpYXQiOjE3MjE4ODczMjYsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6Ijc5YWE0NWZjLTIyYjgtNDI3Yi05MmE4LTg2ODJmYzlhOGRjMyIsInN1YiI6ImIyMWNzMDgxQGtpdHN3LmFjLmluIn0sImNvbXBhbnlOYW1lIjoiZ29NYXJ0IiwiY2xpZW50SUQiOiI3OWFhNDVmYy0yMmI4LTQyN2ItOTJhOC04NjgyZmM5YThkYzMiLCJjbGllbnRTZWNyZXQiOiJ6SmJPa0REeG9NeWJBTXR4Iiwib3duZXJOYW1lIjoiTWFydGhhIFNhaSBIYW5pdGgiLCJvd25lckVtYWlsIjoiYjIxY3MwODFAa2l0c3cuYWMuaW4iLCJyb2xsTm8iOiJCMjFDUzA4MSJ9.I_dn8H-P-dJ1TyyesywHpk1G2f7LanLLWIq6-JJBuO8' 
    }

    def get(self, request, id):
        endpoint_map = {
            'p': 'primes',
            'f': 'fib',
            'e': 'even',
            'r': 'rand'
        }

        test_server_endpoint = endpoint_map.get(id)
        if not test_server_endpoint:
            return Response({"error": "Invalid ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        numbers = self.fetch_numbers_from_test_server(test_server_endpoint)
        
        if numbers is None:
            return Response({"error": "Invalid request or timeout"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        prev_window = list(Number.objects.values_list('value', flat=True))
        self.update_window(numbers)
        curr_window = list(Number.objects.values_list('value', flat=True))
        avg = sum(curr_window) / len(curr_window) if curr_window else 0

        return Response({
            "numbers": numbers,
            "windowPrevstate": prev_window,
            "windowCurrstate": curr_window,
            "average": avg
        }, status=status.HTTP_200_OK)

    def fetch_numbers_from_test_server(self, endpoint):
        test_server_url = f"{self.test_server_base_url}/{endpoint}"
        try:
            response = requests.get(test_server_url, headers=self.auth_header, timeout=0.5)
            response.raise_for_status()
            data = response.json()
            numbers = data.get('numbers', [])
            if not numbers:
                logger.warning(f"No numbers returned from {test_server_url}")
            return list(set(numbers))  
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
        except ValueError as json_err:
            logger.error(f"JSON decode error: {json_err}")
        return None

    def update_window(self, numbers):
        unique_numbers = set(numbers)
        current_count = Number.objects.count()
        
        if current_count >= self.window_size:
            excess_count = current_count - self.window_size + len(unique_numbers)
            ids_to_delete = Number.objects.order_by('id')[:excess_count].values_list('id', flat=True)
            Number.objects.filter(id__in=ids_to_delete).delete()

        for num in unique_numbers:
            Number.objects.get_or_create(value=num)
