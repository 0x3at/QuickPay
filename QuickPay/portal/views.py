from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Transaction, PaymentProfile
from rich import print

def dashboard(request):
    return render(request, "dashboard.html")

def portal(request):
    print(f"Request Captured: {request}")
    return render(request, "payment.html")


@csrf_exempt
def process_payment(request):
    """Process a payment transaction"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        amount = payload.get("amount")
        cardDetails = payload.get("cardDetails")
        salesperson = payload.get("salesperson")

        if not amount or not cardDetails or not salesperson:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        transactionResult = Transaction.processTransaction(
            amount, cardDetails, salesperson
        )
        print(f"Response: {transactionResult}")
        return JsonResponse(transactionResult)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def create_customer_profile(request):
    """Create a new customer profile"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        customerDetails = payload.get("customerDetails")
        cardDetails = payload.get("cardDetails", None)

        if not customerDetails:
            return JsonResponse({"error": "Missing customer details"}, status=400)

        required_fields = [
            "firstName",
            "lastName",
            "address",
            "zipCode",
            "email",
            "companyName",
        ]
        for field in required_fields:
            if field not in customerDetails:
                return JsonResponse(
                    {"error": f"Missing required field: {field}"}, status=400
                )

        # Create profile
        PaymentProfile.createPaymentProfile(
            firstName=customerDetails["firstName"],
            lastName=customerDetails["lastName"],
            address=customerDetails["address"],
            zipCode=customerDetails["zipCode"],
            email=customerDetails["email"],
            companyName=customerDetails["companyName"],
            clientID=customerDetails.get("clientID"),
            created_by=payload.get("salesperson", "System"),
        )
        profile = PaymentProfile.objects.get(clientID=customerDetails.get("clientID"))

        # Add payment method if provided
        if cardDetails and profile.customerProfileID:
            payment_result = profile.addPaymentMethod(cardDetails)
            if "error" in payment_result:
                return JsonResponse(
                    {"profile": "created", "payment_method": payment_result}
                )

        return JsonResponse(
            {
                "success": True,
                "clientId": profile.clientID,
                "customer_profile_id": profile.customerProfileID,
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def add_payment_method(request):
    """Add a payment method to an existing customer profile"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        clientID = payload.get("clientID")
        cardDetails = payload.get("cardDetails")

        if not clientID:
            return JsonResponse({"error": "Missing client ID"}, status=400)
        if not cardDetails:
            return JsonResponse({"error": "Missing card details"}, status=400)

        try:
            profile = PaymentProfile.objects.get(clientID=clientID)
        except PaymentProfile.DoesNotExist:
            return JsonResponse({"error": "Customer profile not found"}, status=404)

        result = profile.addPaymentMethod(cardDetails)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_customer_profile(request, client_id=None):
    """Get customer profile information"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not client_id:
        # Extract client_id from query parameters if not in URL
        client_id = request.GET.get("client_id")

    if not client_id:
        return JsonResponse({"error": "Missing client ID"}, status=400)

    try:
        profile = PaymentProfile.objects.get(clientID=client_id)
        profile_data = {
            "clientID": profile.clientID,
            "firstName": profile.firstName,
            "lastName": profile.lastName,
            "companyName": profile.companyName,
            "email": profile.email,
            "address": profile.address,
            "zipCode": profile.zipCode,
            "customerProfileID": profile.customerProfileID,
            "paymentProfileID": profile.paymentProfileID,
            "status": profile.status,
            "created_at": profile.created_at,
        }

        # If customer has a profile in Authorize.net, get additional details
        if profile.customerProfileID:
            auth_net_profile = PaymentProfile.getCustomerProfile(
                profile.customerProfileID
            )
            if (
                not isinstance(auth_net_profile, dict)
                or "error" not in auth_net_profile
            ):
                # Add any additional Authorize.net profile data if needed
                profile_data["auth_net_active"] = True

        return JsonResponse(profile_data)
    except PaymentProfile.DoesNotExist:
        return JsonResponse({"error": "Customer profile not found"}, status=404)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def process_profile_payment(request):
    """Process a payment using stored payment profile"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        clientID = payload.get("clientID")
        amount = payload.get("amount")
        invoiceID = payload.get("invoiceID", None)
        description = payload.get("description", None)

        if not clientID:
            return JsonResponse({"error": "Missing client ID"}, status=400)
        if not amount:
            return JsonResponse({"error": "Missing amount"}, status=400)

        try:
            profile = PaymentProfile.objects.get(clientID=clientID)
        except PaymentProfile.DoesNotExist:
            return JsonResponse({"error": "Customer profile not found"}, status=404)

        result = profile.chargeProfilePayment(amount, invoiceID, description)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
