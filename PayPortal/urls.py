from django.urls import path
from . import views

urlpatterns = [
    path("client/create", views.createClientProfile, name="createProfile"),
    path("client/get", views.getClient, name="getAllClients"),
    path("client/profiles/add", views.addPaymentMethod, name="addPaymentMethod"),
    path("client/transactions/charge", views.chargeCard, name="chargeCard"),
    path("client/notes/add", views.addNote, name="addNote"),
    path("client/notes/get", views.getNotes, name="getNotes"),
]
