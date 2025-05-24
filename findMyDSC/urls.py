from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('adminadmin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('admin/', include('admins.urls')),
    path('', views.adminSignIn, name='adminSignIn'),
    path('signUp/', views.signUp, name='signUp'),
    path('adminSignIn/', views.adminSignIn, name='adminSignIn'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetPassword/<str:token>', views.resetPassword, name='resetPassword'),
    path('userSignIn/', views.userSignIn, name='userSignIn'),
    path('logOut/', views.logOut, name='logOut'),
    path('termsCondition/', views.termsCondition, name='termsCondition'),
    path('plan/selectPlan', views.selectPlan, name='selectPlan'),
    path('plan/pay/paymentSuccess/', views.paymentSuccess, name='paymentSuccess'),
] 

if settings.DEBUG:  # Only serve static files when in DEBUG mode
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
