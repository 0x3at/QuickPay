from django.urls import path
from . import views

urlpatterns = [
    path(route="", view=views.dashboard, name="dashboard"),
    path(route="payment", view=views.portal, name="portal"),
    path(route="processQuickPay/", view=views.processQuickPay, name="process"),
    path(
        route="createProfile/",
        view=views.create_customer_profile,
        name="createProfile",
    ),
    path(
        route="addPaymentMethod/",
        view=views.add_payment_method,
        name="addPaymentMethod",
    ),
    path(
        route="getProfile/",
        view=views.get_customer_profile,
        name="getProfile",
    ),
    path(
        route="processProfilePayment/",
        view=views.process_profile_payment,
        name="processProfilePayment",
    ),
    path(route="getClients/", view=views.getClients, name="getClients"),
]
