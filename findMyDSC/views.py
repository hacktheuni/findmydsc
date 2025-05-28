from django.shortcuts import render, redirect
from user.models import *
import re
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.core.cache import cache
import uuid

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def signUp(request):
    if request.method == 'POST':
        # Retrieve form data
        subAdminName = request.POST.get('subAdminName')
        subAdminType = request.POST.get('subAdminType')
        subAdminEmail = request.POST.get('subAdminEmail')
        subAdminPhone = request.POST.get('subAdminPhone')
        subAdminCity = request.POST.get('subAdminCity')
        subAdminState = request.POST.get('subAdminState')
        subAdminPinCode = request.POST.get('subAdminPinCode')
        subAdminPassword = request.POST.get('subAdminPassword')
        subAdminReferralEmail = request.POST.get('subAdminReferralEmail')
        freeUser = request.POST.get('freeUser')

        if freeUser == 'True':
            freeUser = True
        else:
            freeUser = False

        # Initial data to be passed back to the form
        form_data = {
            'subAdminName': subAdminName,
            'subAdminType': subAdminType,
            'subAdminEmail': subAdminEmail,
            'subAdminPhone': subAdminPhone,
            'subAdminCity': subAdminCity,
            'subAdminState': subAdminState,
            'subAdminPinCode': subAdminPinCode,
            'subAdminReferralEmail': subAdminReferralEmail,
        }

        # Validation checks
        if not all([subAdminName, subAdminType, subAdminEmail, subAdminPhone, subAdminCity, subAdminState, subAdminPinCode, subAdminPassword]):
            messages.error(request, "All fields are required.")
        elif SignUP.objects.filter(subAdminEmail=subAdminEmail).exists():
            messages.error(request, "Email already registered.")
            form_data['subAdminEmail'] = ''  # Clear the email field in case of error
        elif len(subAdminPhone) != 10 or not subAdminPhone.isdigit():
            messages.error(request, "Phone number must be exactly 10 digits.")
            form_data['subAdminPhone'] = ''  # Clear the phone field in case of error
        elif SignUP.objects.filter(subAdminPhone=subAdminPhone).exists():
            messages.error(request, "Phone number already registered.")
            form_data['subAdminPhone'] = ''  # Clear the phone field in case of error
        elif len(subAdminPassword) < 8 or not re.search(r'[A-Za-z]', subAdminPassword) or not re.search(r'\d', subAdminPassword) or not re.search(r'[@$!%*?&#]', subAdminPassword):
            messages.error(request, "Password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
        elif subAdminReferralEmail and not SignUP.objects.filter(subAdminEmail=subAdminReferralEmail).exists():
            messages.error(request, "Referral Email not registered.")
        else:
            # If validation passes, create and save SignUP instance
            subAdmin = SignUP(subAdminName=subAdminName, subAdminType=subAdminType, subAdminEmail=subAdminEmail, subAdminPhone=subAdminPhone, subAdminCity=subAdminCity, subAdminState=subAdminState, subAdminPinCode=subAdminPinCode, subAdminPassword=make_password(subAdminPassword),subAdminReferralEmail=subAdminReferralEmail, freeUser=freeUser)
            subAdmin.save()
            
            # Create corresponding UpdatedUser
            user = UpdatedUser(subAdminID=subAdmin,  userName='Admin',  userPhone=subAdminPhone,  userUsername=subAdminName,  userPassword=make_password(subAdminPassword),  isActive='False')
            user.save()

            group = UpdatedGroup(groupName='None', userID=user, subAdminID=subAdmin)
            group.save()

            groupHistory = HistoryGroup(groupID=group, groupName=group.groupName, userID=user, subAdminID=subAdmin, groupModifiedDate=group.groupModifiedDate)
            groupHistory.save()

            # Send welcome email
            send_mail(
                subject="Welcome to FIND MY DSC",
                message='''Dear Subscriber, 

Greetings from FIND MY DSC!! 
We take this opportunity to thank you for subscribing to us and welcome you to FIND MY DSC.

Let's start journey of managing all DSC without much hassle.

In case you need any assistance feel free to write to us-
findmydsc@gmail.com 

Regard''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subAdminEmail],
                fail_silently=False,
            )

            messages.success(request, "Account created successfully. Please sign in.")
            return redirect('adminSignIn')

        # Return the form with existing values except for the cleared fields
        return render(request, 'auth/signUp.html', {'form_data': form_data})

    return render(request, 'auth/signUp.html')

def userSignIn(request):
    if request.method == 'POST':
        subAdminEmail = request.POST.get('subAdminEmail')
        userUsername = request.POST.get('userUsername')
        userPassword = request.POST.get('userPassword')
        rememberMe = request.POST.get('rememberMe', None)

        # Prepare form data to retain entered values in case of error
        form_data = {
            'subAdminEmail': subAdminEmail,
            'userUsername': userUsername
        }

        # Validation checks for missing fields
        if not subAdminEmail:
            messages.error(request, "SubAdmin email is required.")
        elif not userUsername:
            messages.error(request, "Username is required.")
        elif not userPassword:
            messages.error(request, "Password is required.")
        else:
            try:
                subAdmin = SignUP.objects.get(subAdminEmail=subAdminEmail)
            except SignUP.DoesNotExist:
                messages.error(request, "SubAdmin not found.")
            else:
                # Check if subAdmin has an active subscription
                active_subscription = SubAdminSubscription.objects.filter(subAdminID=subAdmin, isActive=True).first()
                if not active_subscription:
                    messages.error(request, "Your subscription is inactive or has expired. Please contact your admin.")
                else:
                    # Fetch the user based on subAdmin and username
                    user = UpdatedUser.objects.filter(subAdminID=subAdmin, userUsername=userUsername).first()
                    if user:
                        # Check if the provided password matches the hashed password in the database
                        if check_password(userPassword, user.userPassword):
                            if user.isActive:
                                # Store user information in session
                                request.session['userID'] = user.userID
                                request.session['userName'] = user.userName

                                # Handle remember me functionality
                                if rememberMe:
                                    request.session.set_expiry(30 * 24 * 60 * 60)  # Session lasts for 30 days
                                else:
                                    request.session.set_expiry(0)  # Session expires on browser close

                                messages.success(request, f"Successfully logged in as {user.userName}.")
                                if user.isClientUser:
                                    if user.accessToPendingWork:
                                        return redirect('listPendingWork')
                                    elif user.accessToAnnual:
                                        return redirect('listAnnual')
                                    elif user.accessToTrademark:
                                        return redirect('listTrademark')
                                    else:
                                        messages.error(request, "Access denied: You are not allowed to view this page.")
                                        return redirect('userSignIn')
                                return redirect('listPendingWork')  # Redirect to user dashboard
                            else:
                                messages.error(request, "Your account is deactivated.")
                        else:
                            messages.error(request, "Invalid username or password.")
                    else:
                        messages.error(request, "Invalid username or password.")

        # If there were errors, return the form with the error messages and retained data
        return render(request, 'auth/userSignIn.html', {'form_data': form_data})

    return render(request, 'auth/userSignIn.html')

def adminSignIn(request):
    subAdminID = request.session.get('subAdminID')
    superAdminID = request.session.get('superAdminID')
    userID = request.session.get('userID')

    # Check if subAdmin is logged in, active, and has chosen a plan
    if subAdminID:
        subAdmin = SignUP.objects.filter(subAdminID=subAdminID, isActive=True).first()
        if subAdmin:
            if subAdmin.freeUser:
                return redirect('listDSC')
            if subAdmin.hasChosenPlan:
                return redirect('listPendingWork')
            messages.info(request, "Please choose a subscription plan.")
            return redirect('selectPlan')
        messages.error(request, "Your account is deactivated.")
        return redirect('adminSignIn')

    # Check if user is logged in and active
    if userID:
        user = UpdatedUser.objects.filter(userID=userID, isActive=True).first()
        if user:
            if user.isClientUser:
                if user.accessToPendingWork:
                    return redirect('listPendingWork')
                elif user.accessToAnnual:
                    return redirect('listAnnual')
                elif user.accessToTrademark:
                    return redirect('listTrademark')
                else:
                    messages.error(request, "Access denied: You are not allowed to view this page.")
                    return redirect('userSignIn')
            return redirect('listPendingWork')
        messages.error(request, "Your User account is deactivated.")
        return redirect('userSignIn')

    # If superAdmin is logged in, no need to check plan or activity
    if superAdminID:
        return redirect('listSubAdmin')

    # Handle POST request for login
    if request.method == 'POST':
        userID = request.POST.get('userID')
        password = request.POST.get('password')
        rememberMe = request.POST.get('rememberMe', None)

        # Validate form inputs
        if not userID:
            messages.error(request, "User ID or Email is required.")
        elif not password:
            messages.error(request, "Password is required.")
        else:
            # Try to authenticate subAdmin
            admin = SignUP.objects.filter(subAdminEmail=userID).first()

            if admin:
                if check_password(password, admin.subAdminPassword):  # Password check
                    if admin.isActive:
                        # Set session for subAdmin
                        request.session['subAdminID'] = admin.subAdminID
                        request.session['subAdminName'] = admin.subAdminName
                        _set_session_expiry(request, rememberMe)
 
                        if admin.freeUser:
                            messages.success(request, "Successfully logged in as Free User.")
                            return redirect('listDSC')

                        # Handle plan selection and subscription
                        if admin.isFirstLogin or not admin.hasChosenPlan:
                            if admin.hasUsedFreePlan:
                                messages.info(request, "You have already used the free plan. Please select a paid plan.")
                            return redirect('selectPlan')
                        else:
                            subscription = SubAdminSubscription.objects.filter(subAdminID=admin, isActive=True).first()
                            if subscription and subscription.is_subscription_active():
                                messages.success(request, f"Successfully logged in as {admin.subAdminName}.")
                                return redirect('listPendingWork')
                            messages.error(request, "Your subscription has expired. Please renew your subscription.")
                            return redirect('selectPlan')
                    else:
                        messages.error(request, "Your account is deactivated.")
                else:
                    messages.error(request, "Invalid password.")
            else:
                # Try to authenticate superAdmin if no subAdmin found
                admin = SuperAdmin.objects.filter(superAdminUserID=userID).first()
                if admin:
                    if check_password(password, admin.superAdminPassword):  # Password check
                        if admin.isActive:
                            # Set session for superAdmin
                            request.session['superAdminID'] = admin.superAdminID
                            _set_session_expiry(request, rememberMe)

                            messages.success(request, "Successfully logged in as SuperAdmin.")
                            return redirect('listSubAdmin')
                        messages.error(request, "Your SuperAdmin account is deactivated.")
                    else:
                        messages.error(request, "Invalid password.")
                else:
                    messages.error(request, "Invalid credentials.")

        return render(request, 'auth/adminSignIn.html')

    return render(request, 'auth/adminSignIn.html')

# Helper function to handle session expiry
def _set_session_expiry(request, rememberMe):
    if rememberMe:
        request.session.set_expiry(30 * 24 * 60 * 60)  # Session lasts 30 days
    else:
        request.session.set_expiry(0)  # Session expires on browser close


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = SignUP.objects.get(subAdminEmail=email)

            # Generate a unique token
            token = str(uuid.uuid4())
            cache.set(token, user.subAdminID, timeout=3600)  # Token valid for 1 hour

            reset_link = f'www.findmydsc.in/resetPassword/{token}'
            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n{reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'A password reset link has been sent to your email.')
        except SignUP.DoesNotExist:
            messages.error(request, "No user found with this email address.")
        return redirect(request.path)

    return render(request, 'auth/forgotPassword.html')

def resetPassword(request, token):
    user_id = cache.get(token)  # Retrieve the user ID from the cache using the token

    # Check if user_id is found
    if user_id is None:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('forgotPassword')  

    try:
        user = SignUP.objects.get(subAdminID=user_id)
    except SignUP.DoesNotExist:
        messages.error(request, "No user found for this reset link.")
        return redirect('forgotPassword')

    # Password validation function
    def validate_new_password(password):
        return (len(password) >= 8 and
                re.search(r'[A-Za-z]', password) and
                re.search(r'\d', password) and
                re.search(r'[@$!%*?&#]', password))

    if request.method == 'POST':
        newPassword = request.POST.get('newPassword')
        confirmPassword = request.POST.get('confirmPassword')

        if newPassword == confirmPassword:
            if validate_new_password(newPassword):
                user.subAdminPassword = make_password(newPassword)
                user.save()
                messages.success(request, 'Password changed successfully. Now log in with your new password.')
                # Optionally, delete the token from cache after use
                cache.delete(token)
                return redirect('adminSignIn')
            else:
                messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
        else:
            messages.error(request, 'New password and confirmation do not match.')

    return render(request, 'auth/resetPassword.html', {'user': user, 'token':token})


def logOut(request):
    if request.session.get('subAdminID') or request.session.get('superAdminID'):  
        logout(request)
        return redirect('adminSignIn')  
    
    elif request.session.get('userID'):
        logout(request)
        return redirect('userSignIn')
    
    else:
        logout(request)
        return redirect('adminSignIn')

@csrf_exempt
def selectPlan(request):
    subAdminID = request.session.get('subAdminID')
    subscriptionPlan = SubscriptionPlan.objects.all()
    if subAdminID:
        try:
            subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        except SignUP.DoesNotExist:
            messages.error(request, "SubAdmin not found. Please log in again.")
            return redirect('adminSignIn')
        if subAdmin.hasUsedFreePlan:
                subscriptionPlan = list(SubscriptionPlan.objects.all())
                subscriptionPlan.pop(0)

    if request.method == 'POST':
        selected_plan_id = request.POST.get('planID')

        # Validate if a plan was selected
        if not selected_plan_id:
            messages.error(request, "Please select a subscription plan.")
            return render(request, 'payment/selectPlan.html', {'subscriptionPlan': subscriptionPlan})

        try:
            # Validate if the selected plan exists
            selected_plan = SubscriptionPlan.objects.get(planID=selected_plan_id)

            # Validate if the subAdmin is logged in by checking the session
            subAdminID = request.session.get('subAdminID')
            if not subAdminID:
                messages.error(request, "You are not logged in. Please log in to continue.")
                return redirect('subAdminLogin')  # Redirect to login page if not logged in

            # Fetch the subAdmin details
            subAdmin = SignUP.objects.get(subAdminID=subAdminID)

            # Check for an existing active subscription
            active_subscription = SubAdminSubscription.objects.filter(subAdminID=subAdmin, isActive=True).first()

            # If the selected plan is the free plan
            if selected_plan.planName.lower() == 'free trial':
                if subAdmin.hasUsedFreePlan:
                    messages.error(request, "You have already used the free trial. Please select a paid plan.")
                    return render(request, 'payment/selectPlan.html', {'subscriptionPlan': subscriptionPlan})

                # Update subAdmin's free plan usage
                subAdmin.hasUsedFreePlan = True
                subAdmin.isFirstLogin = False
                subAdmin.hasChosenPlan = True
                subAdmin.save()

                # Update the active subscription if exists, otherwise create a new one
                if active_subscription:
                    # Update the existing subscription
                    active_subscription.planID = selected_plan
                    active_subscription.startDate = timezone.now()
                    active_subscription.endDate = timezone.now() + timezone.timedelta(days=selected_plan.planDuration)
                    active_subscription.razorpayOrderID = ''
                    active_subscription.razorpayPaymentID = ''
                    active_subscription.razorpaySignature = ''
                    active_subscription.paymentStatus = 'Completed'
                    active_subscription.save()
                else:
                    # Create a new subscription for the free plan
                    subscription = SubAdminSubscription(
                        subAdminID=subAdmin,
                        planID=selected_plan,
                        startDate=timezone.now(),
                        endDate=timezone.now() + timezone.timedelta(days=selected_plan.planDuration),
                        isActive=True,
                        razorpayOrderID='',
                        razorpayPaymentID='',
                        razorpaySignature='',
                        paymentStatus='Completed',
                    )
                    subscription.save()

                # Redirect to the dashboard after successful plan selection
                return redirect('listPendingWork')

            # If the selected plan is a paid plan
            else:
                # Calculate the amount for the paid plan (convert to paisa)
                amount = int(selected_plan.planAnnualPrice * 100)
                # Store the selected plan ID in the session for later use in payment success callback
                request.session['planID'] = selected_plan_id

                # Create a Razorpay order for paid plans
                order = razorpay_client.order.create({
                    'amount': amount,
                    'currency': 'INR',
                    'payment_capture': '1'
                })
                
                # Prepare payment details to send to the frontend
                payment = {
                    'key': settings.RAZORPAY_KEY_ID,
                    'amount': amount,
                    'subAdminEmail': subAdmin.subAdminEmail,
                    'subAdminPhone': subAdmin.subAdminPhone,
                    'subAdminName': subAdmin.subAdminName,
                    'order_id': order['id'],
                    'plan': selected_plan,
                }
                # Render payment page
                return render(request, 'payment/paymentPage.html', {'payment': payment})

        except SubscriptionPlan.DoesNotExist:
            # Handle case where selected plan does not exist
            messages.error(request, "The selected subscription plan does not exist. Please choose a valid plan.")
            return render(request, 'payment/selectPlan.html', {'subscriptionPlan': subscriptionPlan})

        except SignUP.DoesNotExist:
            # Handle case where the subAdmin does not exist
            messages.error(request, "SubAdmin not found. Please log in again.")
            return redirect('subAdminLogin')

        except Exception as e:
            # General error handling with render
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return render(request, 'payment/selectPlan.html', {'subscriptionPlan': subscriptionPlan})

    # Render the select plan page (GET request)
    return render(request, 'payment/selectPlan.html', {'subscriptionPlan': subscriptionPlan})

@csrf_exempt
def paymentSuccess(request):
    if request.method == 'POST':
        # Extract payment details from the request
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Validate that all necessary fields are present
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            messages.error(request, "Missing payment details. Please try again.")
            return redirect('selectPlan')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            # Verify payment signature using Razorpay utility
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Fetch subAdmin and plan details from the session
            subAdmin_id = request.session.get('subAdminID')
            plan_id = request.session.get('planID')

            # Validate that both subAdmin and plan IDs exist in the session
            if not subAdmin_id or not plan_id:
                messages.error(request, "Invalid session data. Please try again.")
                return redirect('selectPlan')

            # Ensure subAdmin and plan are valid in the database
            try:
                subAdmin = SignUP.objects.get(subAdminID=subAdmin_id)
                plan = SubscriptionPlan.objects.get(planID=plan_id)
            except SignUP.DoesNotExist:
                messages.error(request, "SubAdmin not found. Please log in again.")
                return redirect('subAdminLogin')
            except SubscriptionPlan.DoesNotExist:
                messages.error(request, "Selected subscription plan not found.")
                return redirect('selectPlan')

            # Check if the user already has a subscription (active or inactive)
            subscription = SubAdminSubscription.objects.filter(subAdminID=subAdmin).first()

            if subscription:
                # Extend or update the existing subscription
                if subscription.endDate > timezone.now():
                    # Extend from the current end date
                    new_end_date = subscription.endDate + timezone.timedelta(days=plan.planDuration)
                else:
                    # If the subscription is expired, start from today
                    new_end_date = timezone.now() + timezone.timedelta(days=plan.planDuration)

                # Update the existing subscription
                subscription.planID = plan
                subscription.endDate = new_end_date
                subscription.isActive = True  # Reactivate the subscription
                subscription.razorpayOrderID = razorpay_order_id
                subscription.razorpayPaymentID = razorpay_payment_id
                subscription.razorpaySignature = razorpay_signature
                subscription.paymentStatus = 'Completed'
                subscription.save()
            else:
                # Create a new subscription if no previous one exists
                subscription = SubAdminSubscription(
                    subAdminID=subAdmin,
                    planID=plan,
                    startDate=timezone.now(),
                    endDate=timezone.now() + timezone.timedelta(days=plan.planDuration),
                    isActive=True,
                    razorpayOrderID=razorpay_order_id,
                    razorpayPaymentID=razorpay_payment_id,
                    razorpaySignature=razorpay_signature,
                    paymentStatus='Completed',
                )
                subscription.save()

            # Log the payment details for future reference
            payment_log = RazorpayPaymentLog(
                subAdminID=subAdmin,
                planID=plan,
                orderID=razorpay_order_id,
                paymentID=razorpay_payment_id,
                signature=razorpay_signature,
                amountPaid=plan.planAnnualPrice,
                status='Paid',
            )
            payment_log.save()

            # Update subAdmin's status
            subAdmin.hasChosenPlan = True
            subAdmin.isFirstLogin = False
            subAdmin.save()

            # Clear session data (optional, to avoid issues with future requests)
            request.session.pop('planID', None)

            # Redirect to dashboard after successful payment
            messages.success(request, "Your payment was successful! Subscription updated.")
            return redirect('listPendingWork')

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment signature verification failed. Please contact support.")
            return redirect('selectPlan')

        except Exception as e:
            # General error handling for other exceptions
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('selectPlan')

    # If the request method is not POST, redirect to the failure page
    messages.error(request, "Invalid request. Please try again.")
    return redirect('selectPlan')

def termsCondition(request):
    return render(request, 'policies/termsCondition.html')


