from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Transaction
from rich import print

def portal(request):
    print(f"Request Captured: {request}")
    return render(request, 'index.html')


@csrf_exempt  # Consider using proper CSRF protection in production
def process(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            # Parse JSON data from request body
            amount = payload.get("amount")
            number = payload.get("number")
            expiration = payload.get("expiration")
            cvv = payload.get("cvv")
            salesperson = payload.get("salesperson")
            response = Transaction.processTransaction(
                amount, number, expiration, cvv, salesperson
            )
            print(f"Response: {response}")
            return JsonResponse(response)

        except json.JSONDecodeError as e:
            print(f"Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    # For GET requests, render the payment form
    if request.method == "GET":
        return render(request, 'portal/index.html')

    # Only accept POST or GET requests
    return JsonResponse({"error": "Method not allowed"}, status=405)
