from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("payment", views.payment, name="payment"),
    path("client/create", views.createClientProfile, name="createProfile"),
    path("client/get", views.getClient, name="getAllClients"),
    path("client/profiles/add", views.addPaymentMethod, name="addPaymentMethod"),
    path("client/transactions/charge", views.chargeCard, name="chargeCard"),
    path("client/profiles/charge", views.chargeProfile, name="chargeProfile"),
    path("client/notes/add", views.addNote, name="addNote"),
    path("client/notes/get", views.getNotes, name="getNotes"),
    path("client/details", views.clientDetails, name="clientDetails"),
    path("client/profile", views.clientProfile, name="clientProfile"),
]
