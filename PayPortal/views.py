import json
import traceback

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rich import print
from rich.panel import Panel

from PayPortal.models import (
    AuthNetInterface,
    CardBillingDetails,
    CardDetails,
    Client,
    PaymentProfile,
)


@csrf_exempt
def chargeCard(request) -> JsonResponse:
    """Charge a card"""
    if request.method != "POST":
        print(Panel(
            f"[bold red]Received invalid {request.method} request instead of POST[/bold red]",
            title="❌[ERROR] |chargeCard| Method Error",
            border_style="bright_red"
        ))
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        print(Panel(
            "[bold bright_blue]Processing card charge request[/bold bright_blue]",
            title="🔎[INFO] |chargeCard| Payment Processing",
            border_style="bright_blue"
        ))
        
        payload = json.loads(request.body)
        clientID = payload.get("clientID")
        amount = payload.get("amount")
        cardDetails = payload.get("cardDetails")
        salesperson = payload.get("salesperson")
        
        # Validate required fields
        if not clientID:
            print(Panel(
                "[bold red]Missing clientID in request[/bold red]",
                title="❌[ERROR] |chargeCard| Validation Error",
                border_style="bright_red"
            ))
            return JsonResponse({"error": "Missing clientID"}, status=400)
            
        if not amount:
            print(Panel(
                "[bold red]Missing amount in request[/bold red]",
                title="❌[ERROR] |chargeCard| Validation Error",
                border_style="bright_red"
            ))
            return JsonResponse({"error": "Missing amount"}, status=400)
            
        if not cardDetails:
            print(Panel(
                "[bold red]Missing card details in request[/bold red]",
                title="❌[ERROR] |chargeCard| Validation Error",
                border_style="bright_red"
            ))
            return JsonResponse({"error": "Missing card details"}, status=400)
            
        if not salesperson:
            print(Panel(
                "[bold red]Missing salesperson in request[/bold red]",
                title="❌[ERROR] |chargeCard| Validation Error",
                border_style="bright_red"
            ))
            return JsonResponse({"error": "Missing salesperson"}, status=400)
        
        print(Panel(
            f"[bold yellow]Preparing transaction\nClient ID: {clientID}\nAmount: ${amount}\nSalesperson: {salesperson}[/bold yellow]",
            title="|chargeCard| Transaction Details",
            border_style="yellow"
        ))
        
        cardDetails = CardDetails(**cardDetails)
        
        print(Panel(
            "[bold bright_blue]Submitting payment to payment processor[/bold bright_blue]",
            title="🔎[INFO] |chargeCard| Payment Submission",
            border_style="bright_blue"
        ))

        txResult = AuthNetInterface.processCardTransaction(
            amount=amount, cardDetails=cardDetails, clientID=clientID, salesperson=salesperson
        )
        
        # Check if transaction was successful
        if "error" not in txResult or not txResult["error"]:
            print(Panel(
                f"[bold green]Transaction processed successfully\nTransaction ID: {txResult.get('transId', 'N/A')}\nAmount: ${amount}[/bold green]",
                title="❎[SUCCESS] |chargeCard| Payment Success",
                border_style="bright_green"
            ))
        else:
            print(Panel(
                f"[bold red]Transaction failed\nError: {txResult.get('error', 'Unknown')}\nError text: {txResult.get('errorText', 'No additional details')}[/bold red]",
                title="❌[ERROR] |chargeCard| Payment Error",
                border_style="bright_red"
            ))

        return JsonResponse(
            {"success": True, "transactionResult": txResult}, status=200
        )

    except json.JSONDecodeError:
        print(Panel(
            "[bold red]Invalid JSON received in request[/bold red]",
            title="❌[ERROR] |chargeCard| JSON Error",
            border_style="bright_red"
        ))
        return JsonResponse({"error": "Invalid JSON"}, status=400)
        
    except Exception as e:
        print(Panel(
            f"[bold red]Unexpected error in chargeCard: {str(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
            title="❌[ERROR] |chargeCard| System Error",
            border_style="bright_red"
        ))
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


@csrf_exempt
def getClient(request) -> JsonResponse:
    """Get all client profiles"""
    if request.method != "GET":
        print(
            Panel(
                f"[bold red]Received invalid {request.method} request instead of GET[/bold red]",
                title="❌[ERROR] |getClient| Method Error",
                border_style="bright_red",
            )
        )
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        print(
            Panel(
                "[bold bright_blue]Processing request to get client(s)[/bold bright_blue]",
                title="🔎[INFO] |getClient| Client List Request",
                border_style="bright_blue",
            )
        )
        try:
            payload = json.loads(request.body)
            clientID = payload.get("clientID")
        except json.JSONDecodeError:
            print(
                Panel(
                    "[bold red]No payload provided[/bold red]",
                    title="🔎[INFO] |getClient| No Payload",
                    border_style="bright_red",
                )
            )
            clientID = None
            pass
        if not clientID:
            clients = Client.getClient()
        else:
            client = Client.getClient(clientID if isinstance(clientID, int) else int(clientID))
            print(
                Panel(
                    "[bold green]Successfully retrieved client[/bold green]",
                    title="❎[SUCCESS] |getClient| Client List Success",
                    border_style="bright_green",
                )
            )
            return JsonResponse( client, status=200)
        print(
            Panel(
                "[bold green]Successfully retrieved client(s)[/bold green]",
                title="❎[SUCCESS] |getClient| Client List Success",
                border_style="bright_green",
            )
        )

        return JsonResponse({"clients": clients}, status=200)

    except Exception as e:
        print(
            Panel(
                f"[bold red]Error retrieving client list: {str(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
                title="❌[ERROR] |getClient| Client List Error",
                border_style="bright_red",
            )
        )
        return JsonResponse(
            {"error": "Failed to retrieve client list", "details": str(e)}, status=500
        )


# Create your views here.
@csrf_exempt
def createClientProfile(request) -> JsonResponse:
    """Create a new customer profile"""
    if request.method != "POST":
        print(
            Panel(
                f"[bold red]Received invalid {request.method} request instead of POST[/bold red]",
                title="❌[ERROR] |createClientProfile| Method Error",
                border_style="bright_red",
            )
        )
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        clientDetails = payload.get("clientDetails")
        print(
            Panel(
                f"[bold bright_blue]Received request with customer details: {json.dumps(clientDetails, indent=2)}[/bold bright_blue]",
                title="🔎[INFO] |createClientProfile| Request Details",
                border_style="bright_blue",
            )
        )

        if not clientDetails:
            print(
                Panel(
                    "[bold red]Missing client details in request[/bold red]",
                    title="❌[ERROR] |createClientProfile| Validation Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse({"error": "Missing client details"}, status=400)

        requiredFields = [
            "clientID",
            "companyName",
            "phone",
            "salesperson",
            "email",
        ]
        for field in requiredFields:
            if field not in clientDetails:
                print(
                    Panel(
                        f"[bold red]Validation failed: missing field {field}[/bold red]",
                        title="❌[ERROR] |createClientProfile| Validation Error",
                        border_style="bright_red",
                    )
                )
                return JsonResponse(
                    {"error": f"Missing required field: {str(field)}"}, status=400
                )

        # Create profile
        print(
            Panel(
                f"[bold green]Calling createClientProfile for [CID:{clientDetails['clientID']}]Company:{clientDetails['companyName']}[/bold green]",
                title="🔎[INFO] |createClientProfile| Profile Creation",
                border_style="bright_blue",
            )
        )
        client = Client.createClientProfile(
            companyName=clientDetails["companyName"],
            clientID=int(clientDetails.get("clientID")),
            phone=clientDetails["phone"],
            salesperson=clientDetails["salesperson"],
            email=clientDetails["email"],
        )

        # Check if profile creation was successful
        if not client or not isinstance(client, Client):
            print(
                Panel(
                    f"[bold red]Profile creation failed. Result: {client}[/bold red]",
                    title="❌[ERROR] |createClientProfile| Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse(
                {
                    "error": "Failed to create client profile",
                    "details": str(client)
                    if client
                    else "No response from payment gateway",
                },
                status=500,
            )

        if not client.customerProfileID:
            print(
                Panel(
                    "[bold red]Profile created but no clientID received[/bold red]",
                    title="❌[ERROR] |createClientProfile| Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse(
                {
                    "error": "Client profile created but no ID received from payment gateway"
                },
                status=500,
            )

        cardDetails = payload.get("cardDetails", None)
        billingDetails = payload.get("billingDetails", None)
        # Add payment method if provided
        if cardDetails is None:
            print(
                Panel(
                    "[bold green]Profile created successfully without payment method[/bold green]",
                    title="❎[SUCCESS] |createClientProfile| Success",
                    border_style="bright_green",
                )
            )
            return JsonResponse(
                data={
                    "success": True,
                    "clientId": str(client.clientID),
                    "customerProfileID": str(client.customerProfileID),
                },
                status=200,
            )
        if cardDetails is not None and billingDetails is not None:
            print(
                Panel(
                    f"[bold bright_blue]Adding payment method for profile {client.clientID}[/bold bright_blue]",
                    title="🔎[INFO] |createClientProfile| Payment Method",
                    border_style="bright_blue",
                )
            )
            cardDetails = CardDetails(**cardDetails)
            billingDetails = CardBillingDetails(**billingDetails)
            payment = PaymentProfile.addPaymentMethod(
                client=client, cardDetails=cardDetails, billingDetails=billingDetails
            )
            if isinstance(payment, PaymentProfile) and payment.status == "Active":
                print(
                    Panel(
                        f"[bold green]Payment method addition result: {payment.status}[/bold green]",
                        title="❎[SUCCESS] |createClientProfile| Success",
                        border_style="bright_green",
                    )
                )
                return JsonResponse(
                    {
                        "success": True,
                        "clientId": str(client.clientID),
                        "customerProfileID": str(client.customerProfileID),
                        "paymentMethodStatus": str(payment.status),
                    },
                    status=200,
                )
            else:
                print(
                    Panel(
                        "[bold red]Payment method addition failed[/bold red]",
                        title="❌[ERROR] |createClientProfile| Payment Error",
                        border_style="bright_red",
                    )
                )
                return JsonResponse(
                    {
                        "success": False,
                        "clientId": str(client.clientID),
                        "customerProfileID": str(client.customerProfileID),
                        "paymentMethodStatus": str(payment["error"]),  # type: ignore
                    },
                    status=500,
                )

    except json.JSONDecodeError:
        print(
            Panel(
                "[bold red]Invalid JSON received in request[/bold red]",
                title="❌[ERROR] |createClientProfile| JSON Error",
                border_style="bright_red",
            )
        )
        return JsonResponse(
            {"errorMessage": "Invalid JSON", "error": "JSONDecodeError"}, status=400
        )
    except Exception as e:
        print(
            Panel(
                f"[bold red]Unexpected error in createClientProfile: {str(e)}\nError type: {type(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
                title="❌[ERROR] |createClientProfile| Critical Error",
                border_style="bright_red",
            )
        )
        return JsonResponse(
            {"errorMessage": "An unexpected error occurred", "error": str(e)},
            status=500,
        )

    # Catch all other unexpected Issues
    print(
        Panel(
            "[bold red]Hit unhandled base case - this should never happen[/bold red]",
            title="❌[ERROR] |createClientProfile| Unhandled Case",
            border_style="bright_red",
        )
    )
    return JsonResponse(
        {
            "errorMessage": "An unexpected error occurred",
            "error": "Unhandled Base Case",
        },
        status=500,
    )


@csrf_exempt
def addPaymentMethod(request) -> JsonResponse:
    """Add a payment method to a client profile"""
    if request.method != "POST":
        print(
            Panel(
                f"[bold red]Received invalid {request.method} request instead of POST[/bold red]",
                title="❌[ERROR] |addPaymentMethod| Method Error",
                border_style="bright_red",
            )
        )
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        clientID = payload.get("clientID")
        cardDetails = payload.get("cardDetails")
        billingDetails = payload.get("billingDetails")

        print(
            Panel(
                f"[bold bright_blue]Processing payment method addition request for clientID: {clientID}[/bold bright_blue]",
                title="🔎[INFO] |addPaymentMethod| Payment Request",
                border_style="bright_blue",
            )
        )

        # Validate required fields
        if not clientID:
            print(
                Panel(
                    "[bold red]Missing clientID in request[/bold red]",
                    title="❌[ERROR] |addPaymentMethod| Validation Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse({"error": "Missing clientID"}, status=400)

        if not cardDetails:
            print(
                Panel(
                    "[bold red]Missing card details in request[/bold red]",
                    title="❌[ERROR] |addPaymentMethod| Validation Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse({"error": "Missing card details"}, status=400)

        if not billingDetails:
            print(
                Panel(
                    "[bold red]Missing billing details in request[/bold red]",
                    title="❌[ERROR] |addPaymentMethod| Validation Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse({"error": "Missing billing details"}, status=400)

        try:
            print(
                Panel(
                    f"[bold yellow]Looking up client with ID: {clientID}[/bold yellow]",
                    title="🔎[INFO] |addPaymentMethod| Database Lookup",
                    border_style="bright_blue",
                )
            )
            client = Client.objects.get(clientID=clientID)
            print(
                Panel(
                    f"[bold green]Found client: {client.companyName} (ID: {client.clientID})[/bold green]",
                    title="❎[SUCCESS] |addPaymentMethod| Client Found",
                    border_style="bright_green",
                )
            )
        except Client.DoesNotExist:
            print(
                Panel(
                    f"[bold red]Client with ID {clientID} not found in database[/bold red]",
                    title="❌[ERROR] |addPaymentMethod| Not Found Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse({"error": "Client not found"}, status=404)

        print(
            Panel(
                f"[bold bright_blue]Preparing to add payment method for {client.companyName}[/bold bright_blue]",
                title="🔎[INFO] |addPaymentMethod| Payment Processing",
                border_style="bright_blue",
            )
        )

        cardDetails = CardDetails(**cardDetails)
        billingDetails = CardBillingDetails(**billingDetails)

        payment = PaymentProfile.addPaymentMethod(
            client=client, cardDetails=cardDetails, billingDetails=billingDetails
        )

        if isinstance(payment, PaymentProfile) and payment.status == "Active":
            print(
                Panel(
                    f"[bold green]Successfully added payment method for client {client.clientID}[/bold green]",
                    title="❎[SUCCESS] |addPaymentMethod| Payment Success",
                    border_style="bright_green",
                )
            )
            return JsonResponse(
                {
                    "success": True,
                    "clientId": str(client.clientID),
                    "customerProfileID": str(client.customerProfileID),
                    "paymentMethodStatus": str(payment.status),
                },
                status=200,
            )
        else:
            error_message = (
                str(payment.get("error", "Unknown error"))
                if isinstance(payment, dict)
                else "Unknown error"
            )
            print(
                Panel(
                    f"[bold red]Failed to add payment method: {error_message}[/bold red]",
                    title="❌[ERROR] |addPaymentMethod| Payment Error",
                    border_style="bright_red",
                )
            )
            return JsonResponse(
                {
                    "success": False,
                    "clientId": str(client.clientID),
                    "customerProfileID": str(client.customerProfileID),
                    "paymentMethodStatus": error_message,
                },
                status=500,
            )

    except json.JSONDecodeError:
        print(
            Panel(
                "[bold red]Invalid JSON received in request[/bold red]",
                title="❌[ERROR] |addPaymentMethod| JSON Error",
                border_style="bright_red",
            )
        )
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        print(
            Panel(
                f"[bold red]Unexpected error in addPaymentMethod: {str(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
                title="❌[ERROR] |addPaymentMethod| System Error",
                border_style="bright_red",
            )
        )
        return JsonResponse(
            {"error": f"An unexpected error occurred: {str(e)}"}, status=500
        )
