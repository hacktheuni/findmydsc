from django.urls import path
from . import views

urlpatterns = [
    # the urls for the subAdmin
    path('listUser', views.listUser, name='listUser'),
    path('addUser', views.addUser, name='addUser'),
    path('updateUser/<int:userID>/', views.updateUser, name='updateUser'),
    path('deleteUser', views.deleteUser, name='deleteUser'),
    path('updateProfile', views.updateProfile, name='updateProfile'),
    path('subscriptionDetails', views.subscriptionDetails, name='subscriptionDetails'),
    path('deleteProfile', views.deleteProfile, name='deleteProfile'),

    # the urls for the admin
    path('listSubAdmin', views.listSubAdmin, name='listSubAdmin'),
    path('listFeedback', views.listFeedback, name='listFeedback'),
    path('action', views.action, name='action'),
    path('exportData', views.exportData, name='exportData'),
    path('exportToExcel', views.exportToExcel, name='exportToExcel')
]

