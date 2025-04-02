import json
import os
import traceback
import uuid
from datetime import datetime

import dotenv
from authorizenet import apicontractsv1 as adn
from authorizenet.apicontractsv1 import (
    creditCardType,
    merchantAuthenticationType,
    orderType,
    paymentType,
    transactionRequestType,
)
from authorizenet.apicontrollers import (
    createCustomerPaymentProfileController,
    createCustomerProfileController,
    createTransactionController,
)
from django.db import models
from rich import print
from rich.panel import Panel

dotenv.load_dotenv()


class CardDetails:
    def __init__(self, cardNumber: str, expirationDate: str, cardCode: str):
        self.cardNumber: str = cardNumber
        self.expirationDate: str = expirationDate
        self.cardCode: str = cardCode


class CardBillingDetails:
    def __init__(self, firstName: str, lastName: str, address: str, zipCode: str):
        self.firstName: str = firstName
        self.lastName: str = lastName
        self.address: str = address
        self.zipCode: str = zipCode


class Client(models.Model):
    clientID = models.IntegerField(default=0)
    companyName = models.CharField(max_length=128, default="", blank=True)
    phone = models.CharField(max_length=128, default="", blank=True)
    email = models.CharField(max_length=254, default="", blank=True)
    customerProfileID = models.CharField(max_length=128, default="", blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    isParent = models.BooleanField(default=False)
    isChild = models.BooleanField(default=False)
    parentClientID = models.IntegerField(default=0)
    defaultPaymentID = models.CharField(max_length=128, default="", blank=True)
    salesperson = models.CharField(max_length=128, default="", blank=True)

    def getClientDetails(self) -> dict:
        defaultPayment = (
            PaymentProfile.objects.get(paymentProfileID=self.defaultPaymentID)
            if self.defaultPaymentID
            else None
        )
        return {
            "clientID": self.clientID,
            "companyName": self.companyName,
            "phone": self.phone,
            "email": self.email,
            "salesperson": self.salesperson,
            "defaultPayment": defaultPayment.getPaymentProfileDetails()
            if defaultPayment
            else {},
            "createdAt": self.createdAt,
        }

    @staticmethod
    def getClient(clientID: (int | None) = None) -> dict | list:
        """Get all clients with sanitized data for display"""
        try:
            print(
                Panel(
                    "[bold bright_blue]Retrieving client(s) from database[/bold bright_blue]",
                    title="🔎[INFO] ‖Client.getClient‖ Database Query",
                    border_style="bright_blue",
                )
            )

            if clientID is not None:
                client: Client = Client.objects.get(clientID=clientID)
                print(
                    Panel(
                        f"[bold yellow]Found client {client.clientID} in database[/bold yellow]",
                        title="🔎[INFO] ‖Client.getClient‖ Query Results",
                        border_style="bright_blue",
                    )
                )
                return {
                    "clientID": client.clientID,
                    "companyName": client.companyName,
                    "phone": client.phone,
                    "email": client.email,
                    "salesperson": client.salesperson,
                }
            else:
                clients = Client.objects.all()
            print(
                Panel(
                    f"[bold yellow]Found {len(clients)} clients in database[/bold yellow]",
                    title="🔎[INFO] ‖Client.getClient‖ Query Results",
                    border_style="bright_blue",
                )
            )

            clientList: list = [
                {
                    "clientID": int(client.clientID),
                    "companyName": str(client.companyName),
                    "phone": str(client.phone),
                    "createdAt": str(client.createdAt),
                    "email": str(client.email),
                    "salesperson": str(client.salesperson),
                }
                for client in clients
            ]

            print(
                Panel(
                    f"[bold green]Successfully sanitized {len(clientList)} client records[/bold green]",
                    title="✅[SUCCESS] ‖Client.getAllSanitizedClients‖ Data Processing",
                    border_style="bright_green",
                )
            )

            return clientList

        except Exception as e:
            print(
                Panel(
                    f"[bold red]Error getting client list: {str(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
                    title="❌[ERROR] ‖Client.getAllSanitizedClients‖ Database Error",
                    border_style="bright_red",
                )
            )
            # Return an empty list instead of raising the exception
            # This allows the API to at least return an empty result rather than crashing
            return []

    @staticmethod
    def createClientProfile(
        clientID: int,
        companyName: str,
        phone: str,
        salesperson: str,
        email: str = "noreply@lifecorp.com",
    ):
        print(
            Panel(
                f"[bold bright_blue]Creating payment profile for clientID: {clientID}[/bold bright_blue]",
                title="🔎[INFO] ‖Client.createClientProfile‖ Profile Creation",
                border_style="bright_blue",
            )
        )

        try:
            # Create a new PaymentProfile record
            client: Client = Client(
                companyName=companyName,
                clientID=clientID,
                phone=phone,
                salesperson=salesperson,
                email=email,
            )
            client.save()
            print(
                Panel(
                    f"[bold green]Database record created for clientID: {clientID}[/bold green]",
                    title="✅[SUCCESS] ‖Client.createClientProfile‖ Database Success",
                    border_style="bright_green",
                )
            )

            # Create customer profile in Authorize.net
            processorInterface: AuthNetInterface = AuthNetInterface()
            merchantAuth: merchantAuthenticationType = (
                processorInterface.getAuthStruct()
            )

            if merchantAuth is not None:
                print(
                    Panel(
                        f"[bold green]✅ Merchant authentication obtained: {merchantAuth is not None}[/bold green]",
                        title="✅[SUCCESS] ‖Client.createClientProfile‖ Authentication",
                        border_style="bright_green",
                    )
                )
            else:
                # Should never happen
                print(
                    Panel(
                        f"[bold red]❌ Merchant authentication obtained: {merchantAuth is not None}[/bold red]",
                        title="❌[ERROR] ‖Client.createClientProfile‖ Authentication",
                        border_style="bright_red",
                    )
                )

            # Create customer profile
            customerProfile = adn.customerProfileType()
            customerProfile.merchantCustomerId = (
                str(clientID) if clientID else companyName
            )
            customerProfile.description = f"Profile for {companyName}"
            customerProfile.email = email

            print(
                Panel(
                    f"[bold yellow]Submitting Request to create Customer Profile\n- Merchant Customer ID: {customerProfile.merchantCustomerId}\n- Description: {customerProfile.description}\n- Email: {customerProfile.email}\n- Environment: {processorInterface.env}[/bold yellow]",
                    title="🔎[INFO] ‖Client.createClientProfile‖ Customer Profile Request",
                    border_style="bright_blue",
                )
            )

            # Prepare the request
            request = adn.createCustomerProfileRequest()
            request.merchantAuthentication = merchantAuth
            request.profile = customerProfile
            # request.validationMode = "liveMode"

            print(
                Panel(
                    f"[bold bright_blue]Sending customer profile request to {processorInterface.env}[/bold bright_blue]",
                    title="🔎[INFO] ‖Client.createClientProfile‖ API Request",
                    border_style="bright_blue",
                )
            )

            # Create controller and execute
            controller = createCustomerProfileController(request)
            controller.setenvironment(processorInterface.env)

            try:
                controller.execute()
                response = controller.getresponse()

                # Use our custom response printer for better error details
                print(
                    Panel(
                        "[bold bright_blue]Full Response Details:[/bold bright_blue]",
                        title="🔎[INFO] ‖Client.createClientProfile‖ Response",
                        border_style="bright_blue",
                    )
                )

            except Exception as api_error:
                print(
                    Panel(
                        f"[bold red]Authorize.net API error: {str(api_error)}[/bold red]",
                        title="❌[ERROR] ‖Client.createClientProfile‖ API Error",
                        border_style="bright_red",
                    )
                )
                client.delete()
                return {"error": f"API Error: {str(api_error)}"}

            if response is not None:
                if response.messages.resultCode == "Ok":
                    print(
                        Panel(
                            f"[bold green]Response result code: {response.messages.resultCode}\n✅ Success! Customer profile created with ID: {response.customerProfileId}[/bold green]",
                            title="✅[SUCCESS] ‖Client.createClientProfile‖ Profile Creation Success",
                            border_style="bright_green",
                        )
                    )
                    client.customerProfileID = response.customerProfileId
                    client.save()
                    return client
                else:
                    error_msg = (
                        response.messages.message[0].text
                        if hasattr(response.messages, "message")
                        else "Unknown error"
                    )
                    error_code = (
                        response.messages.message[0].code
                        if hasattr(response.messages, "message")
                        else "Unknown code"
                    )
                    print(
                        Panel(
                            f"[bold red]❌ Error creating profile - Code: {error_code}, Message: {error_msg}[/bold red]",
                            title="❌[ERROR] ‖Client.createClientProfile‖ Profile Creation Error",
                            border_style="bright_red",
                        )
                    )
                    client.delete()
                    return {"error": f"Error {error_code}: {error_msg}"}
            else:
                print(
                    Panel(
                        "[bold red]No response received from Authorize.net[/bold red]",
                        title="❌[ERROR] ‖Client.createClientProfile‖ Communication Error",
                        border_style="bright_red",
                    )
                )
                client.delete()
                return {"error": "No response from payment gateway"}

        except Exception as e:
            print(
                Panel(
                    f"[bold red]Unexpected error in createPaymentProfile: {str(e)}\nTraceback: {traceback.format_exc()}[/bold red]",
                    title="❌[ERROR] ‖Client.createClientProfile‖ System Error",
                    border_style="bright_red",
                )
            )
            client.delete()
            return {"error": f"System Error: {str(e)}"}


class ClientNote(models.Model):
    clientID = models.IntegerField(default=0)
    createdAt = models.DateTimeField(auto_now_add=True)
    createdBy = models.CharField(max_length=128, default="", blank=True)
    note = models.CharField(max_length=248)

    def getClientNoteDetails(self) -> dict:
        return {
            "clientID": self.clientID,
            "createdAt": self.createdAt,
            "createdBy": self.createdBy,
            "note": self.note,
        }

    @staticmethod
    def createNote(client: Client, createdBy: str, note: str):
        try:
            noteRec: ClientNote = ClientNote(
                clientID=client.clientID, createdBy=createdBy, note=note
            )
            noteRec.save()
            return noteRec
        except Exception as e:
            print(
                Panel(
                    renderable=f"[bold red]Error while creating note for client {client.clientID}: {e}[/bold red]",
                    title="❌[ERROR] ‖ClientNote.createNote‖ Note Creation Error",
                    border_style="bright_red",
                )
            )
            return {"error": f"Note Creation Error: {str(e)}"}


class PaymentProfile(models.Model):
    processor = models.CharField(max_length=128, default="AuthorizeNet", blank=True)
    clientID = models.IntegerField(default=0)
    createdBy = models.CharField(max_length=128, default="", blank=True)
    status = models.CharField(max_length=128, default="Active", blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    billedFrom = models.CharField(
        max_length=128, default="Wholesale Communications", blank=True
    )
    customerProfileID = models.CharField(max_length=128, default="", blank=True)
    paymentProfileID = models.CharField(max_length=128, default="", blank=True)
    firstName = models.CharField(max_length=128, default="", blank=True)
    lastName = models.CharField(max_length=128, default="", blank=True)
    email = models.CharField(max_length=254, default="", blank=True)
    streetAddress = models.CharField(max_length=128, default="", blank=True)
    state = models.CharField(max_length=128, default="", blank=True)
    zipCode = models.CharField(max_length=128, default="", blank=True)
    cardType = models.CharField(max_length=128, default="", blank=True)
    lastFour = models.CharField(max_length=128, default="", blank=True)
    isChildBillable = models.BooleanField(default=False)
    customerType = models.CharField(max_length=128, default="business", blank=True)

    def getPaymentProfileDetails(self) -> dict:
        return {
            "processor": self.processor,
            "clientID": self.clientID,
            "createdBy": self.createdBy,
            "status": self.status,
            "createdAt": self.createdAt,
            "billedFrom": self.billedFrom,
            "customerProfileID": self.customerProfileID,
            "paymentProfileID": self.paymentProfileID,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "zipCode": self.zipCode,
            "cardType": self.cardType,
            "lastFour": self.lastFour,
        }

    @staticmethod
    def addPaymentMethod(
        client: Client, cardDetails: CardDetails, billingDetails: CardBillingDetails
    ):
        """Add a payment method to an existing customer profile"""
        print(
            Panel(
                f"[bold bright_blue]Adding payment method to profile for [{client.clientID}]{client.companyName} ProfileID: {client.customerProfileID}[/bold bright_blue]",
                title="🔎[INFO] ‖PaymentProfile.addPaymentMethod‖ Payment Method Addition",
                border_style="bright_blue",
            )
        )
        # Create a new PaymentProfile record
        profile: PaymentProfile = PaymentProfile(
            clientID=client.clientID,
            createdBy=client.salesperson,
            customerProfileID=client.customerProfileID,
            firstName=billingDetails.firstName,
            lastName=billingDetails.lastName,
            email=client.email,
            streetAddress=billingDetails.address,
            zipCode=billingDetails.zipCode,
            lastFour=cardDetails.cardNumber[-4:],
        )
        profile.save()
        processorInterface: AuthNetInterface = AuthNetInterface()
        # Get merchant authentication
        merchantAuth: merchantAuthenticationType = processorInterface.getAuthStruct()

        # Create credit card
        creditCard: creditCardType = adn.creditCardType()
        creditCard.cardNumber = cardDetails.cardNumber
        creditCard.expirationDate = cardDetails.expirationDate
        creditCard.cardCode = cardDetails.cardCode
        print(
            Panel(
                f"[bold yellow]Card info prepared: {cardDetails.cardNumber[-4:]} exp: {cardDetails.expirationDate}[/bold yellow]",
                title="🔎[INFO] ‖PaymentProfile.addPaymentMethod‖ Card Details",
                border_style="bright_blue",
            )
        )

        # Create payment
        payment: paymentType = adn.paymentType()
        payment.creditCard = creditCard

        # Create payment profile
        paymentProfile = adn.customerPaymentProfileType()
        paymentProfile.payment = payment

        # Billing address
        billTo = adn.customerAddressType()
        billTo.firstName = billingDetails.firstName
        billTo.lastName = billingDetails.lastName
        billTo.address = billingDetails.address
        billTo.zip = billingDetails.zipCode
        paymentProfile.billTo = billTo

        # Create request
        request = adn.createCustomerPaymentProfileRequest()
        request.merchantAuthentication = merchantAuth
        request.customerProfileId = client.customerProfileID
        request.paymentProfile = paymentProfile
        request.validationMode = os.getenv("AUTH_NET_MODE")  # or "testMode" for testing

        print(
            Panel(
                f"[bold bright_blue]Sending payment profile request to Authorize.net for customer: {client.customerProfileID}[/bold bright_blue]",
                title="🔎[INFO] ‖PaymentProfile.addPaymentMethod‖ API Request",
                border_style="bright_blue",
            )
        )

        # Create controller and execute
        controller = createCustomerPaymentProfileController(request)
        controller.setenvironment(processorInterface.env)
        controller.execute()

        # Get response
        response = controller.getresponse()
        print(
            Panel(
                f"[bold yellow]Received payment profile response: {response.messages.resultCode if response is not None else 'None'}[/bold yellow]",
                title="🔎[INFO] ‖PaymentProfile.addPaymentMethod‖ Response Received",
                border_style="bright_blue",
            )
        )

        if response is not None and response.messages.resultCode == "Ok":
            # Save payment profile ID to the new profile
            profile.paymentProfileID = response.customerPaymentProfileId
            profile.save()
            if client.defaultPaymentID == "":
                client.defaultPaymentID = response.customerPaymentProfileId
                client.save()
                print(
                    Panel(
                        f"[bold green]Payment profile {response.customerPaymentProfileId} set as default for [{client.clientID}]{client.companyName}[/bold green]",
                        title="✅[SUCCESS] ‖PaymentProfile.addPaymentMethod‖ Default Payment Set",
                        border_style="bright_green",
                    )
                )
            print(
                Panel(
                    f"[bold green]Success! Payment profile created with ID: {response.customerPaymentProfileId}[/bold green]",
                    title="✅[SUCCESS] ‖PaymentProfile.addPaymentMethod‖ Payment Profile Success",
                    border_style="bright_green",
                )
            )
            return profile
        else:
            # Delete the new profile if the payment method addition failed
            profile.delete()

            if (
                response is not None
                and hasattr(response, "messages")
                and hasattr(response.messages, "message")
            ):
                error_msg: str = response.messages.message[0].text
                print(
                    Panel(
                        f"[bold red]Error creating payment profile: {str(error_msg)}[/bold red]",
                        title="❌[ERROR] ‖PaymentProfile.addPaymentMethod‖ Payment Profile Error",
                        border_style="bright_red",
                    )
                )
                return {"error": str(error_msg)}
            print(
                Panel(
                    "[bold red]Error creating payment profile: Unknown error[/bold red]",
                    title="❌[ERROR] ‖PaymentProfile.addPaymentMethod‖ Unknown Error",
                    border_style="bright_red",
                )
            )
            return {"error": "Failed to create payment profile"}


class AuthNetInterface:
    def __init__(self):
        self.processor: str = "AuthorizeNet"
        self.sandbox: bool = bool(os.getenv("DEV"))
        self.env: str | None = (
            os.getenv("SANDBOX_AUTH_NET_ENV")
            if self.sandbox
            else os.getenv("PROD_AUTH_NET_ENV")
        )
        self.apiLoginID: str | None = (
            os.getenv("SANDBOX_AUTH_NET_ID")
            if self.sandbox
            else os.getenv("PROD_AUTH_NET_ID")
        )
        self.transactionKey: str | None = (
            os.getenv("SANDBOX_AUTH_NET_TK")
            if self.sandbox
            else os.getenv("PROD_AUTH_NET_TK")
        )
        print(
            Panel(
                f"[bold yellow]initializing authnet interface\nSandbox: {self.sandbox}\nEnvironment: {self.env}[/bold yellow]",
                title="🔎[INFO] ‖AuthNetInterface.__init__‖ Initialization",
                border_style="bright_blue",
            )
        )

    def getAuthStruct(self) -> merchantAuthenticationType:
        authStruct: adn.merchantAuthenticationType = adn.merchantAuthenticationType()
        authStruct.name = self.apiLoginID
        authStruct.transactionKey = self.transactionKey
        print(
            Panel(
                f"[bold bright_blue]Auth credentials prepared\nLogin ID: {str(self.apiLoginID)[:4]}{'*' * 8}[/bold bright_blue]",
                title="🔎[INFO] ‖AuthNetInterface.getAuthStruct‖ Authentication",
                border_style="bright_blue",
            )
        )
        return authStruct

    @staticmethod
    def getCardStruct(cardDetails: CardDetails) -> creditCardType:
        creditCard: creditCardType = adn.creditCardType()
        creditCard.cardNumber = cardDetails.cardNumber
        creditCard.expirationDate = cardDetails.expirationDate
        creditCard.cardCode = cardDetails.cardCode
        print(
            Panel(
                f"[bold yellow]Credit card details prepared\nCard ending in: {cardDetails.cardNumber[-4:]}\nExpiration: {cardDetails.expirationDate}[/bold yellow]",
                title="🔎[INFO] ‖AuthNetInterface.getCardStruct‖ Card Details",
                border_style="bright_blue",
            )
        )
        return creditCard

    @staticmethod
    def getOrderStruct(invoiceID: str) -> orderType:
        order: orderType = adn.orderType()
        order.invoiceNumber = invoiceID
        order.description = "Autocommunications through WholeSale Communications"
        print(
            Panel(
                f"[bold bright_blue]Order details prepared\nInvoice ID: {invoiceID}\nDescription: {orderType.description}[/bold bright_blue]",
                title="🔎[INFO] ‖AuthNetInterface.getOrderType‖ Order Information",
                border_style="bright_blue",
            )
        )
        return order

    @staticmethod
    def getTransactionStruct(
        amount: float, creditCard: adn.creditCardType, order: adn.orderType
    ) -> transactionRequestType:
        payment: paymentType = adn.paymentType()
        payment.creditCard = creditCard
        txStruct: transactionRequestType = adn.transactionRequestType()
        txStruct.transactionType = "authCaptureTransaction"
        txStruct.amount = str(amount)
        txStruct.currencyCode = "USD"
        txStruct.payment = payment
        txStruct.order = order
        print(
            Panel(
                f"[bold yellow]Transaction request prepared\nType: {txStruct.transactionType}\nAmount: ${amount} {txStruct.currencyCode}\nCard ending in: {creditCard.cardNumber[-4:]}[/bold yellow]",
                title="🔎[INFO] ‖AuthNetInterface.getTransactionStruct‖ Transaction Setup",
                border_style="bright_blue",
            )
        )
        return txStruct

    @staticmethod
    def processCardTransaction(
        amount: float, cardDetails: CardDetails, clientID: int, salesperson: str
    ) -> dict:
        print(
            Panel(
                f"[bold bright_blue]Processing transaction for {amount} with card {cardDetails.cardNumber} expiring {cardDetails.expirationDate} and cvv {cardDetails.cardCode}[/bold bright_blue]",
                title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ Transaction Processing",
                border_style="bright_blue",
            )
        )

        # Initialize Transaction Record
        invoiceID: str = str(uuid.uuid4())[:16]
        refID: str = str(datetime.now().timestamp())

        print(
            Panel(
                f"[bold bright_blue]Creating transaction record\nInvoice ID: {invoiceID}\nReference ID: {refID}\nClient ID: {clientID}\nAmount: ${amount}[/bold bright_blue]",
                title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ Transaction Initialization",
                border_style="bright_blue",
            )
        )

        tx: Transaction = Transaction(
            invoiceID=invoiceID,
            refID=refID,
            amount=amount,
            salesperson=salesperson,
            clientID=clientID,
        )
        tx.save()

        # Initialize the transaction request
        creditCard: creditCardType = AuthNetInterface.getCardStruct(cardDetails)
        order: orderType = AuthNetInterface.getOrderStruct(invoiceID=invoiceID)

        print(
            Panel(
                f"[bold yellow]Preparing API request\nClient ID: {clientID}\nRef ID: {refID}[/bold yellow]",
                title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ Request Preparation",
                border_style="bright_blue",
            )
        )

        txRequest = adn.createTransactionRequest()
        txRequest.merchantAuthentication = AuthNetInterface().getAuthStruct()
        txRequest.refId = refID
        txRequest.transactionRequest = AuthNetInterface.getTransactionStruct(
            amount=amount,  # Must convert float to string
            creditCard=creditCard,
            order=order,
        )

        # Execute the request
        controller = createTransactionController(txRequest)
        controller.setenvironment(AuthNetInterface().env)

        print(
            Panel(
                f"[bold bright_blue]Sending transaction to {AuthNetInterface().env}\nInvoice ID: {invoiceID}\nAmount: ${amount}[/bold bright_blue]",
                title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ API Request",
                border_style="bright_blue",
            )
        )

        controller.execute()
        tx.submitted = True
        tx.result = "Submitted"
        tx.save()

        print(
            Panel(
                f"[bold green]Transaction submitted\nInvoice ID: {invoiceID}\nRef ID: {refID}[/bold green]",
                title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Request Sent",
                border_style="bright_green",
            )
        )

        response = controller.getresponse()

        if response is not None:
            print(
                Panel(
                    f"[bold green]Received response from payment gateway[/bold green]",
                    title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Response Received",
                    border_style="bright_green",
                )
            )

            # Extract main messages fields
            if hasattr(response, "messages"):
                # resultStatus = messages.resultCode
                tx.resultStatus = getattr(response.messages, "resultCode", "")

                # Print response in nice format
                if tx.resultStatus == "Ok":
                    print(
                        Panel(
                            AuthNetInterface.printSuccessResponse(response),
                            title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Success Response",
                            border_style="bright_green",
                        )
                    )
                else:
                    print(
                        Panel(
                            AuthNetInterface.printError(response),
                            title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Error Response",
                            border_style="bright_red",
                        )
                    )

                # Extract from main messages
                if (
                    hasattr(response.messages, "message")
                    and len(response.messages.message) > 0
                ):
                    msg = response.messages.message[0]
                    # resultCode = messages.message[0].code
                    tx.resultCode = getattr(msg, "code", "")
                    # resultText (part 1) = messages.message[0].text
                    tx.resultText = getattr(msg, "text", "")

                    if tx.resultStatus == "Ok":
                        print(
                            Panel(
                                f"[bold green]Result code: {tx.resultCode}\nMessage: {tx.resultText}[/bold green]",
                                title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Response Message",
                                border_style="bright_green",
                            )
                        )
                    else:
                        print(
                            Panel(
                                f"[bold red]Result code: {tx.resultCode}\nMessage: {tx.resultText}[/bold red]",
                                title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Response Message",
                                border_style="bright_red",
                            )
                        )

            # Extract transaction response fields
            if hasattr(response, "transactionResponse"):
                txResp = response.transactionResponse

                # responseCode = transactionResponse.responseCode
                tx.responseCode = str(getattr(txResp, "responseCode", ""))
                # authCode = transactionResponse.authCode
                tx.authCode = getattr(txResp, "authCode", "")
                # avsResultCode = transactionResponse.avsResultCode
                tx.avsResultCode = getattr(txResp, "avsResultCode", "")
                # cvvResultCode = transactionResponse.cvvResultCode
                tx.cvvResultCode = getattr(txResp, "cvvResultCode", "")
                # cavvResultCode = transactionResponse.cavvResultCode
                tx.cavvResultCode = getattr(txResp, "cavvResultCode", "")
                # networkTransId = transactionResponse.networkTransId
                tx.networkTransId = getattr(txResp, "networkTransId", "")
                # accountNumber = transactionResponse.accountNumber
                tx.accountNumber = getattr(txResp, "accountNumber", "")
                # accountType = transactionResponse.accountType
                tx.accountType = getattr(txResp, "accountType", "")
                # transId = transactionResponse.transId
                tx.transID = getattr(txResp, "transId", "")

                if tx.responseCode == "1":
                    print(
                        Panel(
                            f"[bold green]Response code: {tx.responseCode}\nAuth code: {tx.authCode}\nTransaction ID: {tx.transID}\nAccount: {tx.accountNumber if tx.accountNumber else 'N/A'}[/bold green]",
                            title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Transaction Details",
                            border_style="bright_green",
                        )
                    )
                else:
                    print(
                        Panel(
                            f"[bold yellow]Response code: {tx.responseCode}\nAuth code: {tx.authCode}\nTransaction ID: {tx.transID}\nAccount: {tx.accountNumber if tx.accountNumber else 'N/A'}[/bold yellow]",
                            title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ Transaction Details",
                            border_style="bright_blue",
                        )
                    )

                # Get transaction messages if available
                if hasattr(txResp, "messages") and hasattr(txResp.messages, "message"):
                    if len(txResp.messages.message) > 0:
                        txMsg = txResp.messages.message[0]
                        # resultNumber = transactionResponse.messages.message[0].code
                        tx.resultNumber = getattr(txMsg, "code", "")
                        # resultText (part 2) = transactionResponse.messages.message[0].description
                        # Only set resultText from here if it's not already set from messages.message
                        if not tx.resultText:
                            tx.resultText = getattr(txMsg, "description", "")

                # Get error information if it exists
                if hasattr(txResp, "errors") and hasattr(txResp.errors, "error"):
                    if len(txResp.errors.error) > 0:
                        err = txResp.errors.error[0]
                        # error = transactionResponse.errors.error[0].errorCode
                        tx.error = getattr(err, "errorCode", "")
                        # errorText = transactionResponse.errors.error[0].errorText
                        tx.errorText = getattr(err, "errorText", "")

                        print(
                            Panel(
                                f"[bold red]Error code: {tx.error}\nError message: {tx.errorText}[/bold red]",
                                title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Transaction Error",
                                border_style="bright_red",
                            )
                        )

            if tx.responseCode == "1":
                tx.result = "Success"
                tx.save()

                print(
                    Panel(
                        f"[bold green]Transaction successful\nInvoice ID: {invoiceID}\nTransaction ID: {tx.transID}\nAmount: ${amount}[/bold green]",
                        title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Transaction Success",
                        border_style="bright_green",
                    )
                )

                return tx.getResults()
            else:
                tx.result = "Failed"

                print(
                    Panel(
                        f"[bold red]Transaction failed\nInvoice ID: {invoiceID}\nResponse code: {tx.responseCode}[/bold red]",
                        title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Transaction Failed",
                        border_style="bright_red",
                    )
                )

                # Get specific error details from transactionResponse if available
                if hasattr(response, "transactionResponse") and hasattr(
                    response.transactionResponse, "errors"
                ):
                    txResp = response.transactionResponse
                    if hasattr(txResp.errors, "error"):
                        if (
                            isinstance(txResp.errors.error, list)
                            and len(txResp.errors.error) > 0
                        ):
                            err = txResp.errors.error[0]
                            tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )
                        elif not isinstance(txResp.errors.error, list):
                            err = txResp.errors.error
                            tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )

                # If we don't have specific error info from transaction, use general errors
                if (
                    not tx.error
                    and hasattr(response, "messages")
                    and hasattr(response.messages, "message")
                ):
                    if len(response.messages.message) > 0:
                        msg = response.messages.message[0]
                        tx.error = getattr(msg, "code", "UNKNOWN_ERROR")
                        tx.errorText = getattr(msg, "text", "Unknown error occurred")

            # Save all extracted data
            tx.save()
            return {
                "error": str(tx.error) or "UNKNOWN_ERROR",
                "errorText": str(tx.errorText) or "Transaction failed",
            }
        else:
            # No response from gateway
            print(
                Panel(
                    f"[bold red]No response received from payment gateway\nInvoice ID: {invoiceID}[/bold red]",
                    title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Communication Error",
                    border_style="bright_red",
                )
            )

            tx.result = "Error"
            tx.error = "NO_RESPONSE"
            tx.errorText = "No response from payment gateway"
            tx.save()

            return {
                "error": "NO_RESPONSE",
                "errorText": "No response from payment gateway",
            }

    @staticmethod
    def printSuccessResponse(response):
        """
        Pretty-prints an Authorize.net response in a JSON-like format
        that's easier to read than the recursive object dump.
        """

        # Start with an empty dictionary
        result = {}

        # Extract refId
        if hasattr(response, "refId"):
            result["refId"] = response.refId

        # Extract messages structure
        if hasattr(response, "messages"):
            messages = {"resultCode": response.messages.resultCode}

            # Extract message array
            if hasattr(response.messages, "message"):
                msg_list = []
                # Sometimes it's a single message, sometimes a list
                if isinstance(response.messages.message, list):
                    for msg in response.messages.message:
                        msg_list.append(
                            {
                                "code": getattr(msg, "code", None),
                                "text": getattr(msg, "text", None),
                            }
                        )
                else:
                    msg = response.messages.message
                    msg_list.append(
                        {
                            "code": getattr(msg, "code", None),
                            "text": getattr(msg, "text", None),
                        }
                    )
                messages["message"] = msg_list

            result["messages"] = messages

        # Extract transaction response
        if hasattr(response, "transactionResponse"):
            tx_resp = response.transactionResponse
            tx_data = {
                "responseCode": getattr(tx_resp, "responseCode", None),
                "authCode": getattr(tx_resp, "authCode", None),
                "avsResultCode": getattr(tx_resp, "avsResultCode", None),
                "cvvResultCode": getattr(tx_resp, "cvvResultCode", None),
                "cavvResultCode": getattr(tx_resp, "cavvResultCode", None),
                "transId": getattr(tx_resp, "transId", None),
                "refTransID": getattr(tx_resp, "refTransID", None) or "",
                "transHash": getattr(tx_resp, "transHash", None) or "",
                "testRequest": getattr(tx_resp, "testRequest", None),
                "accountNumber": getattr(tx_resp, "accountNumber", None),
                "accountType": getattr(tx_resp, "accountType", None),
                "transHashSha2": getattr(tx_resp, "transHashSha2", None) or "",
                "networkTransId": getattr(tx_resp, "networkTransId", None) or "",
            }

            # Extract messages from transaction response
            if hasattr(tx_resp, "messages"):
                msg_list = []
                if hasattr(tx_resp.messages, "message"):
                    if isinstance(tx_resp.messages.message, list):
                        for msg in tx_resp.messages.message:
                            msg_list.append(
                                {
                                    "code": getattr(msg, "code", None),
                                    "description": getattr(msg, "description", None),
                                }
                            )
                    else:
                        msg = tx_resp.messages.message
                        msg_list.append(
                            {
                                "code": getattr(msg, "code", None),
                                "description": getattr(msg, "description", None),
                            }
                        )
                tx_data["messages"] = msg_list

            result["transactionResponse"] = tx_data

        # Print in a nicely formatted JSON structure
        result_str = json.dumps(result, indent=2, default=str)
        return result_str

    @staticmethod
    def printError(response):
        """
        Pretty-prints an Authorize.net error response in a JSON-like format
        that's easier to read than the recursive object dump.
        """
        # Start with an empty dictionary
        result = {}

        # Extract refId
        if hasattr(response, "refId"):
            result["refId"] = response.refId

        # Extract messages structure
        if hasattr(response, "messages"):
            messages = {"resultCode": response.messages.resultCode}

            # Extract message array
            if hasattr(response.messages, "message"):
                msg_list = []
                # Sometimes it's a single message, sometimes a list
                if isinstance(response.messages.message, list):
                    for msg in response.messages.message:
                        msg_list.append(
                            {
                                "code": getattr(msg, "code", None),
                                "text": getattr(msg, "text", None),
                            }
                        )
                else:
                    msg = response.messages.message
                    msg_list.append(
                        {
                            "code": getattr(msg, "code", None),
                            "text": getattr(msg, "text", None),
                        }
                    )
                messages["message"] = msg_list

            result["messages"] = messages

        # Extract transaction response errors
        if hasattr(response, "transactionResponse"):
            tx_resp = response.transactionResponse
            tx_data = {
                "responseCode": getattr(tx_resp, "responseCode", None),
                "transId": getattr(tx_resp, "transId", None),
            }

            # Extract error information
            if hasattr(tx_resp, "errors"):
                error_list = []
                if hasattr(tx_resp.errors, "error"):
                    if isinstance(tx_resp.errors.error, list):
                        for err in tx_resp.errors.error:
                            error_list.append(
                                {
                                    "errorCode": getattr(err, "errorCode", None),
                                    "errorText": getattr(err, "errorText", None),
                                }
                            )
                    else:
                        err = tx_resp.errors.error
                        error_list.append(
                            {
                                "errorCode": getattr(err, "errorCode", None),
                                "errorText": getattr(err, "errorText", None),
                            }
                        )
                tx_data["errors"] = error_list

            result["transactionResponse"] = tx_data

        # Print in a nicely formatted JSON structure
        result_str = json.dumps(result, indent=2, default=str)
        return result_str

    @staticmethod
    def chargeProfilePayment(
        paymentProfile: PaymentProfile,
        client: Client,
        amount:str,
        invoiceID=None,
        description=None,
    ):
        """Process a payment using stored customer payment profile"""
        if not paymentProfile.customerProfileID or not paymentProfile.paymentProfileID:
            return {"error": "Missing customer or payment profile ID"}
        if client.customerProfileID != paymentProfile.customerProfileID:
            return {"error": "Client and payment profile do not match"}
        # Create a unique invoiceID if not provided
        if not invoiceID:
            invoiceID = str(uuid.uuid4())[:12]

        # Generate reference ID
        refID = str(datetime.now().timestamp())

        # Create transaction record
        tx = Transaction(
            clientID=client.clientID,
            invoiceID=invoiceID,
            refID=refID,
            amount=amount,
            salesperson=client.salesperson,
        )
        tx.save()
        AuthInterface = AuthNetInterface()
        # Get merchant authentication
        merchantAuth = AuthInterface.getAuthStruct()

        # Create a customer profile payment type
        profileToCharge = adn.customerProfilePaymentType()
        profileToCharge.customerProfileId = paymentProfile.customerProfileID
        profileToCharge.paymentProfile = adn.paymentProfile()
        profileToCharge.paymentProfile.paymentProfileId = (
            paymentProfile.paymentProfileID
        )

        # Create transaction request
        txRequest = adn.createTransactionRequest()
        txRequest.merchantAuthentication = merchantAuth
        txRequest.refId = refID

        # Create transaction type
        txType = adn.transactionRequestType()
        txType.transactionType = "authCaptureTransaction"
        txType.amount = amount
        txType.profile = profileToCharge

        # Add order information if needed
        if description or invoiceID:
            order = AuthInterface.getOrderStruct(invoiceID)
            if description:
                order.description = description
            txType.order = order

        txRequest.transactionRequest = txType

        # Create controller and execute
        controller = createTransactionController(txRequest)
        controller.setenvironment(AuthInterface.env)
        controller.execute()

        # Update transaction record
        tx.submitted = True
        tx.result = "Submitted"
        tx.save()

        # Process response
        response = controller.getresponse()

        # Process response (reusing existing Transaction response handling)
        # This code would need the same response handling as in Transaction.processTransaction
        # For brevity, let's just extract key information
        if response is None:
            AuthNetInterface.printError(response)
        if response is not None:
            print(
                Panel(
                    f"[bold green]Received response from payment gateway[/bold green]",
                    title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Response Received",
                    border_style="bright_green",
                )
            )

            # Extract main messages fields
            if hasattr(response, "messages"):
                # resultStatus = messages.resultCode
                tx.resultStatus = getattr(response.messages, "resultCode", "")

                # Print response in nice format
                if tx.resultStatus == "Ok":
                    print(
                        Panel(
                            AuthNetInterface.printSuccessResponse(response),
                            title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Success Response",
                            border_style="bright_green",
                        )
                    )
                else:
                    print(
                        Panel(
                            AuthNetInterface.printError(response),
                            title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Error Response",
                            border_style="bright_red",
                        )
                    )

                # Extract from main messages
                if (
                    hasattr(response.messages, "message")
                    and len(response.messages.message) > 0
                ):
                    msg = response.messages.message[0]
                    # resultCode = messages.message[0].code
                    tx.resultCode = getattr(msg, "code", "")
                    # resultText (part 1) = messages.message[0].text
                    tx.resultText = getattr(msg, "text", "")

                    if tx.resultStatus == "Ok":
                        print(
                            Panel(
                                f"[bold green]Result code: {tx.resultCode}\nMessage: {tx.resultText}[/bold green]",
                                title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Response Message",
                                border_style="bright_green",
                            )
                        )
                    else:
                        print(
                            Panel(
                                f"[bold red]Result code: {tx.resultCode}\nMessage: {tx.resultText}[/bold red]",
                                title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Response Message",
                                border_style="bright_red",
                            )
                        )

            # Extract transaction response fields
            if hasattr(response, "transactionResponse"):
                txResp = response.transactionResponse

                # responseCode = transactionResponse.responseCode
                tx.responseCode = str(getattr(txResp, "responseCode", ""))
                # authCode = transactionResponse.authCode
                tx.authCode = getattr(txResp, "authCode", "")
                # avsResultCode = transactionResponse.avsResultCode
                tx.avsResultCode = getattr(txResp, "avsResultCode", "")
                # cvvResultCode = transactionResponse.cvvResultCode
                tx.cvvResultCode = getattr(txResp, "cvvResultCode", "")
                # cavvResultCode = transactionResponse.cavvResultCode
                tx.cavvResultCode = getattr(txResp, "cavvResultCode", "")
                # networkTransId = transactionResponse.networkTransId
                tx.networkTransId = getattr(txResp, "networkTransId", "")
                # accountNumber = transactionResponse.accountNumber
                tx.accountNumber = getattr(txResp, "accountNumber", "")
                # accountType = transactionResponse.accountType
                tx.accountType = getattr(txResp, "accountType", "")
                # transId = transactionResponse.transId
                tx.transID = getattr(txResp, "transId", "")

                if tx.responseCode == "1":
                    print(
                        Panel(
                            f"[bold green]Response code: {tx.responseCode}\nAuth code: {tx.authCode}\nTransaction ID: {tx.transID}\nAccount: {tx.accountNumber if tx.accountNumber else 'N/A'}[/bold green]",
                            title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Transaction Details",
                            border_style="bright_green",
                        )
                    )
                else:
                    print(
                        Panel(
                            f"[bold yellow]Response code: {tx.responseCode}\nAuth code: {tx.authCode}\nTransaction ID: {tx.transID}\nAccount: {tx.accountNumber if tx.accountNumber else 'N/A'}[/bold yellow]",
                            title="🔎[INFO] ‖AuthNetInterface.processCardTransaction‖ Transaction Details",
                            border_style="bright_blue",
                        )
                    )

                # Get transaction messages if available
                if hasattr(txResp, "messages") and hasattr(txResp.messages, "message"):
                    if len(txResp.messages.message) > 0:
                        txMsg = txResp.messages.message[0]
                        # resultNumber = transactionResponse.messages.message[0].code
                        tx.resultNumber = getattr(txMsg, "code", "")
                        # resultText (part 2) = transactionResponse.messages.message[0].description
                        # Only set resultText from here if it's not already set from messages.message
                        if not tx.resultText:
                            tx.resultText = getattr(txMsg, "description", "")

                # Get error information if it exists
                if hasattr(txResp, "errors") and hasattr(txResp.errors, "error"):
                    if len(txResp.errors.error) > 0:
                        err = txResp.errors.error[0]
                        # error = transactionResponse.errors.error[0].errorCode
                        tx.error = getattr(err, "errorCode", "")
                        # errorText = transactionResponse.errors.error[0].errorText
                        tx.errorText = getattr(err, "errorText", "")

                        print(
                            Panel(
                                f"[bold red]Error code: {tx.error}\nError message: {tx.errorText}[/bold red]",
                                title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Transaction Error",
                                border_style="bright_red",
                            )
                        )

            if tx.responseCode == "1":
                tx.result = "Success"
                tx.save()

                print(
                    Panel(
                        f"[bold green]Transaction successful\nInvoice ID: {invoiceID}\nTransaction ID: {tx.transID}\nAmount: ${amount}[/bold green]",
                        title="✅[SUCCESS] ‖AuthNetInterface.processCardTransaction‖ Transaction Success",
                        border_style="bright_green",
                    )
                )

                return tx.getResults()
            else:
                tx.result = "Failed"

                print(
                    Panel(
                        f"[bold red]Transaction failed\nInvoice ID: {invoiceID}\nResponse code: {tx.responseCode}[/bold red]",
                        title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Transaction Failed",
                        border_style="bright_red",
                    )
                )

                # Get specific error details from transactionResponse if available
                if hasattr(response, "transactionResponse") and hasattr(
                    response.transactionResponse, "errors"
                ):
                    txResp = response.transactionResponse
                    if hasattr(txResp.errors, "error"):
                        if (
                            isinstance(txResp.errors.error, list)
                            and len(txResp.errors.error) > 0
                        ):
                            err = txResp.errors.error[0]
                            tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )
                        elif not isinstance(txResp.errors.error, list):
                            err = txResp.errors.error
                            tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )

                # If we don't have specific error info from transaction, use general errors
                if (
                    not tx.error
                    and hasattr(response, "messages")
                    and hasattr(response.messages, "message")
                ):
                    if len(response.messages.message) > 0:
                        msg = response.messages.message[0]
                        tx.error = getattr(msg, "code", "UNKNOWN_ERROR")
                        tx.errorText = getattr(msg, "text", "Unknown error occurred")

            # Save all extracted data
            tx.save()
            return {
                "error": str(tx.error) or "UNKNOWN_ERROR",
                "errorText": str(tx.errorText) or "Transaction failed",
            }
        else:
            # No response from gateway
            print(
                Panel(
                    f"[bold red]No response received from payment gateway\nInvoice ID: {invoiceID}[/bold red]",
                    title="❌[ERROR] ‖AuthNetInterface.processCardTransaction‖ Communication Error",
                    border_style="bright_red",
                )
            )

            tx.result = "Error"
            tx.error = "NO_RESPONSE"
            tx.errorText = "No response from payment gateway"
            tx.save()

            return {
                "error": "NO_RESPONSE",
                "errorText": "No response from payment gateway",
            }


class Transaction(models.Model):
    result = models.CharField(max_length=64, default="Not Submitted")
    transID = models.CharField(max_length=254, default="", blank=True)
    refID = models.CharField(max_length=64)
    invoiceID = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    clientID = models.IntegerField(default=0, blank=True)
    processor = models.CharField(max_length=128, default="", blank=True)
    billedFrom = models.CharField(max_length=128, default="", blank=True)
    customerProfileID = models.CharField(max_length=128, default="", blank=True)
    paymentProfileID = models.CharField(max_length=128, default="", blank=True)
    firstName = models.CharField(max_length=128, default="", blank=True)
    lastName = models.CharField(max_length=128, default="", blank=True)
    email = models.CharField(max_length=254, default="", blank=True)
    streetAddress = models.CharField(max_length=128, default="", blank=True)
    zipCode = models.CharField(max_length=128, default="", blank=True)
    isParentBilled = models.BooleanField(default=False)
    amount = models.CharField(max_length=64)
    salesperson = models.CharField(max_length=254)
    submitted = models.BooleanField(default=False)
    resultStatus = models.CharField(
        max_length=8, default="", blank=True
    )  # messages.resultCode
    resultCode = models.CharField(
        max_length=16, default="", blank=True
    )  # messages.message[0].code
    resultNumber = models.CharField(
        max_length=16, default="", blank=True
    )  # transactionResponse.messages.message[0].code
    resultText = models.CharField(
        max_length=254, default="", blank=True
    )  # messages.message[0].text or transactionResponse.messages.message[0].description
    responseCode = models.CharField(
        max_length=32, default="", blank=True
    )  # transactionResponse.responseCode
    authCode = models.CharField(
        max_length=6, default="", blank=True
    )  # transactionResponse.authCode
    avsResultCode = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.avsResultCode
    cvvResultCode = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.cvvResultCode
    cavvResultCode = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.cavvResultCode
    networkTransId = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.networkTransId
    accountNumber = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.accountNumber
    accountType = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.accountType
    error = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.errors.error[0].errorCode
    errorText = models.CharField(
        max_length=254, default="", blank=True
    )  # transactionResponse.errors.error[0].errorText

    def getResults(self):
        result = {
            "result": str(self.result),
            "created_at": str(self.created_at),
            "invoiceID": str(self.invoiceID),
            "refID": str(self.refID),
            "amount": str(self.amount),
            "salesperson": str(self.salesperson),
            "submitted": str(self.submitted),
            "transId": str(self.transID),
            "resultStatus": str(self.resultStatus),
            "resultCode": str(self.resultCode),
            "resultText": str(self.resultText),
            "responseCode": str(self.responseCode),
            "authCode": str(self.authCode),
            "avsResultCode": str(self.avsResultCode),
            "cvvResultCode": str(self.cvvResultCode),
            "cavvResultCode": str(self.cavvResultCode),
            "networkTransId": str(self.networkTransId),
            "accountNumber": str(self.accountNumber),
            "accountType": str(self.accountType),
            "error": str(self.error),
            "errorText": str(self.errorText),
        }
        return result
