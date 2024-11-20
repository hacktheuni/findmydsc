from django.urls import path
from . import views

urlpatterns = [
    path('', views.listDSC, name='listDSC'),
    path('listDSC', views.listDSC, name='listDSC'),
    path('listCompany', views.listCompany, name='listCompany'),
    path('listGroup', views.listGroup, name='listGroup'),
    path('listClient', views.listClient, name='listClient'),
    path('addDSC', views.addDSC, name='addDSC'),
    path('addCompany', views.addCompany, name='addCompany'),
    path('addGroup', views.addGroup, name='addGroup'),
    path('addClient', views.addClient, name='addClient'),
    path('updateDSC/<int:dscID>/', views.updateDSC, name='updateDSC'),
    path('updateCompany/<int:companyID>/', views.updateCompany, name='updateCompany'),
    path('updateGroup/<int:groupID>/', views.updateGroup, name='updateGroup'),
    path('updateClient/<int:clientID>/', views.updateClient, name='updateClient'),
    path('deleteDSC', views.deleteDSC, name='deleteDSC'),
    path('deleteCompany', views.deleteCompany, name='deleteCompany'),
    path('deleteGroup', views.deleteGroup, name='deleteGroup'),
    path('deleteClient', views.deleteClient, name='deleteClient'),
    path('feedBack', views.feedBack, name='feedBack'),
    path('fetchGroupName', views.fetchGroupName, name='fetchGroupName'),
    path('updatePassword', views.updatePassword, name='updatePassword'),
]