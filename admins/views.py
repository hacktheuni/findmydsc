from django.shortcuts import render, redirect
from user.models import *
from django.contrib import messages
import os, re
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from datetime import timedelta
import csv

# User All Function are here for SubAdmin
def listUser(request):
    subAdminID = request.session.get('subAdminID')
    if subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone)
        users = UpdatedUser.objects.filter(subAdminID=subAdmin.subAdminID, isActive="True").all().order_by('-userModifiedDate')
        context = {
            'base': 'base/subAdminBase.html',
            'users': users,
            'user': user,
            'subAdmin': subAdmin
        }
        return render(request, 'user/listUser.html', context)
    else:
        return redirect('adminSignIn')

def addUser(request):
    subAdminID = request.session.get('subAdminID')
    if subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone)
        context = {
            'base': 'base/subAdminBase.html',
            'user': user,
            'subAdmin': subAdmin
        }

        if request.method == 'POST':
            userName = request.POST.get('userName')
            userPhone = request.POST.get('userPhone')
            userUsername = request.POST.get('userUsername')
            userPassword = request.POST.get('userPassword')

            # Prepare form data to retain entered values in case of error
            form_data = {
                'userName': userName,
                'userPhone': userPhone,
                'userUsername': userUsername
            }

            # 1. Name validation: only letters and spaces
            if not re.match(r'^[A-Za-z\s]+$', userName):
                messages.error(request, "Name can only contain letters and spaces.")
                context['form_data'] = form_data
                return render(request, 'user/addUser.html', context)

            # 2. Phone number validation: exactly 10 digits
            if not re.match(r'^\d{10}$', userPhone):
                messages.error(request, "Phone number must be exactly 10 digits.")
                context['form_data'] = form_data
                return render(request, 'user/addUser.html', context)

            # 4. Password validation: minimum 8 characters, letters, numbers, and special characters
            if len(userPassword) < 8 or not re.search(r'[A-Za-z]', userPassword) or not re.search(r'\d', userPassword) or not re.search(r'[@$!%*?&#]', userPassword):
                messages.error(request, "Password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                context['form_data'] = form_data
                return render(request, 'user/addUser.html', context)

            # Check for existing phone number and username
            if UpdatedUser.objects.filter(subAdminID=user.subAdminID, userPhone=userPhone).exists():
                messages.error(request, "Phone number already exists.")
                context['form_data'] = form_data
                return render(request, 'user/addUser.html', context)

            if UpdatedUser.objects.filter(subAdminID=user.subAdminID, userUsername=userUsername).exists():
                messages.error(request, "Username already exists.")
                context['form_data'] = form_data
                return render(request, 'user/addUser.html', context)

            # Save the user
            user = UpdatedUser(
                subAdminID=user.subAdminID,
                userName=userName,
                userPhone=userPhone,
                userUsername=userUsername,
                userPassword=make_password(userPassword)
            )
            user.save()

            # Save user history
            userHistory = HistoryUser(
                subAdminID=user.subAdminID,
                userID=user,
                userName=userName,
                userPhone=userPhone,
                userUsername=userUsername,
                userPassword=make_password(userPassword),
                userModifiedDate=user.userModifiedDate
            )
            userHistory.save()

            messages.success(request, "User added successfully.")
            return HttpResponseRedirect(reverse('listUser'))

        return render(request, 'user/addUser.html', context)
    else:
        return redirect('adminSignIn')

def updateUser(request, userID):
    subAdminID = request.session.get('subAdminID')
    if subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.filter(subAdminID=subAdmin.subAdminID, userID=userID).first()
        userHistory = HistoryUser.objects.filter(subAdminID=subAdmin.subAdminID, userID=userID).all().order_by('-userModifiedDate')
        
        context = {
            'base': 'base/subAdminBase.html',
            'user': user,
            'userHistory': userHistory,
            'subAdmin': subAdmin
        }

        if request.method == 'POST':
            userName = request.POST.get('userName')
            userPhone = request.POST.get('userPhone')
            userUsername = request.POST.get('userUsername')
            userPassword = request.POST.get('userPassword')

            # Check if all fields are filled
            if not userName or not userPhone or not userUsername or not userPassword:
                messages.error(request, "All fields are required.")
                return redirect(request.path)

            # 1. Name validation: only letters and spaces
            if not re.match(r'^[A-Za-z\s]+$', userName):
                messages.error(request, "Name can only contain letters and spaces.")
                return redirect(request.path)

            # 2. Phone number validation: exactly 10 digits
            if not re.match(r'^\d{10}$', userPhone):
                messages.error(request, "Phone number must be exactly 10 digits.")
                return redirect(request.path)

            # 4. Password validation: minimum 8 characters, letters and numbers
            if len(userPassword) < 8 or not re.search(r'[A-Za-z]', userPassword) or not re.search(r'\d', userPassword):
                messages.error(request, "Password must be at least 8 characters long and contain both letters and numbers.")
                return redirect(request.path)

            # Check if phone number already exists for another user
            if UpdatedUser.objects.filter(userPhone=userPhone).exists() and UpdatedUser.objects.filter(userUsername=userUsername, userPassword=userPassword).exists():
                messages.error(request, "Phone number and Username already exists.")
                return redirect(request.path)

            # Update the user
            user.userName = userName
            user.userPhone = userPhone
            user.userUsername = userUsername
            user.userPassword = make_password(userPassword)
            user.save()

            # Create/update user history
            userHistory = HistoryUser(
                subAdminID=user.subAdminID, 
                userID=user, 
                userName=userName, 
                userPhone=userPhone, 
                userUsername=userUsername, 
                userPassword=make_password(userPassword), 
                userModifiedDate=user.userModifiedDate
            )
            userHistory.save()

            messages.success(request, "User updated successfully.")
            return redirect(request.path)
        
        return render(request, 'user/updateUser.html', context)   
    else:
        return redirect('adminSignIn')

def deleteUser(request):
    if request.method == 'POST':
        userIDs = request.POST.getlist('userIDs')
        confirmation = request.POST.get('deleteUser')
        if confirmation:
            if userIDs:
                # Retrieve users to deactivate that are still active
                users_to_deactivate = UpdatedUser.objects.filter(userID__in=userIDs, isActive=True)
                
                if users_to_deactivate.exists():
                    # Deactivating users and setting the deactivatedBy field to 'subAdmin'
                    users_to_deactivate.update(isActive=False, deactivatedBy='subAdmin')
                    messages.success(request, "Selected users have been deactivated successfully.")
                else:
                    messages.error(request, "No active users were found to deactivate.")
            else:
                messages.error(request, "No users selected for deactivation.")
        else:
            messages.error(request, "Deletion not confirmed.")

    return redirect('subAdminListUser')


# All profile related Function are here for subAdmin 
def updateProfile(request):
    subAdminID = request.session.get('subAdminID')
    if subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone)
        
        context = {
            'base': 'base/subAdminBase.html',
            'subAdmin': subAdmin,
            'user': user,
            'options': ["Company/ LLP", "Chartered Accountant", "Company Secretary", "Cost Accountant", "Others"]
        }

        if request.method == 'POST':
            # Retrieve form data
            subAdminName = request.POST.get('subAdminName')
            subAdminType = request.POST.get('subAdminType')
            subAdminEmail = request.POST.get('subAdminEmail')
            subAdminPhone = request.POST.get('subAdminPhone')
            subAdminCity = request.POST.get('subAdminCity')
            subAdminState = request.POST.get('subAdminState')
            subAdminPinCode = request.POST.get('subAdminPinCode')

            # Handle file upload if a new logo is provided
            if 'subAdminLogo' in request.FILES:
                logo = request.FILES['subAdminLogo']

                # Validate file size (max 500KB)
                if logo.size > 500 * 1024:  # 500KB
                    messages.error(request, "The logo file is too large. Maximum size allowed is 500KB.")
                    return render(request, 'adminDetails/updateProfile.html', context)

                # Validate file type (only PNG and JPEG)
                file_ext = os.path.splitext(logo.name)[1].lower()
                if file_ext not in ['.png', '.jpg', '.jpeg']:
                    messages.error(request, "Invalid file format. Only PNG and JPEG files are allowed.")
                    return render(request, 'adminDetails/updateProfile.html', context)

                # Check if an old logo exists and delete it
                if subAdmin.subAdminLogo:
                    old_logo_path = os.path.join(settings.MEDIA_ROOT, subAdmin.subAdminLogo.name)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)

                # Save the new logo
                subAdmin.subAdminLogo = logo

            # Update the rest of the subAdmin fields
            subAdmin.subAdminName = subAdminName
            subAdmin.subAdminType = subAdminType
            subAdmin.subAdminEmail = subAdminEmail
            subAdmin.subAdminPhone = subAdminPhone
            subAdmin.subAdminCity = subAdminCity
            subAdmin.subAdminState = subAdminState
            subAdmin.subAdminPinCode = subAdminPinCode
            subAdmin.save()

            return redirect('updateProfile')  # Redirect after successful update

        return render(request, 'adminDetails/updateProfile.html', context)
    else:
        return redirect('adminSignIn')

def deleteProfile(request):
    if request.method == 'POST':
        deleteProfile = request.POST.get('deleteProfile')
        subAdminPassword = request.POST.get('subAdminPassword')
        subAdminID = request.session.get('subAdminID')

        if deleteProfile:
            try:
                # Retrieve the subAdmin profile
                profile = SignUP.objects.get(subAdminID=subAdminID)

                # Check if the provided password matches the hashed password
                if check_password(subAdminPassword, profile.subAdminPassword):
                    profile.delete()  # Delete the profile if the password matches
                    # Clear all session data
                    request.session.flush()
                    messages.success(request, "Your Account is Deleted")
                    return redirect('adminSignIn')
                else:
                    messages.error(request, "Password does not match.")
                    return redirect('updateProfile')

            except SignUP.DoesNotExist:
                messages.error(request, "Account not found.")
                return redirect('updateProfile')
        else:
            messages.error(request, "Deletion not confirmed.")
            return redirect('updateProfile')

    return redirect('updateProfile')

def subscriptionDetails(request):
    subAdminID = request.session.get('subAdminID')
    context = {
        'base': 'base/subAdminBase.html',
        'subAdmin': None,
        'user': None,
        'subscriptionPlan': None,
        'activePlan': None,
        'start_date': None,
        'end_date': None,
        'time_remaining': None,
        'formatted_time_remaining': None,  # For formatted output
    }

    if subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone)
        subscriptionPlan = SubscriptionPlan.objects.all()
        activePlan = SubAdminSubscription.objects.filter(subAdminID=subAdmin, isActive=True).first()

        if subAdmin.hasUsedFreePlan:
            subscriptionPlan = list(SubscriptionPlan.objects.all())
            subscriptionPlan.pop(0)

        # Add logic to get subscription details if an active plan exists
        if activePlan:
            context['activePlan'] = activePlan
            context['start_date'] = activePlan.startDate
            context['end_date'] = activePlan.endDate

            # Calculate time remaining
            time_remaining = activePlan.endDate - timezone.now()
            if time_remaining > timedelta(0):
                context['time_remaining'] = time_remaining
                # Format time remaining for display
                days, seconds = time_remaining.days, time_remaining.seconds
                hours, remainder = divmod(seconds, 3600)
                context['formatted_time_remaining'] = f"{days} days, {hours} hours"
            else:
                context['time_remaining'] = timedelta(0)  # Plan has expired
                context['formatted_time_remaining'] = "Subscription has expired"

        context['subAdmin'] = subAdmin
        context['user'] = user
        context['subscriptionPlan'] = subscriptionPlan

    return render(request, 'adminDetails/subscriptionDetails.html', context)

def exportToCSV(request):
    sub_admin_id = request.session.get('subAdminID')
    
    if not sub_admin_id:
        messages.error(request, "No subAdminID found in session.")
        return redirect('adminSignIn')

    subAdmin = SignUP.objects.get(subAdminID=sub_admin_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{subAdmin.subAdminName}db.csv"'
    writer = csv.writer(response)

    # Write the header row for the CSV file in the specified order
    writer.writerow([
        'Group Name', 'Company Name', 'Client Name', 'Status', 'Location', 
        'Renewal Date', 'Contact Person', 'Phone Number', 'Last Modified Date', 
        'Last Received By', 'Last Received From', 'Last Delivered By', 'Last Delivery To'
    ])

    try:
        dsc_data = UpdatedDSC.objects.filter(subAdminID=sub_admin_id).select_related('companyID__groupID', 'userID')

        if not dsc_data.exists():
            messages.warning(request, "No data available for export.")
            return redirect('exportData')

        for dsc in dsc_data:
            company = dsc.companyID
            group = company.groupID if company else None
            user = dsc.userID

            # Fetch related client information
            client = UpdatedClient.objects.filter(companyID=company).first() if company else None

            # Write each row to the CSV file in the specified order
            writer.writerow([
                group.groupName if group else '',                    
                company.companyName if company else '',               
                dsc.clientName,                                       
                dsc.status,                                         
                dsc.location,                                         
                dsc.renewalDate.strftime('%d-%m-%Y') if dsc.renewalDate else '', 
                client.clientName if client else '',                
                client.clientPhone if client else '',                 
                dsc.modifiedDate.strftime('%d-%m-%Y %H:%M:%S'),      
                dsc.receivedBy,                                       
                dsc.receivedFrom,                                     
                dsc.deliveredBy,                                     
                dsc.deliveredTo                                      
            ])

        request.session['export_message'] = "Data exported successfully."
        request.session['export_message_level'] = messages.SUCCESS
        return response

    except Exception as e:
        request.session['export_message'] = "Failed to export data. Please try again."
        request.session['export_message_level'] = messages.ERROR
        return redirect('exportData')
        
def exportData(request):
    # Display any success or error messages set in the session
    message = request.session.pop('export_message', None)
    message_level = request.session.pop('export_message_level', None)

    if message:
        messages.add_message(request, message_level, message)
    
    context = {
        'base': 'base/subAdminBase.html'
    }
    return render(request, 'adminDetails/exportData.html', context)


# All Function are here for the superAdmin
def listSubAdmin(request):
    if request.session.get('superAdminID'):
        subAdmins = SignUP.objects.annotate(
            active_user_count=Count('updateduser', filter=Q(updateduser__isActive=True), distinct=True),
            dsc_count=Count('updateddsc', distinct=True)  # Ensure distinct DSC entries are counted
        ).order_by('-subAdminRegisterDate')
        context = {
            'subAdmins': subAdmins
        }
        return render(request, 'subAdmin/listSubAdmin.html', context)
    else:
        return redirect('adminSignIn')

def listFeedback(request):
    if request.session.get('superAdminID'):
        feedbacks = Feedback.objects.all().order_by('-feedbackDate')
        context = {
            'feedbacks': feedbacks
        }
        return render(request, 'contactUs/listFeedback.html', context)
    else:
        return redirect('adminSignIn')

def action(request):
    if request.method == 'POST':
        subAdminIDs = request.POST.getlist('subAdminIDs')
        action_type = request.POST.get('action_type')  

        if subAdminIDs:
            if action_type == 'deactivate':
                # Deactivate subAdmins and their users
                subAdmins_to_deactivate = SignUP.objects.filter(subAdminID__in=subAdminIDs, isActive=True)
                if subAdmins_to_deactivate.exists():
                    subAdmins_to_deactivate.update(isActive=False)  # Deactivating subAdmins
                    
                    # Deactivate users of the subAdmins
                    users_to_deactivate = UpdatedUser.objects.filter(subAdminID__in=subAdminIDs, isActive=True)
                    users_to_deactivate.update(isActive=False, deactivatedBy='superAdmin')  # Deactivating users and marking who deactivated them

                    messages.success(request, "Selected subAdmins and their users have been deactivated successfully.")
                else:
                    messages.error(request, "Some subAdmins are already deactivated or do not exist.")

            elif action_type == 'activate':
                # Activate subAdmins
                subAdmins_to_activate = SignUP.objects.filter(subAdminID__in=subAdminIDs, isActive=False)
                if subAdmins_to_activate.exists():
                    subAdmins_to_activate.update(isActive=True)  # Activating subAdmins

                    # Activate users of the subAdmins, excluding those deactivated by subAdmin
                    users_to_activate = UpdatedUser.objects.filter(subAdminID__in=subAdminIDs, isActive=False, deactivatedBy='superAdmin')
                    users_to_activate.update(isActive=True, deactivatedBy=None)  # Activating users and clearing the deactivation marker

                    messages.success(request, "Selected subAdmins and their eligible users have been activated successfully.")
                else:
                    messages.error(request, "Some subAdmins are already active or do not exist.")
        else:
            messages.error(request, "No subAdmins selected for activation or deactivation.")
        
        return redirect('listSubAdmin')

    return redirect('listSubAdmin')


