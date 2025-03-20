from datetime import datetime
import os
import uuid
from django.db import models
from authorizenet import apicontractsv1 as authApi
from authorizenet.apicontrollers import createTransactionController
from dotenv import load_dotenv
from rich import print
import json

load_dotenv()


class PaymentProfile(models.Model):
    processor = models.CharField(max_length=2,default="A")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=128)
    clientID = models.IntegerField(null=True)
    clientName = models.CharField(null=True,max_length=128)
    email = models.CharField(null=True,max_length=32)
    customerType = models.CharField(null=True,max_length=32, default="Business")
    customerProfile = models.CharField(null=True,max_length=12)
    paymentProfileID = models.CharField(null=True,max_length=16)
    status= models.CharField(null=True,max_length=32,default="Active")


# Create your models here.
class Transaction(models.Model):
    processor = models.CharField(max_length=2)
    result = models.CharField(max_length=64, default="Not Submitted")
    created_at = models.DateTimeField(auto_now_add=True)
    invoiceID = models.CharField(max_length=16)
    refID = models.CharField(max_length=64)
    transId = models.CharField(max_length=254, null=True, blank=True)
    amount = models.CharField(max_length=64)
    salesperson = models.CharField(max_length=128)
    submitted = models.BooleanField(default=False)  # type:ignore
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

    def getResults(self) -> dict[str, str]:
        result = {
            "processor": str(self.processor),
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
            "networkTransId": str(self.networkTransId),
            "accountType": str(self.accountType),
            "error": str(self.error),
            "errorText": str(self.errorText),
        }
        print(result)
        return result

    @staticmethod
    def process(
        processor: str, amount: float, salesperson: str, cardDetails: dict[str, str]
    ):
        strategies = {
            # Auth.net
            "A": {
                "keys": {"name": "SB_AUTH_NET_ID", "key": "SB_AUTH_NET_ID"},
                "strategy": AuthNetStrategy,
            },
            # Stripe
            "S": {"strategy": AuthNetStrategy, "keys": {"key": ""}},
        }
        try:
            (
                strategies.get(processor, {})
                .get("strategy", {})(
                    amount=amount,
                    salesperson=salesperson,
                    keys=strategies.get(processor, {}).get("keys", {}),
                    cardDetails=cardDetails,
                )
                .process()
            )
        except Exception as e:
            print(e)
            return e


class AuthNetStrategy:
    def __init__(
        self,
        amount: float,
        salesperson: str,
        keys: dict[str, str],
        cardDetails: dict[str, str],
    ):
        self.tx: Transaction = Transaction(
            processor="A",
            amount=str(amount),
            salesperson=salesperson,
            invoiceID=str(uuid.uuid4())[:16],
            refID=(str(datetime.now().timestamp())).split(".")[0],
        )
        self.__keys: dict[str, str] = keys
        self.__cardDetails: dict[str, str] = cardDetails

    @property
    def __authType(self):
        authType = authApi.merchantAuthenticationType()
        authType.name = os.getenv(self.__keys["name"])
        authType.transactionKey = os.getenv(self.__keys["key"])
        return authType

    @property
    def __cardType(self):
        creditCard = authApi.creditCardType()
        creditCard.cardNumber = self.__cardDetails["number"]
        creditCard.expirationDate = self.__cardDetails["expiration"]
        creditCard.cardCode = self.__cardDetails["cvv"]
        return creditCard

    @property
    def __orderType(self):
        orderType = authApi.orderType()
        orderType.invoiceNumber = self.tx.invoiceID
        orderType.description = "Autocommunications through WholeSale Communications"
        return orderType

    @property
    def __paymentType(self):
        payment = authApi.paymentType()
        payment.creditCard = self.__cardType
        return payment

    @property
    def __transactionType(self):
        txType = authApi.transactionRequestType()
        txType.transactionType = "authCaptureTransaction"
        txType.amount = self.tx.amount
        txType.currencyCode = "USD"
        txType.payment = self.__paymentType
        txType.order = self.__orderType
        return txType

    @property
    def __transactionRequest(self):
        txRequest = authApi.createTransactionRequest()
        txRequest.refId = self.tx.refID
        txRequest.merchantAuthentication = self.__authType
        txRequest.transactionRequest = self.__transactionType
        return txRequest

    @property
    def __controller(self):
        controller = createTransactionController(self.__transactionRequest)
        return controller

    def process(self):
        self.__controller.execute()
        self.tx.submitted = True
        self.tx.save()
        response = self.__controller.getresponse()
        if response is not None:
            # REFACTOR COUNTER : 4
            # auth.net sdk and api fucking suck
            if hasattr(response, "messages"):
                self.tx.resultStatus = getattr(response.messages, "resultCode", None)
                print("\n=== AUTHORIZE.NET RESPONSE ===")
                if self.tx.resultStatus == "Ok":
                    AuthNetStrategy.printSuccessResponse(response)
                else:
                    AuthNetStrategy.printError(response)
                print("===============================\n")

                if (
                    hasattr(response.messages, "message")
                    and len(response.messages.message) > 0
                ):
                    msg = response.messages.message[0]
                    self.tx.resultCode = getattr(msg, "code", None)
                    self.tx.resultText = getattr(msg, "text", None)
            if hasattr(response, "transactionResponse"):
                tx_resp = response.transactionResponse
                self.tx.responseCode = str(getattr(tx_resp, "responseCode", None))
                self.tx.authCode = getattr(tx_resp, "authCode", None)
                self.tx.avsResultCode = getattr(tx_resp, "avsResultCode", None)
                self.tx.cvvResultCode = getattr(tx_resp, "cvvResultCode", None)
                self.tx.cavvResultCode = getattr(tx_resp, "cavvResultCode", None)
                self.tx.networkTransId = getattr(tx_resp, "networkTransId", None)
                self.tx.accountNumber = getattr(tx_resp, "accountNumber", None)
                self.tx.accountType = getattr(tx_resp, "accountType", None)
                self.tx.transId = getattr(tx_resp, "transId", None)
                self.tx.save()
                if hasattr(tx_resp, "messages") and hasattr(
                    tx_resp.messages, "message"
                ):
                    if len(tx_resp.messages.message) > 0:
                        tx_msg = tx_resp.messages.message[0]
                        self.tx.resultNumber = getattr(tx_msg, "code", None)
                        if not self.tx.resultText:
                            self.tx.resultText = getattr(tx_msg, "description", None)
                        self.tx.save()

                if hasattr(tx_resp, "errors") and hasattr(tx_resp.errors, "error"):
                    if len(tx_resp.errors.error) > 0:
                        err = tx_resp.errors.error[0]
                        self.tx.error = getattr(err, "errorCode", None)
                        self.tx.errorText = getattr(err, "errorText", None)
                        self.tx.save()

            if self.tx.responseCode == "1":
                self.tx.result = "Success"
                self.tx.save()
                return self.tx.getResults()

            else:
                self.tx.result = "Failed"

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
                            self.tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            self.tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )
                        elif not isinstance(tx_resp.errors.error, list):
                            err = tx_resp.errors.error
                            self.tx.error = getattr(err, "errorCode", "UNKNOWN_ERROR")
                            self.tx.errorText = getattr(
                                err, "errorText", "Unknown error occurred"
                            )

                if (
                    not self.tx.error
                    and hasattr(response, "messages")
                    and hasattr(response.messages, "message")
                ):
                    if len(response.messages.message) > 0:
                        msg = response.messages.message[0]
                        self.tx.error = getattr(msg, "code", "UNKNOWN_ERROR")
                        self.tx.errorText = getattr(
                            msg, "text", "Unknown error occurred"
                        )

            self.tx.save()
            return {
                "error": str(self.tx.error) or "UNKNOWN_ERROR",
                "errorText": str(self.tx.errorText) or "Transaction failed",
            }
        else:
            self.tx.result = "Error"
            self.tx.error = "NO_RESPONSE"
            self.tx.errorText = "No response from payment gateway"
            self.tx.save()

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
