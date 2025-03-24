from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Transaction, PaymentProfile
from rich import print


@csrf_exempt
def dashboard(request):
    return render(request, "dashboard.html")


@csrf_exempt
def portal(request):
    print(f"Request Captured: {request}")
    return render(request, "payment.html")


@csrf_exempt
def processQuickPay(request):
    """Process a payment transaction"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        amount = payload.get("amount")
        cardDetails = payload.get("cardDetails")
        salesperson = payload.get("salesperson")
        customerDetails = payload.get("customerDetails")
        try:
            profile = PaymentProfile.objects.get(clientID=customerDetails["clientID"])
        except PaymentProfile.DoesNotExist:
            PaymentProfile.createPaymentProfile(
                firstName=customerDetails["firstName"],
                lastName=customerDetails["lastName"],
                address=customerDetails["address"],
                zipCode=customerDetails["zipCode"],
                companyName=customerDetails["companyName"],
                clientID=customerDetails.get("clientID"),
                createdBy=payload.get("salesperson", "System"),
            )
            profile = PaymentProfile.objects.get(clientID=customerDetails["clientID"])
            profile.addPaymentMethod(cardDetails=cardDetails)
        if not amount or not cardDetails or not salesperson:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        transactionResult = Transaction.processTransaction(
            amount=amount,
            cardDetails=cardDetails,
            clientId=customerDetails["clientID"],
            salesperson=salesperson,
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

        print(
            f"Received request with customer details: {json.dumps(customerDetails, indent=2)}"
        )

        if not customerDetails:
            return JsonResponse({"error": "Missing customer details"}, status=400)

        required_fields = [
            "firstName",
            "lastName",
            "address",
            "zipCode",
            "companyName",
        ]
        for field in required_fields:
            if field not in customerDetails:
                print(f"Validation failed: missing field {field}")
                return JsonResponse(
                    {"error": f"Missing required field: {field}"}, status=400
                )

        # Create profile
        print(
            f"Creating payment profile for {customerDetails['firstName']} {customerDetails['lastName']}"
        )
        profile_result = PaymentProfile.createPaymentProfile(
            firstName=customerDetails["firstName"],
            lastName=customerDetails["lastName"],
            address=customerDetails["address"],
            zipCode=customerDetails["zipCode"],
            companyName=customerDetails["companyName"],
            clientID=str(customerDetails.get("clientID")),
            createdBy=payload.get("salesperson", "System"),
        )

        # Check if profile creation was successful
        if not profile_result or not isinstance(profile_result, PaymentProfile):
            print(f"Profile creation failed. Result: {profile_result}")
            return JsonResponse(
                {
                    "error": "Failed to create customer profile in payment gateway",
                    "details": str(profile_result)
                    if profile_result
                    else "No response from payment gateway",
                },
                status=500,
            )

        profile = profile_result  # Use the returned profile object directly

        if not profile.customerProfileID:
            print("Profile created but no customerProfileID received")
            return JsonResponse(
                {
                    "error": "Customer profile created but no ID received from payment gateway"
                },
                status=500,
            )

        # Add payment method if provided
        if cardDetails:
            print(f"Adding payment method for profile {profile.customerProfileID}")
            payment_result = profile.addPaymentMethod(cardDetails)
            print(f"Payment method addition result: {payment_result}")
            if "error" in payment_result:
                return JsonResponse(
                    {
                        "profile": "created",
                        "customer_profile_id": profile.customerProfileID,
                        "payment_method": payment_result,
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "clientId": profile.clientID,
                "customer_profile_id": profile.customerProfileID,
            }
        )

    except json.JSONDecodeError:
        print("Invalid JSON received in request")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Unexpected error in create_customer_profile: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
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
            profile = PaymentProfile.objects.filter(clientID=clientID).first()
            if not profile:
                return JsonResponse({"error": "Customer profile not found"}, status=404)
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
            "address": profile.address,
            "zipCode": profile.zipCode,
            "customerProfileID": profile.customerProfileID,
            "paymentProfileID": profile.paymentProfileID,
            "status": profile.status,
            "created_at": profile.createdAt,
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


def getClients(request):
    clientList = []
    seen_clients = set()  # Track unique clientIDs

    # Get all profiles ordered by createdAt descending to get latest first
    clientObjs = PaymentProfile.objects.all().order_by("-createdAt")

    for obj in clientObjs:
        # If we haven't seen this clientID yet, add it to our list
        if obj.clientID not in seen_clients:
            seen_clients.add(obj.clientID)  # Mark this clientID as seen
            clientObj = {
                "clientID": str(obj.clientID),
                "companyName": str(obj.companyName),
                "address": str(obj.address),
                "createdAt": str(obj.createdAt),
            }
            clientList.append(clientObj)

    return JsonResponse(data={"rows": clientList})


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
