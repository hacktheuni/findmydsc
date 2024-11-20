from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from .models import SignUP, UpdatedUser, SuperAdmin, SubAdminSubscription

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Adjusted exempt_paths to include '/' as adminSignIn
        exempt_paths = [
            reverse('signUp'),
            reverse('userSignIn'),
            reverse('adminSignIn'),
            '/',  # AdminSignIn page, not homepage
        ]

        # Allow access to the Django admin panel and exempted paths
        if request.path.startswith('/adminadmin/') or request.path in exempt_paths:
            return self.get_response(request)

        # Retrieve the session data
        user = request.session.get('userID')
        subAdmin = request.session.get('subAdminID')
        superAdmin = request.session.get('superAdminID')

        # Redirect to the appropriate sign-in page if no user is logged in
        if not user and not subAdmin and not superAdmin:
            if request.path.startswith('/admin/') or request.path.startswith('/plan/'):
                return redirect('adminSignIn')  # Redirect to adminSignIn ('/')
            elif request.path.startswith('/user/'):
                return redirect('userSignIn')

        # Check if the logged-in user (subAdmin/user/superAdmin) is active
        if user or subAdmin or superAdmin:
            try:
                # Check if subAdmin is logged in
                if subAdmin:
                    logged_in_user = SignUP.objects.get(subAdminID=subAdmin)

                    if not logged_in_user.isActive:
                        logout(request)
                        messages.error(request, "Your account has been deactivated. Please contact the admin.")
                        return redirect('adminSignIn')

                    if not logged_in_user.isIsActive:
                        logged_in_user.isIsActive = True
                        logged_in_user.save()
                        logout(request)
                        messages.error(request, "Your subscription has expired. Please renew your subscription.")
                        return redirect('adminSignIn')

                # Check if user is logged in
                elif user:
                    logged_in_user = UpdatedUser.objects.get(userID=user)
                    if not logged_in_user.isActive:
                        logout(request)
                        messages.error(request, "Your account has been deactivated. Please contact the admin.")
                        return redirect('userSignIn')

                # Check if superAdmin is logged in
                elif superAdmin:
                    logged_in_user = SuperAdmin.objects.get(superAdminID=superAdmin)
                    if not logged_in_user.isActive:
                        logout(request)
                        messages.error(request, "Your account has been deactivated. Please contact the admin.")
                        return redirect('adminSignIn')

            except (SignUP.DoesNotExist, UpdatedUser.DoesNotExist, SuperAdmin.DoesNotExist):
                # If the user record is not found, log them out and redirect to the login page
                logout(request)
                messages.error(request, "User does not exist.")
                return redirect('adminSignIn' if subAdmin or superAdmin else 'userSignIn')

        # Continue processing the request
        response = self.get_response(request)
        return response
