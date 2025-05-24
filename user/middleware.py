from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from .models import SignUP, UpdatedUser, SuperAdmin

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths exempt from middleware checks
        exempt_paths = [
            reverse('signUp'),
            reverse('userSignIn'),
            reverse('adminSignIn'),
            reverse('forgotPassword'),
            reverse('termsCondition'),
            '/',  # AdminSignIn page, not homepage
        ]

        # Paths accessible to logged-in users without a subscription
        accessible_without_subscription = [
            reverse('selectPlan'),
            reverse('paymentSuccess'),
        ]

        # Exempt paths with dynamic segments
        if request.path.startswith('/resetPassword/'):
            return self.get_response(request)
            
        # Allow access to the Django admin panel and exempted paths
        if request.path.startswith('/adminadmin/') or request.path in exempt_paths:
            return self.get_response(request)

        # Retrieve the session data
        user = request.session.get('userID')
        subAdmin = request.session.get('subAdminID')
        superAdmin = request.session.get('superAdminID')

        # Redirect to the appropriate sign-in page if no user is logged in
        if not user and not subAdmin and not superAdmin:
            return redirect('adminSignIn')  # Redirect to adminSignIn ('/')

        # Check if the logged-in user (subAdmin/user/superAdmin) is active and has a subscription
        if subAdmin:
            try:
                logged_in_user = SignUP.objects.get(subAdminID=subAdmin)

                if not logged_in_user.isActive:
                    # If the account is deactivated
                    logout(request)
                    messages.error(request, "Your account has been deactivated. Please contact the admin.")
                    return redirect('adminSignIn')

                if logged_in_user.freeUser:
                    # Allow access to free users
                    return self.get_response(request)

                if not logged_in_user.hasChosenPlan:
                    # Allow access only to `selectPlan` and `paymentSuccess` pages
                    if request.path not in accessible_without_subscription:
                        messages.error(request, "Your subscription plan is expired. Please select a subscription plan to continue.")
                        return redirect('selectPlan')

            except SignUP.DoesNotExist:
                # If the subAdmin record is not found, log them out
                logout(request)
                messages.error(request, "Account does not exist.")
                return redirect('adminSignIn')

        elif user:
            try:
                logged_in_user = UpdatedUser.objects.get(userID=user)
                if not logged_in_user.isActive:
                    # If the account is deactivated
                    logout(request)
                    messages.error(request, "Your account has been deactivated. Please contact the admin.")
                    return redirect('userSignIn')
                
                if not logged_in_user.subAdminID.hasChosenPlan:
                    if request.path not in accessible_without_subscription:
                        messages.error(request, "Your subscription plan is expired. Please contact the admin.")
                        return redirect('userSignIn')

            except UpdatedUser.DoesNotExist:
                # If the user record is not found, log them out
                logout(request)
                messages.error(request, "User does not exist.")
                return redirect('userSignIn')

        elif superAdmin:
            try:
                logged_in_user = SuperAdmin.objects.get(superAdminID=superAdmin)
                if not logged_in_user.isActive:
                    # If the account is deactivated
                    logout(request)
                    messages.error(request, "Your account has been deactivated. Please contact the admin.")
                    return redirect('adminSignIn')

            except SuperAdmin.DoesNotExist:
                # If the superAdmin record is not found, log them out
                logout(request)
                messages.error(request, "Super admin does not exist.")
                return redirect('adminSignIn')

        # If the subAdmin has a subscription, continue processing the request
        response = self.get_response(request)
        return response
