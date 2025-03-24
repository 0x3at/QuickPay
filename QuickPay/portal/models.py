from datetime import datetime
import os
import uuid
from django.db import models
from authorizenet import apicontractsv1 as authApi
from authorizenet.apicontrollers import (
    createTransactionController,
    createCustomerProfileController,
    createCustomerPaymentProfileController,
    getCustomerProfileController,
)
from dotenv import load_dotenv
from rich import print
import json

load_dotenv()


class PaymentProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=128)
    clientID = models.IntegerField(null=True)
    companyName = models.CharField(null=True, max_length=128)
    firstName = models.CharField(null=True, max_length=128)
    lastName = models.CharField(null=True, max_length=128)
    address = models.CharField(null=True, max_length=128)
    zipCode = models.CharField(null=True, max_length=128)
    email = models.CharField(null=True, max_length=32)
    customerType = models.CharField(null=True, max_length=32, default="Business")
    customerProfileID = models.CharField(null=True, max_length=12)
    paymentProfileID = models.CharField(null=True, max_length=16)
    status = models.CharField(null=True, max_length=32, default="Active")

    @staticmethod
    def createPaymentProfile(
        firstName,
        lastName,
        address,
        zipCode,
        email,
        companyName,
        customerType="business",
        clientID=None,
        created_by="System",
    ):
        """Create a customer profile and payment profile in Authorize.net"""
        print(
            f"Creating payment profile for {firstName} {lastName}, clientID: {clientID}, company: {companyName}"
        )

        # Create a new PaymentProfile record
        profile = PaymentProfile(
            firstName=firstName,
            lastName=lastName,
            address=address,
            zipCode=zipCode,
            email=email,
            companyName=companyName,
            customerType=customerType,
            clientID=clientID,
            created_by=created_by,
        )
        profile.save()
        print(f"Local profile saved with ID: {profile.clientID}")

        # Create customer profile in Authorize.net
        merchantAuth = Transaction.getAuthType()

        # Create customer info
        customerInfo = authApi.customerDataType()
        customerInfo.email = email
        customerInfo.type = customerType

        # Create customer shipping address
        customerAddress = authApi.customerAddressType()
        customerAddress.firstName = firstName
        customerAddress.lastName = lastName
        customerAddress.address = address
        customerAddress.zip = zipCode

        # Create customer profile
        customerProfile = authApi.customerProfileType()
        customerProfile.merchantCustomerId = (
            f"{clientID}" if clientID else f"{companyName}"
        )
        customerProfile.email = email
        customerProfile.description = f"Profile for {companyName}"

        # Prepare the request
        request = authApi.createCustomerProfileRequest()
        request.merchantAuthentication = merchantAuth
        request.profile = customerProfile

        print(f"Sending customer profile request to Authorize.net for {email}")

        # Create controller and execute
        controller = createCustomerProfileController(request)
        controller.execute()

        # Get the response
        response = controller.getresponse()
        print(f"Received response from Authorize.net: {response.messages.resultCode}")  # type: ignore

        if response is not None and response.messages.resultCode == "Ok":
            # Save customer profile ID
            profile.customerProfileID = response.customerProfileId
            profile.save()
            print(
                f"Success! Customer profile created with ID: {response.customerProfileId}"
            )
            return profile
        else:
            # Handle error
            profile.status = "Error"
            profile.save()
            if (
                response is not None
                and hasattr(response, "messages")
                and hasattr(response.messages, "message")
            ):
                error_msg = response.messages.message[0].text
                print(f"Error creating customer profile: {error_msg}")
                return {"error": error_msg}
            print("Error creating customer profile: Unknown error")
            return {"error": "Failed to create customer profile"}

    def addPaymentMethod(self, cardDetails):
        """Add a payment method to an existing customer profile"""
        print(
            f"Adding payment method to profile for {self.firstName} {self.lastName}, ProfileID: {self.customerProfileID}"
        )

        if not self.customerProfileID:
            print("Error: No customer profile exists")
            return {"error": "No customer profile exists"}

        # Get merchant authentication
        merchantAuth = Transaction.getAuthType()

        # Create credit card
        creditCard = authApi.creditCardType()
        creditCard.cardNumber = cardDetails["cardNumber"]
        creditCard.expirationDate = cardDetails["expirationDate"]
        creditCard.cardCode = cardDetails["cardCode"]
        print(
            f"Card info prepared: {cardDetails['cardNumber'][-4:]} exp: {cardDetails['expirationDate']}"
        )

        # Create payment
        payment = authApi.paymentType()
        payment.creditCard = creditCard

        # Create payment profile
        paymentProfile = authApi.customerPaymentProfileType()
        paymentProfile.payment = payment

        # Billing address
        billTo = authApi.customerAddressType()
        billTo.firstName = self.firstName
        billTo.lastName = self.lastName
        billTo.address = self.address
        billTo.zip = self.zipCode
        paymentProfile.billTo = billTo

        # Create request
        request = authApi.createCustomerPaymentProfileRequest()
        request.merchantAuthentication = merchantAuth
        request.customerProfileId = self.customerProfileID
        request.paymentProfile = paymentProfile
        request.validationMode = "testMode"  # or "testMode" for testing

        print(
            f"Sending payment profile request to Authorize.net for customer: {self.customerProfileID}"
        )

        # Create controller and execute
        controller = createCustomerPaymentProfileController(request)
        controller.execute()

        # Get response
        response = controller.getresponse()
        print(
            f"Received payment profile response: {response.messages.resultCode if response else 'None'}"
        )

        if response is not None and response.messages.resultCode == "Ok":
            # Save payment profile ID
            self.paymentProfileID = response.customerPaymentProfileId
            self.save()
            print(
                f"Success! Payment profile created with ID: {response.customerPaymentProfileId}"
            )
            return {"success": True, "paymentProfileID": str(self.paymentProfileID)}
        else:
            if (
                response is not None
                and hasattr(response, "messages")
                and hasattr(response.messages, "message")
            ):
                error_msg = response.messages.message[0].text
                print(f"Error creating payment profile: {str(error_msg)}")
                return {"error": str(error_msg)}
            print("Error creating payment profile: Unknown error")
            return {"error": "Failed to create payment profile"}

    @staticmethod
    def getCustomerProfile(customerProfileID):
        """Retrieve a customer profile from Authorize.net"""
        merchantAuth = Transaction.getAuthType()

        # Create request
        request = authApi.getCustomerProfileRequest()
        request.merchantAuthentication = merchantAuth
        request.customerProfileId = customerProfileID

        # Create controller and execute
        controller = getCustomerProfileController(request)
        controller.execute()

        # Get response
        response = controller.getresponse()

        if response is not None and response.messages.resultCode == "Ok":
            return response
        else:
            if (
                response is not None
                and hasattr(response, "messages")
                and hasattr(response.messages, "message")
            ):
                error_msg = response.messages.message[0].text
                return {"error": error_msg}
            return {"error": "Failed to retrieve customer profile"}

    def chargeProfilePayment(self, amount, invoiceID=None, description=None):
        """Process a payment using stored customer payment profile"""
        if not self.customerProfileID or not self.paymentProfileID:
            return {"error": "Missing customer or payment profile ID"}
        
        # Create a unique invoiceID if not provided
        if not invoiceID:
            invoiceID = str(uuid.uuid4())[:16]
        
        # Generate reference ID
        refID = str(datetime.now().timestamp())
        
        # Create transaction record
        tx = Transaction(
            invoiceID=invoiceID,
            refID=refID,
            amount=amount,
            salesperson=self.created_by
        )
        tx.save()
        
        # Get merchant authentication
        merchantAuth = Transaction.getAuthType()
        
        # Create a customer profile payment type
        profileToCharge = authApi.customerProfilePaymentType()
        profileToCharge.customerProfileId = self.customerProfileID
        profileToCharge.paymentProfile = authApi.paymentProfile()
        profileToCharge.paymentProfile.paymentProfileId = self.paymentProfileID
        
        # Create transaction request
        txRequest = authApi.createTransactionRequest()
        txRequest.merchantAuthentication = merchantAuth
        txRequest.refId = refID
        
        # Create transaction type
        txType = authApi.transactionRequestType()
        txType.transactionType = "authCaptureTransaction"
        txType.amount = amount
        txType.profile = profileToCharge
        
        # Add order information if needed
        if description or invoiceID:
            order = Transaction.getOrderType(invoiceID)
            if description:
                order.description = description
            txType.order = order
        
        txRequest.transactionRequest = txType
        
        # Create controller and execute
        controller = createTransactionController(txRequest)
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

        if response is not None:
            if hasattr(response, "messages"):
                tx.resultStatus = getattr(response.messages, "resultCode", None)

                if (
                    hasattr(response.messages, "message")
                    and len(response.messages.message) > 0
                ):
                    msg = response.messages.message[0]
                    tx.resultCode = getattr(msg, "code", None)
                    tx.resultText = getattr(msg, "text", None)

            if hasattr(response, "transactionResponse"):
                tx_resp = response.transactionResponse
                tx.responseCode = str(getattr(tx_resp, "responseCode", None))
                tx.transId = getattr(tx_resp, "transId", None)

                if tx.responseCode == "1":
                    tx.result = "Success"
                    tx.save()
                    return tx.getResults()
                else:
                    tx.result = "Failed"
                    # Get error details (similar to Transaction.processTransaction)
                    # ...

            tx.save()
            return {
                "error": str(tx.error) or "UNKNOWN_ERROR",
                "errorText": str(tx.errorText) or "Transaction failed",
            }
        else:
            tx.result = "Error"
            tx.error = "NO_RESPONSE"
            tx.errorText = "No response from payment gateway"
            tx.save()
            return {
                "error": "NO_RESPONSE",
                "errorText": "No response from payment gateway",
            }


# Create your models here.
class Transaction(models.Model):
    result = models.CharField(max_length=64, default="Not Submitted")
    clientID = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    invoiceID = models.CharField(max_length=16)
    transId = models.CharField(max_length=254, null=True, blank=True)
    refID = models.CharField(max_length=64)
    amount = models.CharField(max_length=64)
    salesperson = models.CharField(max_length=254)
    submitted = models.BooleanField(default=False)
    resultStatus = models.CharField(
        max_length=8, null=True, blank=True
    )  # messages.resultCode
    resultCode = models.CharField(
        max_length=16, null=True, blank=True
    )  # messages.message[0].code
    resultNumber = models.CharField(
        max_length=16, null=True, blank=True
    )  # transactionResponse.messages.message[0].code
    resultText = models.CharField(
        max_length=254, null=True, blank=True
    )  # messages.message[0].text or transactionResponse.messages.message[0].description
    responseCode = models.CharField(
        max_length=32, null=True, blank=True
    )  # transactionResponse.responseCode
    authCode = models.CharField(
        max_length=6, null=True, blank=True
    )  # transactionResponse.authCode
    avsResultCode = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.avsResultCode
    cvvResultCode = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.cvvResultCode
    cavvResultCode = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.cavvResultCode
    networkTransId = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.networkTransId
    accountNumber = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.accountNumber
    accountType = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.accountType
    error = models.CharField(
        max_length=254, null=True, blank=True
    )  # transactionResponse.errors.error[0].errorCode
    errorText = models.CharField(
        max_length=254, null=True, blank=True
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
            "transId": str(self.transId),
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
        print(result)
        return result

    @staticmethod
    def getAuthType():
        authType = authApi.merchantAuthenticationType()
        authType.name = os.getenv("AUTH_NET_ID")
        authType.transactionKey = os.getenv("AUTH_NET_TK")
        return authType

    @staticmethod
    def getCardType(number, expiration, cvv):
        creditCard = authApi.creditCardType()
        creditCard.cardNumber = number
        creditCard.expirationDate = expiration
        creditCard.cardCode = cvv
        return creditCard

    @staticmethod
    def getOrderType(invoiceID):
        orderType = authApi.orderType()
        orderType.invoiceNumber = invoiceID
        orderType.description = "Autocommunications through WholeSale Communications"
        return orderType

    @staticmethod
    def getTransactionType(amount, creditCard, order):
        payment = authApi.paymentType()
        payment.creditCard = creditCard
        txType = authApi.transactionRequestType()
        txType.transactionType = "authCaptureTransaction"
        txType.amount = amount
        txType.currencyCode = "USD"
        txType.payment = payment
        txType.order = order
        return txType

    @staticmethod
    def processTransaction(amount, cardDetails, salesperson):
        print(
            f"Processing transaction for {amount} with card {cardDetails['cardNumber']} expiring {cardDetails['expirationDate']} and cvv {cardDetails['cardCode']}"
        )

        # Initialize Transaction Record
        invoiceID = str(uuid.uuid4())[:16]
        refID = str(datetime.now().timestamp())
        tx = Transaction(
            invoiceID=invoiceID, refID=refID, amount=amount, salesperson=salesperson
        )
        tx.save()

        # Initialize the transaction request
        creditCard = Transaction.getCardType(
            cardDetails["cardNumber"],
            cardDetails["expirationDate"],
            cardDetails["cardCode"],
        )
        order = Transaction.getOrderType(invoiceID=invoiceID)
        txRequest = authApi.createTransactionRequest()
        txRequest.merchantAuthentication = Transaction.getAuthType()
        txRequest.refId = refID
        txRequest.transactionRequest = Transaction.getTransactionType(
            amount,
            creditCard,
            order,
        )

        # Execute the request
        controller = createTransactionController(txRequest)
        controller.execute()
        tx.submitted = True
        tx.result = "Submitted"
        tx.save()

        response = controller.getresponse()

        if response is not None:
            # Extract main messages fields
            if hasattr(response, "messages"):
                # resultStatus = messages.resultCode
                tx.resultStatus = getattr(response.messages, "resultCode", None)
                # Print response in nice format
                print("\n=== AUTHORIZE.NET RESPONSE ===")
                if tx.resultStatus == "Ok":
                    Transaction.printSuccessResponse(response)
                else:
                    Transaction.printError(response)
                print("===============================\n")

                # Extract from main messages
                if (
                    hasattr(response.messages, "message")
                    and len(response.messages.message) > 0
                ):
                    msg = response.messages.message[0]
                    # resultCode = messages.message[0].code
                    tx.resultCode = getattr(msg, "code", None)
                    # resultText (part 1) = messages.message[0].text
                    tx.resultText = getattr(msg, "text", None)

            # Extract transaction response fields
            if hasattr(response, "transactionResponse"):
                tx_resp = response.transactionResponse

                # responseCode = transactionResponse.responseCode
                tx.responseCode = str(getattr(tx_resp, "responseCode", None))
                # authCode = transactionResponse.authCode
                tx.authCode = getattr(tx_resp, "authCode", None)
                # avsResultCode = transactionResponse.avsResultCode
                tx.avsResultCode = getattr(tx_resp, "avsResultCode", None)
                # cvvResultCode = transactionResponse.cvvResultCode
                tx.cvvResultCode = getattr(tx_resp, "cvvResultCode", None)
                # cavvResultCode = transactionResponse.cavvResultCode
                tx.cavvResultCode = getattr(tx_resp, "cavvResultCode", None)
                # networkTransId = transactionResponse.networkTransId
                tx.networkTransId = getattr(tx_resp, "networkTransId", None)
                # accountNumber = transactionResponse.accountNumber
                tx.accountNumber = getattr(tx_resp, "accountNumber", None)
                # accountType = transactionResponse.accountType
                tx.accountType = getattr(tx_resp, "accountType", None)
                # transId = transactionResponse.transId
                tx.transId = getattr(tx_resp, "transId", None)

                # Get transaction messages if available
                if hasattr(tx_resp, "messages") and hasattr(
                    tx_resp.messages, "message"
                ):
                    if len(tx_resp.messages.message) > 0:
                        tx_msg = tx_resp.messages.message[0]
                        # resultNumber = transactionResponse.messages.message[0].code
                        tx.resultNumber = getattr(tx_msg, "code", None)
                        # resultText (part 2) = transactionResponse.messages.message[0].description
                        # Only set resultText from here if it's not already set from messages.message
                        if not tx.resultText:
                            tx.resultText = getattr(tx_msg, "description", None)

                # Get error information if it exists
                if hasattr(tx_resp, "errors") and hasattr(tx_resp.errors, "error"):
                    if len(tx_resp.errors.error) > 0:
                        err = tx_resp.errors.error[0]
                        # error = transactionResponse.errors.error[0].errorCode
                        tx.error = getattr(err, "errorCode", None)
                        # errorText = transactionResponse.errors.error[0].errorText
                        tx.errorText = getattr(err, "errorText", None)

            if tx.responseCode == "1":
                tx.result = "Success"
                tx.save()
                return tx.getResults()
            else:
                tx.result = "Failed"

                # Get specific error details from transactionResponse if available
                if hasattr(response, "transactionResponse") and hasattr(
                    response.transactionResponse, "errors"
                ):
                    tx_resp = response.transactionResponse
                    if hasattr(tx_resp.errors, "error"):
                        if (
                            isinstance(tx_resp.errors.error, list)
                            and len(tx_resp.errors.error) > 0
                        ):
                            err = tx_resp.errors.error[0]
                            tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )
                        elif not isinstance(tx_resp.errors.error, list):
                            err = tx_resp.errors.error
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
            tx.result = "Error"
            tx.error = "NO_RESPONSE"
            tx.errorText = "No response from payment gateway"
            tx.save()

            return {
                "error": "NO_RESPONSE",
                "errorText": "No response from payment gateway",
            }

    @staticmethod
    def print_object_recursively(obj, indent=0, max_depth=3, visited=None):
        """
        Recursively print all attributes of an object, handling circular references
        and limiting recursion depth to provide readable debugging output.

        Args:
            obj: The object to print
            indent: Current indentation level (used for recursion)
            max_depth: Maximum depth to traverse
            visited: Set of already visited object IDs to prevent circular references

        Returns:
            A formatted string representation of the object
        """
        if visited is None:
            visited = set()

        # Avoid circular references
        obj_id = id(obj)
        if obj_id in visited:
            return f"<circular reference to {type(obj).__name__}>"

        # Limit recursion depth
        if indent > max_depth * 2:
            return f"{type(obj).__name__} (max depth reached)"

        visited.add(obj_id)
        pad = "  " * indent

        # Different handling based on object type
        if isinstance(obj, (str, int, float, bool, type(None))):
            return str(obj)
        elif isinstance(obj, (list, tuple)):
            items = [
                f"{pad}  {i}: {Transaction.print_object_recursively(x, indent + 2, max_depth, visited.copy())}"
                for i, x in enumerate(obj)
            ]
            return (
                f"[{', '.join(items)}]"
                if not items
                else f"\n{pad}[\n" + "\n".join(items) + f"\n{pad}]"
            )
        elif isinstance(obj, dict):
            items = [
                f"{pad}  {k}: {Transaction.print_object_recursively(v, indent + 2, max_depth, visited.copy())}"
                for k, v in obj.items()
            ]
            return (
                f"{{{', '.join(items)}}}"
                if not items
                else f"\n{pad}{{\n" + "\n".join(items) + f"\n{pad}}}"
            )
        else:
            # For custom objects
            result = [f"{pad}{type(obj).__name__}:"]
            for attr_name in dir(obj):
                if not attr_name.startswith("_"):  # Skip private attributes
                    try:
                        value = getattr(obj, attr_name)
                        if not callable(value):  # Skip methods
                            value_str = Transaction.print_object_recursively(
                                value, indent + 1, max_depth, visited.copy()
                            )
                            result.append(f"{pad}  {attr_name}: {value_str}")
                    except Exception as attr_error:
                        result.append(f"{pad}  {attr_name}: <error: {str(attr_error)}>")
            return "\n".join(result)

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
        print(json.dumps(result, indent=2, default=str))
        return result

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
        print(json.dumps(result, indent=2, default=str))
        return result
