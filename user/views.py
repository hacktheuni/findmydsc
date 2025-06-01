from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import re
from django.contrib.auth.hashers import check_password, make_password
from datetime import date, datetime, timedelta
from django.db.models import Max
from django.utils.timezone import localtime
from urllib.parse import urlparse

def getUser(request):
    userID = request.session.get('userID')
    subAdminID = request.session.get('subAdminID')
    superAdminID = request.session.get('superAdminID')

    user = None
    base = None
    subAdmin = None
    superAdmin = None

    # Check if it's a user or subAdmin session
    if userID:
        try: 
            user = UpdatedUser.objects.get(userID=userID)
            base = 'base/userBase.html'
            if user.isClientUser:
                base = 'base/clientBase.html'
        except UpdatedUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('userSignIn')
    elif subAdminID:
        try:
            subAdmin = SignUP.objects.get(subAdminID=subAdminID)
            user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone, isActive=False)
            base = 'base/subAdminBase.html'
            if subAdmin.freeUser:
                base = 'base/freeUserBase.html'
        except SignUP.DoesNotExist or UpdatedUser.DoesNotExist:
            messages.error(request, "SubAdmin not found.")
            return redirect('adminSignIn')
    elif superAdminID:
        try:
            superAdmin = SuperAdmin.objects.get(superAdminID=superAdminID)
            base = 'base/superAdminBase.html'
        except SuperAdmin.DoesNotExist:
            messages.error(request, "SuperAdmin not found.")
            return redirect('adminSignIn')
    else:
        return redirect('adminSignIn')

    return {'user': user, 'base': base, 'subAdmin': subAdmin, 'superAdmin': superAdmin}

def query(user, model):
    qs = model.objects.filter(subAdminID=user.subAdminID)

    if model == UpdatedCompany or model == HistoryCompany or model == UpdatedUser or model == Trademark:
        # If the user has a group assigned, filter by that group
        if user.groupID:
            qs = qs.filter(groupID=user.groupID)

    elif model == UpdatedDSC or model == UpdatedClient or model == HistoryDSC or model == HistoryClient or model == AnnualFiling or model == PendingWork:
        # If the user has a group assigned, filter by that group
        if user.groupID:
            qs = qs.filter(companyID__groupID=user.groupID)

    elif model == UpdatedGroup:
        if user.groupID:
            qs = qs.filter(groupID=user.groupID.groupID)

    return qs

def allow_only_client_users(view_func):
    def wrapper(request, *args, **kwargs):
        userID = request.session.get('userID')
        subAdminID = request.session.get('subAdminID')
        if userID:
            try:
                user = UpdatedUser.objects.get(userID=userID)
                # If user is not a client user → allow full access
                if not user.isClientUser:
                    return view_func(request, *args, **kwargs)

                allowed_views = [
                         'updatePassword'  # Add more allowed view names here
                    ]
                if user.canReadOnly:
                    if user.accessToPendingWork:
                        allowed_views.append('listPendingWork')
                    if user.accessToAnnual:
                        allowed_views.append('listAnnual')
                    if user.accessToTrademark:
                        allowed_views.append('listTrademark')
                
                elif user.canReadWrite:
                    # If user is a client user with read/write access → allow access to all views
                    if user.accessToPendingWork:
                        add_views = [
                            'listPendingWork', 'addPendingWork', 'updatePendingWork', 'deletePendingWork'
                        ]
                        allowed_views.extend(add_views)
                    if user.accessToAnnual:
                        add_views = [
                            'listAnnual', 'addAnnual', 'updateAnnual', 'deleteAnnual'
                        ]
                        allowed_views.extend(add_views)
                    if user.accessToTrademark:
                        add_views = [
                            'listTrademark', 'addTrademark', 'updateTrademark', 'deleteTrademark'
                        ]
                        allowed_views.extend(add_views)
                else:
                    # If user has no specific permissions, redirect to a default page
                    messages.error(request, "Access denied: You are not allowed to view this page.")
                    return redirect('userSignIn')  # Or any default allowed view
                
                # Check if current view function is allowed
                if view_func.__name__ in allowed_views:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "Access denied: You are not allowed to view this page.")
                    return redirect(request.META.get('HTTP_REFERER'))  # Or any default allowed view
            except UpdatedUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('userSignIn')
            
        elif subAdminID:
            try:
                subAdmin = SignUP.objects.get(subAdminID=subAdminID)
                # If user is not a client user → allow full access
                if not subAdmin.freeUser:
                    return view_func(request, *args, **kwargs)

                allowed_views_subAdmin = [
                    'listDSC', 'addDSC', 'updateDSC', 'deleteDSC', 'listGroup', 'addGroup', 'updateGroup', 'deleteGroup', 'listCompany', 'addCompany', 'updateCompany', 'deleteCompany', 'feedBack', 'updatePassword', 'updateProfile', 'deleteProfile'
                ]

                # Check if current view function is allowed
                if view_func.__name__ in allowed_views_subAdmin:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "Access denied: You are not allowed to view this page.")
                    return redirect(request.META.get('HTTP_REFERER'))  # Or any default allowed view
            except SignUP.DoesNotExist:
                messages.error(request, "SubAdmin not found.")
                return redirect('adminSignIn')
        else:
            return redirect('adminSignIn')
        
    return wrapper

def parse_date(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def parse_amount(amt_str):
    try:
        return float(amt_str) if amt_str else 0.0 
    except ValueError:
        return 0.0
    


# All List Function are here
@allow_only_client_users
def listDSC(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    whatsapp_url = request.session.pop('whatsapp_url', None)

    updatedDSCs = query(user, UpdatedDSC).order_by('-modifiedDate')

    today = date.today()
    for dsc in updatedDSCs:
        if dsc.renewalDate:
            dsc.is_expired = dsc.renewalDate.date() < today
        else:
            dsc.is_expired = False  

    context = {
        'base': base,
        'updatedDSCs': updatedDSCs,
        'user': user,
        'whatsurl': whatsapp_url,
    }
    return render(request, 'dsc/listDSC.html', context)

@allow_only_client_users
def listCompany(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    companies = query(user, UpdatedCompany).order_by('-companyModifiedDate')
    context = {
        'base': base,
        'companies': companies,
        'user': user,
    }
    return render(request, 'company/listCompany.html', context)

@allow_only_client_users
def listGroup(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
            
    groups = UpdatedGroup.objects.filter(subAdminID=user.subAdminID).all().order_by('-groupModifiedDate')
    context = {
        'base': base,
        'groups':groups,
        'user': user
    }
    return render(request, 'group/listGroup.html', context)

@allow_only_client_users
def listClient(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    clients = query(user, UpdatedClient).order_by('-clientModifiedDate')
    context = {
        'base': base,
        'clients': clients,
        'user': user,
    }
    return render(request, 'client/listClient.html', context)

@allow_only_client_users
def listWork(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    work = Work.objects.filter(subAdminID=user.subAdminID).order_by('-modifiedDate')
    context = {
        'base': base,
        'user': user,
        'work': work
    }
    return render(request, 'work/listWork.html', context)

@allow_only_client_users
def listPendingWork(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    show_archived = request.GET.get('archived', 'false').lower() == 'true'

    # Base queryset: all pending work for this sub-admin and archive flag
    qs = PendingWork.objects.filter(
        subAdminID=user.subAdminID,
        isArchived=show_archived
    )

    # If the user has a group, narrow to work for companies in that group
    if user.groupID:
        qs = qs.filter(companyID__groupID=user.groupID)

    # Order and annotate
    pendingWork = qs.order_by('-isPinned', '-modifiedDate')
    today = localtime().date()

    for work in pendingWork:
        if work.internalDueDate:
            work.is_internal_expired = work.internalDueDate < today
            work.is_internal_due_soon = today <= work.internalDueDate < (today + timedelta(days=4))
        if work.actualDueDate:
            work.is_actual_expired = work.actualDueDate < today
            work.is_actual_due_soon = today <= work.actualDueDate < (today + timedelta(days=4))
        work.is_approved              = (work.status == "Approved")
        work.is_marked_for_resubmission = (work.status == "Sent For Resubmission")
        work.is_pending_for_approval  = (work.status == "Pending For Approval")
        work.is_rejected              = (work.status == "Rejected")

    return render(request, 'pendingWork/listPendingWork.html', {
        'base': base,
        'user': user,
        'pendingWork': pendingWork,
        'show_archived': show_archived,
    })

@allow_only_client_users
def listAnnual(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    show_archived = request.GET.get('archived', 'false').lower() == 'true'

    # Base queryset: all annual filings for this sub-admin and archive flag
    qs = AnnualFiling.objects.filter(
        subAdminID=user.subAdminID,
        isArchived=show_archived
    )

    # If the user has a group, narrow to filings for companies in that group
    if user.groupID:
        qs = qs.filter(companyID__groupID=user.groupID)

    annualFilies = qs.order_by('-isPinned', '-modifiedDate')

    for af in annualFilies:
        af.is_approved_DPT3 = (af.statusDPT3 == 'Approved')
        af.is_approved_MGT14 = (af.statusMGT14 == 'Approved')
        af.is_approved_AOC4 = (af.statusAOC4 == 'Approved')
        af.is_approved_MGT7 = (af.statusMGT7 == 'Approved')
        af.is_approved_Form11 = (af.statusForm11 == 'Approved')
        af.is_approved_Form8 = (af.statusForm8 == 'Approved')

        af.is_pending_DPT3 = (af.statusDPT3 == 'Pending')
        af.is_pending_MGT14 = (af.statusMGT14 == 'Pending')
        af.is_pending_AOC4 = (af.statusAOC4 == 'Pending')
        af.is_pending_MGT7 = (af.statusMGT7 == 'Pending')
        af.is_pending_Form11 = (af.statusForm11 == 'Pending')
        af.is_pending_Form8 = (af.statusForm8 == 'Pending')
    return render(request, 'annualFiling/listAnnual.html', {
        'base': base,
        'user': user,
        'annualFilies': annualFilies,
        'show_archived': show_archived,
    })

@allow_only_client_users
def listTrademark(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    show_archived = request.GET.get('archived', 'false').lower() == 'true'

    # Base queryset: all annual filings for this sub-admin and archive flag
    qs = Trademark.objects.filter(
        subAdminID=user.subAdminID,
        isArchived=show_archived
    )

    # If the user has a group, narrow to filings for companies in that group
    if user.groupID:
        qs = qs.filter(groupID=user.groupID)

    trademark = qs.order_by('-modifiedDate') 

    for tm in trademark:
        tm.is_objected = (tm.status1 == "Objected")
        tm.is_accepted = (tm.status1 == "Accepted")  
        tm.is_registered = (tm.status1 == "Registered")
        tm.is_abandoned = (tm.status1 == "Abandoned")
        tm.is_opposed = (tm.status1 == "Opposed")

    return render(request, 'trademark/listTrademark.html', {
        'base': base,
        'user': user,
        'trademark': trademark,
        'show_archived': show_archived,
    })

@allow_only_client_users
def listPendingWorkReport(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    # Base queryset
    qs = PendingWork.objects.filter(subAdminID=user.subAdminID)

    # Group‑gate: if user has a group, limit to that group’s companies
    if user.groupID:
        qs = qs.filter(companyID__groupID=user.groupID)

    pendingWork = qs.all()

    return render(request, 'report/listPendingWorkReport.html', {
        'base': base,
        'user': user,
        'pendingWork': pendingWork,
    })

@allow_only_client_users
def listAnnualReport(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    # Base queryset
    qs = AnnualFiling.objects.filter(subAdminID=user.subAdminID)

    # Group‑gate: if user has a group, limit to that group’s companies
    if user.groupID:
        qs = qs.filter(companyID__groupID=user.groupID)

    annualFilies = qs.all()

    return render(request, 'report/listAnnualReport.html', {
        'base': base,
        'user': user,
        'annualFilies': annualFilies,
    })


# All Add Function are here
@allow_only_client_users
def addDSC(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    try:
        subAdmin = SignUP.objects.get(subAdminID=user.subAdminID.subAdminID)
    except SignUP.DoesNotExist:
        messages.error(request, "SubAdmin not found.")
        return redirect('listDSC')
    if not subAdmin.freeUser:
        try:
            # Fetch the user's subscription plan
            subscription_plan = SubAdminSubscription.objects.get(subAdminID=user.subAdminID, isActive='True')
            subscription_plan_name = subscription_plan.planID.planName.lower()
            if subscription_plan_name == 'free trial':
                max_dsc_allowed = 100
            elif subscription_plan_name == 'basic':
                max_dsc_allowed = 350
            elif subscription_plan_name == 'standard':
                max_dsc_allowed = 700
            elif subscription_plan_name == 'premimum':
                max_dsc_allowed = 1500
            elif subscription_plan_name == 'premimum plus':
                max_dsc_allowed = float('inf')
            else:
                max_dsc_allowed = 0  # fallback if plan is somehow invalid
        except SubAdminSubscription.DoesNotExist:
            messages.error(request, "Subscription plan not found.")
            return redirect('listDSC')
    else:
        max_dsc_allowed = float('inf')  # Free users can add unlimited DSCs

    existing_dsc_count = UpdatedDSC.objects.filter(subAdminID=user.subAdminID).count()
    companies = query(user, UpdatedCompany).all()

    context = {
        'base': base,
        'companies': companies,
        'user': user
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        status = request.POST.get('status')
        location = request.POST.get('location')
        renewalDate = request.POST.get('renewalDate') or None
        receivedBy = request.POST.get('receivedBy') or ''
        receivedFrom = request.POST.get('receivedFrom') or ''
        clientPhone = request.POST.get('clientPhone')
        deliveredTo = request.POST.get('deliveredTo') or ''
        deliveredBy = request.POST.get('deliveredBy') or ''

        form_data = request.POST.copy()
        if renewalDate:
            renewalDate = parse_date(renewalDate)
        form_data['renewalDate'] = renewalDate

        if status == 'IN':
            required_fields = ['clientName', 'companyName', 'status', 'location', 'receivedBy', 'receivedFrom', 'clientPhone']
        elif status == 'OUT':
            required_fields = ['clientName', 'companyName', 'status', 'location', 'deliveredTo', 'deliveredBy', 'clientPhone']

        if not all(required_fields):
            messages.error(request, "Please fill all required fields.")
        elif existing_dsc_count >= max_dsc_allowed:
            messages.error(request, f"You can only add up to {max_dsc_allowed} DSCs based on your subscription plan.")
        else:
            subAdminID = user.subAdminID
            company = query(user, UpdatedCompany).filter(companyName=companyName).first()

            if not company:
                messages.error(request, "Company not found.")
                form_data['companyName'] = ''
                form_data['receivedFrom'] = ''
                form_data['deliveredTo'] = ''
                
            else:
                dsc = UpdatedDSC(
                    clientName=clientName,
                    companyID=company,
                    status=status,
                    receivedBy=receivedBy,
                    receivedFrom=receivedFrom,
                    deliveredTo=deliveredTo,
                    deliveredBy=deliveredBy,
                    location=location,
                    renewalDate=renewalDate,
                    clientPhone=clientPhone,
                    userID=user,
                    subAdminID=subAdminID
                )
                dsc.save()

                dscHistory = HistoryDSC(
                    dscID=dsc,
                    clientName=clientName,
                    companyID=company,
                    status=status,
                    receivedBy=receivedBy,
                    receivedFrom=receivedFrom,
                    deliveredTo=deliveredTo,
                    deliveredBy=deliveredBy,
                    location=location,
                    renewalDate=renewalDate,
                    clientPhone=clientPhone,
                    userID=user,
                    subAdminID=subAdminID,
                    modifiedDate=dsc.modifiedDate
                )
                dscHistory.save()

                # Send WhatsApp message based on status
                if status == 'IN':
                    whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=receivedFrom)
                elif status == 'OUT':
                    whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=deliveredTo)
                else:
                    whatsapp_url = ''

                request.session['whatsapp_url'] = whatsapp_url
                messages.success(request, "DSC added successfully.")
                return redirect('listDSC')

        context['form_data'] = form_data
        return render(request, 'dsc/addDSC.html', context)

    return render(request, 'dsc/addDSC.html', context)

@allow_only_client_users
def addCompany(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    groups = query(user, UpdatedGroup)
    context = {
        'base': base,
        'groups': groups,
        'user': user
    }

    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        companyName = request.POST.get('companyName')
        companyType = request.POST.get('companyType')

        # Prepare form data to retain values in case of error
        form_data = {
            'groupName': groupName,
            'companyName': companyName,
            'companyType': companyType
        }

        # Validation checks
        if not groupName or not companyName or not companyType:
            messages.error(request, "Please fill all required fields.")
        else:
            subAdminID = user.subAdminID
            group = query(user, UpdatedGroup).filter(groupName=groupName).first()

            if group:
                # Normalize the company name for case-insensitive comparison
                companyName_normalized = companyName.lower()

                if UpdatedCompany.objects.filter(companyName__iexact=companyName_normalized, subAdminID=subAdminID).exists():
                    messages.error(request, "Company already exists.")
                    form_data['companyName'] = ''  # Clear the company name in case of this error
                else:
                    company = UpdatedCompany(
                        companyName=companyName,companyType=companyType, groupID=group, userID=user, subAdminID=subAdminID
                    )
                    company.save()

                    companyHistory = HistoryCompany(
                        companyID=company, companyName=companyName,companyType=companyType, groupID=group,
                        userID=user, subAdminID=subAdminID, companyModifiedDate=company.companyModifiedDate
                    )
                    companyHistory.save()

                    messages.success(request, "Company added successfully.")
                    return HttpResponseRedirect(reverse('listCompany'))
            else:
                messages.error(request, "Group not found.")
                form_data['groupName'] = ''  # Clear the group name if the group is not found

        # If there's any error, re-render the form with previous data
        context['form_data'] = form_data
        return render(request, 'company/addCompany.html', context)

    return render(request, 'company/addCompany.html', context)

@allow_only_client_users
def addGroup(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
            
    context = {
        'base': base,
        'user': user
    }
    if request.method == 'POST':
        groupName = request.POST.get('groupName')

        if not groupName:
            messages.error(request, "Group name cannot be empty.")
            return redirect(request.path)
        else:
            if user:
                subAdminID = user.subAdminID
                # Normalize the group name to make it case-insensitive
                groupName_normalized = groupName.lower()
                if UpdatedGroup.objects.filter(groupName__iexact=groupName_normalized, subAdminID=subAdminID).exists():
                    messages.error(request, "Group already exists.")
                    return redirect(request.path)
                else:
                    group = UpdatedGroup(
                        groupName=groupName, userID=user, subAdminID=subAdminID
                    )
                    group.save()

                    groupHistory = HistoryGroup(
                        groupID=group, groupName=groupName, userID=user,
                        subAdminID=subAdminID, groupModifiedDate=group.groupModifiedDate
                    )
                    groupHistory.save()
                    messages.success(request, "Group added successfully.")
                    return HttpResponseRedirect(reverse('listGroup'))

    
    return render(request, 'group/addGroup.html', context)

@allow_only_client_users
def addClient(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    # Fetch companies that do not have a client associated with them
    companies_with_no_clients = query(user, UpdatedCompany).exclude(
        updatedclient__isnull=False
    )
    context = {
        'base': base,
        'companies': companies_with_no_clients
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        clientPhone = request.POST.get('clientPhone')

        # Prepare form data to retain values in case of error
        form_data = {
            'clientName': clientName,
            'companyName': companyName,
            'clientPhone': clientPhone
        }

        # Check if all fields are filled
        if not all([clientName, companyName, clientPhone]):
            messages.error(request, "Please fill all required fields.")
        elif not re.match(r'^[A-Za-z\s]+$', clientName):
            messages.error(request, "Client name can only contain letters and spaces.")
            form_data['clientName'] = ''  # Clear client name field in case of error
        elif not re.match(r'^\d{10}$', clientPhone):
            messages.error(request, "Phone number must be exactly 10 digits.")
            form_data['clientPhone'] = ''  # Clear phone number in case of error
        else:
            # Check if the phone number already exists
            subAdminID = user.subAdminID
            company = query(user, UpdatedCompany).filter(companyName=companyName).first()

            if company:
                if UpdatedClient.objects.filter(clientPhone=clientPhone).exists():
                    messages.error(request, "Phone number already exists.")
                    form_data['clientPhone'] = ''  # Clear phone field
                else:
                    # Create and save the new client
                    client = UpdatedClient(
                        clientName=clientName, companyID=company, userID=user,
                        clientPhone=clientPhone, subAdminID=subAdminID
                    )
                    client.save()

                    # Save the client to the history
                    clientHistory = HistoryClient(
                        clientID=client, clientName=clientName, companyID=company,
                        userID=user, clientPhone=clientPhone,
                        subAdminID=subAdminID, clientModifiedDate=client.clientModifiedDate
                    )
                    clientHistory.save()

                    messages.success(request, "Client added successfully.")
                    return HttpResponseRedirect(reverse('listClient'))
            else:
                messages.error(request, "Company not found.")
                form_data['companyName'] = ''  # Clear company name if not found

        # If there are any errors, re-render the form with previous data
        context['form_data'] = form_data
        return render(request, 'client/addClient.html', context)

    return render(request, 'client/addClient.html', context)

@allow_only_client_users
def addWork(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    context = {
        'base': base,
    }
    
    if request.method == 'POST':
        formNo = request.POST.get('formNo')
        matter = request.POST.get('matter')
        filingDays = request.POST.get('filingDays')
        
        # Prepare form data to retain values in case of errors
        form_data = {
            'formNo': formNo,
            'matter': matter,
            'filingDays': filingDays,
        }
        
        # Validate that all required fields are provided
        if not all([formNo, matter, filingDays]):
            messages.error(request, "Please fill all required fields.")
        # Check that filingDays is numeric
        elif not filingDays.isdigit():
            messages.error(request, "Filing days must be a number.")
            form_data['filingDays'] = ''
        # Check if formNo already exists for this sub-admin
        elif Work.objects.filter(formNo=formNo, subAdminID=user.subAdminID).exists():
            messages.error(request, "Form number already exists.")
        else:
            try:
                # Create and save a new Work record
                work = Work(
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                )
                work.save()
                historyWork = HistoryWork(
                    formID=work,
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                    modifiedDate=work.modifiedDate
                )
                historyWork.save()
                messages.success(request, "Work added successfully.")
                return HttpResponseRedirect(reverse('listWork'))
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        # If there are errors, pass the form data back to the template
        context['form_data'] = form_data
        return render(request, 'work/addWork.html', context)
    
    return render(request, 'work/addWork.html', context)

@allow_only_client_users
def addPendingWork(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    companies = query(user, UpdatedCompany)
    forms = Work.objects.filter(subAdminID=user.subAdminID).all()
    users = query(user, UpdatedUser).filter(isActive="True").all()
    context = {
        'base': base,
        'companies': companies,
        'forms': forms,
        'users': users,
        'user': user
    }

    if request.method == 'POST':
        # Get data from POST request
        form_no           = request.POST.get('formNo')            
        company_name      = request.POST.get('companyName')       
        event_date        = request.POST.get('eventDate')
        actual_due_date   = request.POST.get('actualDueDate')
        cutOffTime        = request.POST.get('cutOffTime')          
        srnNo             = request.POST.get('srnNo', '')
        internal_due_date = request.POST.get('internalDueDate')
        user_id_str       = request.POST.get('userID')
        status            = request.POST.get('status')
        srn_date_str      = request.POST.get('srnDate', '')
        amt_str           = request.POST.get('amt', '')
        remark            = request.POST.get('remark')
        billing           = request.POST.get('billing')
        fees              = request.POST.get('fees', '')
        isArchived = 'isArchived' in request.POST
        isPinned   = 'isPinned' in request.POST

        form_data = request.POST.copy()

        if company_name:
            try:
                company = query(user, UpdatedCompany).get(companyName=company_name)
                groupName = company.groupID.groupName
            except UpdatedCompany.DoesNotExist:
                messages.error(request, "Company not found.")
                form_data['companyName'] = ''
                context['form_data'] = form_data
                return render(request, 'pendingWork/addPendingWork.html', context)
        else:
            groupName = ''
        
        form_data['groupName'] = groupName
        
        # Check required fields (optional fields for srnNo, srnDate, and amt are not required)
        if not all([form_no, company_name, event_date, actual_due_date, 
                    cutOffTime, user_id_str, status, billing]):
            messages.error(request, "Please fill all required fields.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)

        srnDate = parse_date(srn_date_str)
        amt = parse_amount(amt_str)
        fees = parse_amount(fees)
        
        # Fetch foreign key objects:
        try:
            work_instance = Work.objects.get(formNo=form_no, subAdminID=user.subAdminID)
            updated_user_instance = UpdatedUser.objects.get(userName=user_id_str, subAdminID=user.subAdminID)
        except Work.DoesNotExist:
            messages.error(request, "Work record not found.")
            form_data['formNo'] = ''
            form_data['matter'] = ''
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        except UpdatedUser.DoesNotExist:
            messages.error(request, "User record not found.")
            form_data['userID'] = ''
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        
        # --- Auto-generate indexSRN for the current subAdminID ---
        max_index_dict = PendingWork.objects.filter(subAdminID=user.subAdminID).aggregate(max_index=Max('indexSRN'))
        max_index = max_index_dict.get('max_index')
        try:
            next_index = int(max_index) + 1 if max_index is not None else 1
        except Exception:
            next_index = 1
        # ----------------------------------------------------------
        
        # Create and save the PendingWork record (with indexSRN included)
        try:
            pending_work = PendingWork(
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo,      # remains as provided (or empty)
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                modifiedBy=user.userName,
                indexSRN=next_index,  # New auto-increment field for the subAdmin
            )
            pending_work.save()
            
            # Optionally, create a history record as well
            history_pending_work = HistoryPendingWork(
                pendingWorkID=pending_work,
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo,
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                indexSRN=next_index,
                modifiedBy=user.userName,
                modifiedDate=pending_work.modifiedDate  # assuming this field exists
            )
            history_pending_work.save()
            
            messages.success(request, "Pending work added successfully.")
            return HttpResponseRedirect(reverse('listPendingWork'))
        except Exception as e:
            messages.error(request, f"Error saving pending work")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
    
    return render(request, 'pendingWork/addPendingWork.html', context)

@allow_only_client_users
def addAnnual(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    companies = query(user, UpdatedCompany)
    context = {
        'base': base,
        'user': user,
        'companies': companies
    }

    if request.method == 'POST':
        # Retrieve data from POST request
        company_name       = request.POST.get('companyName')  # from the form
        financialYear      = request.POST.get('financialYear')
        
        statusDPT3         = request.POST.get('statusDPT3', 'N/A')
        srnNoDPT3          = request.POST.get('srnNoDPT3')
        srnDateDPT3_str    = request.POST.get('srnDateDPT3')
        amtDPT3_str        = request.POST.get('amtDPT3')
        
        statusMGT14        = request.POST.get('statusMGT14', 'N/A')
        srnNoMGT14         = request.POST.get('srnNoMGT14')
        srnDateMGT14_str   = request.POST.get('srnDateMGT14')
        amtMGT14_str       = request.POST.get('amtMGT14')
        
        statusAOC4         = request.POST.get('statusAOC4', 'N/A')
        srnNoAOC4          = request.POST.get('srnNoAOC4')
        srnDateAOC4_str    = request.POST.get('srnDateAOC4')
        amtAOC4_str        = request.POST.get('amtAOC4')
        
        statusMGT7         = request.POST.get('statusMGT7', 'N/A')
        srnNoMGT7          = request.POST.get('srnNoMGT7')
        srnDateMGT7_str    = request.POST.get('srnDateMGT7')
        amtMGT7_str        = request.POST.get('amtMGT7')
        
        statusForm11       = request.POST.get('statusForm11', 'N/A')
        srnNoForm11        = request.POST.get('srnNoForm11')
        srnDateForm11_str  = request.POST.get('srnDateForm11')
        amtForm11_str      = request.POST.get('amtForm11')
        
        statusForm8        = request.POST.get('statusForm8', 'N/A')
        srnNoForm8         = request.POST.get('srnNoForm8')
        srnDateForm8_str   = request.POST.get('srnDateForm8')
        amtForm8_str       = request.POST.get('amtForm8')
        
        isArchived         = 'isArchived' in request.POST
        isPinned           = 'isPinned' in request.POST


        
        company = query(user, UpdatedCompany).filter(companyName=company_name).first()
        groupName = company.groupID.groupName
        # Prepare form data to repopulate form in case of error

        form_data = request.POST.copy()
        form_data['groupName'] = groupName

        # Validate required fields
        if not company_name or not financialYear:
            messages.error(request, "Company name and Financial Year are required.")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)

        # Look up the company record using the provided company name and current sub-admin
        try:
            company = query(user, UpdatedCompany).get(companyName=company_name)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company not found.")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)

        srnDateDPT3   = parse_date(srnDateDPT3_str)
        srnDateMGT14  = parse_date(srnDateMGT14_str)
        srnDateAOC4   = parse_date(srnDateAOC4_str)
        srnDateMGT7   = parse_date(srnDateMGT7_str)
        srnDateForm11 = parse_date(srnDateForm11_str)
        srnDateForm8  = parse_date(srnDateForm8_str)

        amtDPT3   = parse_amount(amtDPT3_str)
        amtMGT14  = parse_amount(amtMGT14_str)
        amtAOC4   = parse_amount(amtAOC4_str)
        amtMGT7   = parse_amount(amtMGT7_str)
        amtForm11 = parse_amount(amtForm11_str)
        amtForm8  = parse_amount(amtForm8_str)

        try:
            # Create the AnnualFiling record without indexSRN first.
            af = AnnualFiling.objects.create(
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedBy=user
            )
            # --- Auto-generate indexSRN for AnnualFiling for the current subAdminID ---
            max_index_dict = AnnualFiling.objects.filter(subAdminID=user.subAdminID).aggregate(max_index=Max('indexSRN'))
            max_index = max_index_dict.get('max_index')
            try:
                next_index = int(max_index) + 1 if max_index is not None else 1
            except Exception:
                next_index = 1
            af.indexSRN = next_index
            af.save()
            # Optionally, create a history record for AnnualFiling.
            historyaf = HistoryAnnualFiling(
                annualFilingID = af,
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedDate   = af.modifiedDate,
                indexSRN       = af.indexSRN,
                modifiedBy=user
            )
            historyaf.save()
            messages.success(request, "Annual Filing added successfully!")
            return HttpResponseRedirect(reverse('listAnnual'))
        except Exception as e:
            messages.error(request, f"Error saving Annual Filing")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)
    return render(request, 'annualFiling/addAnnual.html', context)

@allow_only_client_users
def addTrademark(request):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    groups = query(user, UpdatedGroup)
    context = {
        'base': base,
        'user': user,
        'groups': groups
    }

    if request.method == 'POST':
        # Get data from POST request
        nameOfTrademark    = request.POST.get('nameOfTrademark')            
        applicationNo     = request.POST.get('applicationNo')         
        classNo        = request.POST.get('classNo')
        nameOfApplicant   = request.POST.get('nameOfApplicant')
        dateOfApp        = request.POST.get('dateOfApp')
        status1 = request.POST.get('status1')
        status2 = request.POST.get('status2')
        hearingDate       = request.POST.get('hearingDate')
        remark            = request.POST.get('remark')
        groupName           = request.POST.get('groupName')
        oppDate           = request.POST.get('oppDate')
        lastDate           = request.POST.get('lastDate')
        expiryDate           = request.POST.get('expiryDate')
        fees              = request.POST.get('fees', '')
        feesStatus        = request.POST.get('feesStatus')
        isArchived = 'isArchived' in request.POST

        hearingDate = parse_date(hearingDate)
        oppDate = parse_date(oppDate)
        lastDate = parse_date(lastDate)
        expiryDate = parse_date(expiryDate)
        dateOfApp = parse_date(dateOfApp)
        fees = parse_amount(fees)

        form_data = request.POST.copy()
        form_data['hearingDate'] = hearingDate
        form_data['oppDate'] = oppDate
        form_data['lastDate'] = lastDate
        form_data['expiryDate'] = expiryDate
        form_data['dateOfApp'] = dateOfApp

        required_fields = [nameOfTrademark, nameOfApplicant,  status1, groupName]
        if status1 != 'Application to be filed':
            required_fields.append(applicationNo)
        if status1 == 'Registered':
            required_fields.append(expiryDate)

        # Check required fields (optional fields for srnNo, srnDate, and amt are not required)
        if not all(required_fields):
            messages.error(request, "Please fill all required fields")
            context['form_data'] = form_data
            return render(request, 'trademark/addTrademark.html', context)
        
        try:
            group = query(user, UpdatedGroup).get(groupName=groupName)
        except UpdatedGroup.DoesNotExist:
            messages.error(request, "Group record not found.")
            form_data['groupName'] = ''
            context['form_data'] = form_data
            return render(request, 'trademark/addTrademark.html', context)

        if applicationNo:
            if query(user, Trademark).filter(applicationNo=applicationNo).exists():
                messages.error(request, "Application No. already exists.")
                form_data['applicationNo'] = ''
                context['form_data'] = form_data
                return render(request, 'trademark/addTrademark.html', context)
        if classNo and (not classNo.isdigit() or not (1 <= int(classNo) <= 45)):
            messages.error(request, "Class No. must be a number between 1 and 45.")
            form_data['classNo'] = ''
            context['form_data'] = form_data
            return render(request, 'trademark/addTrademark.html', context)
        
        # --- Auto-generate indexSRN for the current subAdminID ---
        max_index_dict = Trademark.objects.filter(subAdminID=user.subAdminID).aggregate(max_index=Max('indexSRN'))
        max_index = max_index_dict.get('max_index')
        try:
            next_index = int(max_index) + 1 if max_index is not None else 1
        except Exception:
            next_index = 1
        
        try:
            trademark = Trademark(
                subAdminID=user.subAdminID,
                nameOfTrademark=nameOfTrademark,
                applicationNo=applicationNo,
                classNo=classNo,
                nameOfApplicant=nameOfApplicant,
                dateOfApp=dateOfApp,
                status1=status1,
                status2=status2,
                hearingDate=hearingDate,
                remark=remark,
                groupID=group,
                oppDate=oppDate,
                lastDate=lastDate,
                expiryDate=expiryDate,
                fees=fees,
                feesStatus=feesStatus,
                isArchived=isArchived,
                modifiedBy=user,
                indexSRN=next_index
            )
            trademark.save()
            
            # Optionally, create a history record as well
            history_trademark = HistoryTrademark(
                trademarkID=trademark,
                subAdminID=trademark.subAdminID,
                nameOfTrademark=trademark.nameOfTrademark,
                applicationNo=trademark.applicationNo,
                classNo=trademark.classNo,
                nameOfApplicant=trademark.nameOfApplicant,
                dateOfApp=trademark.dateOfApp,
                status1=trademark.status1,
                status2=trademark.status2,
                hearingDate=trademark.hearingDate,
                remark=trademark.remark,
                groupID=trademark.groupID,
                oppDate=trademark.oppDate,
                lastDate=trademark.lastDate,
                expiryDate=trademark.expiryDate,
                fees=trademark.fees,
                feesStatus=trademark.feesStatus,
                isArchived=trademark.isArchived,
                modifiedBy=user,
                indexSRN=trademark.indexSRN,
                modifiedDate=trademark.modifiedDate  # assuming this field exists
            )
            history_trademark.save()
            
            messages.success(request, "Trademark added successfully.")
            return HttpResponseRedirect(reverse('listTrademark'))
        except Exception as e:
            messages.error(request, f"Error saving Trademark.")
            context['form_data'] = form_data
            return render(request, 'trademark/addTrademark.html', context)
    
    return render(request, 'trademark/addTrademark.html', context)


# All Update Function are here
@allow_only_client_users
def updateDSC(request, dscID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    companies = query(user, UpdatedCompany)
    try:
        dsc = query(user, UpdatedDSC).get(dscID=dscID)
        dscHistory = query(user, HistoryDSC).filter(dscID=dscID).order_by('-modifiedDate')
    except UpdatedDSC.DoesNotExist:
        messages.error(request, "DSC not found.")
        return redirect('listDSC')

    # Try to get the client for receivedFrom and deliveredTo; fallback to dsc's values if not found
    try:
        client = query(user, UpdatedClient).get(companyID=dsc.companyID)
        receivedFrom = client.clientName
        deliveredTo = client.clientName
        clientPhone = client.clientPhone
    except UpdatedClient.DoesNotExist:
        client = None
        receivedFrom = dsc.receivedFrom  # Fallback to previous value
        deliveredTo = dsc.deliveredTo    # Fallback to previous value
        clientPhone = dsc.clientPhone

    context = {
        'base': base,
        'dsc': dsc,
        'dscHistory': dscHistory,
        'user': user,
        'companies': companies,
        'options': ['IN', 'OUT'],
        'receivedFrom': receivedFrom,
        'deliveredTo': deliveredTo,
        'clientPhone': clientPhone
    }
    
    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        status = request.POST.get('status')
        location = request.POST.get('location')
        renewalDate = request.POST.get('renewalDate')
        receivedBy = request.POST.get('receivedBy', '')
        clientPhone = request.POST.get('clientPhone')
        receivedFrom = request.POST.get('receivedFrom', '')
        deliveredTo = request.POST.get('deliveredTo', '')
        deliveredBy = request.POST.get('deliveredBy', '')

        # Check if renewalDate is provided, otherwise set it to None
        renewalDate = renewalDate if renewalDate else None

        if not all([clientName, companyName, status, location]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)
        else:
            if user:
                company = query(user, UpdatedCompany).filter(companyName=companyName).first()

                if company:
                    dsc.clientName = clientName
                    dsc.companyID = company
                    dsc.status = status
                    dsc.location = location
                    dsc.renewalDate = renewalDate
                    dsc.userID = user
                    
                    # Conditional field updates based on status
                    if status == 'IN':
                        dsc.receivedFrom = receivedFrom
                        dsc.receivedBy = receivedBy
                        dsc.deliveredTo = ''  # Set to an empty string instead of None when status is IN
                        dsc.deliveredBy = ''
                        whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.receivedFrom)
                    elif status == 'OUT':
                        dsc.deliveredTo = deliveredTo
                        dsc.deliveredBy = deliveredBy
                        dsc.receivedFrom = ''  # Set to an empty string instead of None when status is OUT
                        dsc.receivedBy = ''    # Set to an empty string instead of None when status is OUT
                        whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.deliveredTo)

                    dsc.clientPhone = clientPhone
                    dsc.save()

                    # Save history
                    dscHistory = HistoryDSC(
                        dscID=dsc, clientName=clientName, companyID=company, status=status, receivedBy=receivedBy, 
                        receivedFrom=receivedFrom, deliveredTo=deliveredTo, deliveredBy=deliveredBy, location=location, renewalDate=renewalDate, 
                        clientPhone=clientPhone, userID=user, subAdminID=user.subAdminID, modifiedDate=dsc.modifiedDate
                    )
                    dscHistory.save()

                    # Send WhatsApp message
                    messages.success(request, "DSC updated successfully.")
                    context['whatsurl'] = whatsapp_url

                    return render(request, 'dsc/updateDSC.html', context)
                else:
                    messages.error(request, "Company not found.")
                    return redirect(request.path)
          
    return render(request, 'dsc/updateDSC.html', context)

@allow_only_client_users
def updateCompany(request, companyID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    
    groups = query(user, UpdatedGroup)
    try:
        company = query(user, UpdatedCompany).get(companyID=companyID)
        companyHistory = query(user, HistoryCompany).filter(companyID=companyID).all().order_by('-companyModifiedDate')
    except UpdatedCompany.DoesNotExist:
        messages.error(request, "Company not found.")
        return redirect('listCompany')
    context = {
        'base': base,
        'company': company,
        'groups': groups,
        'companyHistory': companyHistory,
        'user': user
    }
    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        companyName = request.POST.get('companyName')
        companyType = request.POST.get('companyType')
        
        if not groupName or not companyName or not companyType:
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)
        else:
            if user:
                
                group = query(user, UpdatedGroup).filter(groupName=groupName).first()

                if group:
                    companyName_normalized = companyName.lower()
                    if UpdatedCompany.objects.filter(companyName__iexact=companyName_normalized, companyType=companyType, groupID=group).exclude(companyID=companyID).exists():
                        messages.error(request, "Company already exists.")
                        return redirect(request.path)
                    else:
                        company.companyName = companyName
                        company.companyType = companyType
                        company.groupID = group
                        company.userID = user
                        company.save()

                        companyHistory = HistoryCompany(
                            companyID=company, companyName=companyName, companyType=companyType, groupID=group,
                            userID=user, subAdminID=user.subAdminID, companyModifiedDate=company.companyModifiedDate
                        )
                        companyHistory.save()

                        messages.success(request, "Company updated successfully.")
                        return redirect(request.path)
                else:
                    messages.error(request, "Group not found.")
                    return redirect(request.path)
                
    return render(request, 'company/updateCompany.html', context)

@allow_only_client_users    
def updateGroup(request, groupID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
        
    try:
        group = UpdatedGroup.objects.get(groupID=groupID)
        groupHistory = HistoryGroup.objects.filter(groupID=groupID).all().order_by('-groupModifiedDate')
    except UpdatedGroup.DoesNotExist:
        messages.error(request, "Group not found.")
        return redirect('listGroup')
    context = {
        'base': base,
        'group': group,
        'user': user,
        'groupHistory': groupHistory
    }

    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        
        if not groupName:
            messages.error(request, "Group name cannot be empty.")
            return redirect(request.path)
        else:
            if user:
                groupName_normalized = groupName.lower()
                # Check if the group already exists with the new name
                if UpdatedGroup.objects.filter(groupName__iexact=groupName_normalized).exclude(groupID=groupID).exists():
                    messages.error(request, "Group already exists.")
                    return redirect(request.path)
                
                group.groupName = groupName
                group.userID = user
                group.subAdminID = user.subAdminID
                group.save()

                groupHistory = HistoryGroup(
                    groupID=group, groupName=groupName, userID=user,
                    subAdminID=user.subAdminID, groupModifiedDate=group.groupModifiedDate
                )
                groupHistory.save()

                messages.success(request, "Group updated successfully.")
                return redirect(request.path)

    return render(request, 'group/updateGroup.html', context)

@allow_only_client_users    
def updateClient(request, clientID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    try:
        client = query(user, UpdatedClient).get(clientID=clientID)
        clientHistory = query(user, HistoryClient).filter(clientID=clientID).all().order_by('-clientModifiedDate')
    except UpdatedClient.DoesNotExist:
        messages.error(request, "Client not found.")
        return redirect('listClient')
    
    context = {
        'base': base,
        'client': client,
        'clientHistory': clientHistory,
        'user': user
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        clientPhone = request.POST.get('clientPhone')

        # Check if all fields are filled
        if not all([clientName, clientPhone]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)

        # 1. Name validation: only letters and spaces
        if not re.match(r'^[A-Za-z\s]+$', clientName):
            messages.error(request, "Client name can only contain letters and spaces.")
            return redirect(request.path)

        # 2. Phone number validation: exactly 10 digits
        if not re.match(r'^\d{10}$', clientPhone):
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect(request.path)

        if user:
            if client:
                # Check if the phone number or email already exists
                if UpdatedClient.objects.filter(clientPhone=clientPhone, clientName=clientName).exclude(clientID=clientID).exists():
                    messages.error(request, "Phone number already exists.")
                    return redirect(request.path)

                # Update client details
                client.clientName = clientName
                client.userID = user
                client.clientPhone = clientPhone
                client.save()

                # Update client history
                clientHistory = HistoryClient(
                    clientID=client, clientName=clientName, companyID=client.companyID,
                    userID=user, clientPhone=clientPhone,
                    subAdminID=user.subAdminID, clientModifiedDate=client.clientModifiedDate
                )
                clientHistory.save()

                messages.success(request, "Client updated successfully.")
                return redirect(request.path)
            else:
                messages.error(request, "Company not found.")
                return redirect(request.path)

    return render(request, 'client/updateClient.html', context)

@allow_only_client_users
def updateWork(request, formID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    
    try:
        work = Work.objects.get(formID=formID, subAdminID=user.subAdminID)
        historyWork = HistoryWork.objects.filter(formID=work.formID).all()
    except Work.DoesNotExist:
        messages.error(request, "Work not found.")
        return redirect('listWork')
    
    context = {
        'base': base,
        'historyWork': historyWork,
        'work': work
    }
    
    if request.method == 'POST':
        formNo = request.POST.get('formNo')
        matter = request.POST.get('matter')
        filingDays = request.POST.get('filingDays')
        
        # Prepare form data to repopulate form in case of errors.
        form_data = {
            'formNo': formNo,
            'matter': matter,
            'filingDays': filingDays,
        }
        
        # Validate that all required fields are provided.
        if not all([formNo, matter, filingDays]):
            messages.error(request, "Please fill all required fields.")
        # Check that filingDays is numeric.
        elif not filingDays.isdigit():
            messages.error(request, "Filing days must be a number.")
            form_data['filingDays'] = ''
        # Check if formNo already exists for the current sub-admin (excluding this record)
        elif Work.objects.filter(formNo=formNo, subAdminID=user.subAdminID).exclude(formID=formID).exists():
            messages.error(request, "Form number already exists.")
            context['form_data'] = form_data
            return render(request, 'work/updateWork.html', context)
        else:
            try:
                # Update the work record
                work.formNo = formNo
                work.matter = matter
                work.filingDays = int(filingDays)
                work.modifiedBy = user
                work.save()

                historyWork = HistoryWork(
                    formID=work,
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                    modifiedDate=work.modifiedDate
                )
                historyWork.save()

                messages.success(request, "Work updated successfully.")
                return redirect(request.path)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        # If errors exist, re-render the form with the posted data.
        context['form_data'] = form_data
        return render(request, 'work/updateWork.html', context)
    
    else:
        # For GET requests, prepopulate the form with the existing data.
        form_data = {
            'formNo': work.formNo,
            'matter': work.matter,
            'filingDays': work.filingDays,
            'formID': work.formID
        }
        context['form_data'] = form_data
        return render(request, 'work/updateWork.html', context)

@allow_only_client_users
def updatePendingWork(request, pendingWorkID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    
    # Retrieve companies, forms, and users for the form dropdowns
    companies = query(user,UpdatedCompany)
    forms = Work.objects.filter(subAdminID=user.subAdminID).all()
    users = query(user, UpdatedUser).filter(isActive="True").all()

    try:
        pending_work = query(user, PendingWork).get(pendingWorkID=pendingWorkID)
        historyPendingWork = HistoryPendingWork.objects.filter(pendingWorkID=pending_work.pendingWorkID)
    except PendingWork.DoesNotExist:
        messages.error(request, "Pending work not found.")
        return redirect('listPendingWork') 
    context = {
        'base': base,
        'companies': companies,
        'forms': forms,
        'users': users,
        'user': user,
        'pending_work': pending_work,
        'historyPendingWork': historyPendingWork
    }
    
    if request.method == 'POST':
        # Get data from POST request
        form_no             = request.POST.get('formNo')             # form number from the input
        company_name        = request.POST.get('companyName')          # company name from the input
        event_date          = request.POST.get('eventDate')
        actual_due_date     = request.POST.get('actualDueDate')
        cutOffTime          = request.POST.get('cutOffTime')           # number field used to calculate internal due date
        srnNo_input         = request.POST.get('srnNo', '')
        internal_due_date   = request.POST.get('internalDueDate')
        user_id_str         = request.POST.get('userName')
        status              = request.POST.get('status')
        srn_date_input      = request.POST.get('srnDate', '')
        amt_input           = request.POST.get('amt', '')
        remark              = request.POST.get('remark')
        billing             = request.POST.get('billing')
        fees                = request.POST.get('fees', '')
        
        # For checkboxes, assume "on" if checked.
        isArchived = 'isArchived' in request.POST
        isPinned   = 'isPinned' in request.POST
        
        srnDate = parse_date(srn_date_input)
        internal_due_date = parse_date(internal_due_date)
        event_date = parse_date(event_date)
        actual_due_date = parse_date(actual_due_date)
        amt = parse_amount(amt_input)
        fees = parse_amount(fees)

        form_data = request.POST.copy()
        form_data['srnDate'] = srnDate
        form_data['internalDueDate'] = internal_due_date
        form_data['eventDate'] = event_date
        form_data['actualDueDate'] = actual_due_date
        
        # Check required fields (optional fields are not included here)
        if not all([form_no, company_name, event_date, actual_due_date, 
                    cutOffTime, user_id_str, status, billing]):
            messages.error(request, "Please fill all required fields.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)

         # Fetch foreign key objects:
        try:
            # Look up the company by companyName and current sub-admin.
            company_instance = query(user, UpdatedCompany).get(companyName=company_name)
            groupName = company_instance.groupID.groupName
            form_data['groupName'] = groupName
            work_instance = Work.objects.get(formNo=form_no, subAdminID=user.subAdminID)
            updated_user_instance = UpdatedUser.objects.get(userName=user_id_str, subAdminID=user.subAdminID)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company record not found.")
            form_data['companyName'] = pending_work.companyID.companyName
            form_data['groupName'] = pending_work.companyID.groupID.groupName
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        except Work.DoesNotExist:
            messages.error(request, "Work record not found.")
            form_data['formNo'] = pending_work.formID.formNo
            form_data['matter'] = pending_work.formID.matter
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        except UpdatedUser.DoesNotExist:
            messages.error(request, "User record not found.")
            form_data['userID'] = pending_work.userID.userName
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        
        try:
            # Update the pending work record with new values.
            pending_work.formID           = work_instance
            pending_work.companyID        = company_instance
            pending_work.eventDate        = event_date
            pending_work.actualDueDate    = actual_due_date
            pending_work.cutOffTime       = cutOffTime
            pending_work.internalDueDate  = internal_due_date
            pending_work.userID           = updated_user_instance
            pending_work.status           = status
            pending_work.srnNo            = srnNo_input
            pending_work.srnDate          = srnDate
            pending_work.amt              = amt
            pending_work.remark           = remark
            pending_work.billing          = billing
            pending_work.fees             = fees
            pending_work.isArchived       = isArchived
            pending_work.isPinned         = isPinned
            pending_work.modifiedBy       = user.userName
        
            pending_work.save()

            history_pending_work = HistoryPendingWork(
                pendingWorkID=pending_work,
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company_instance,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo_input,
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                modifiedBy=user.userName,
                modifiedDate=pending_work.modifiedDate
            )
            history_pending_work.save()
            messages.success(request, "Pending work updated successfully.")
            return redirect(request.path)
        except Exception as e:
            messages.error(request, f"Error updating pending work")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
    
    else:
        # For GET request, prepopulate form_data with existing pending_work values.
        form_data = {
            'pendingWorkID': pending_work.pendingWorkID,
            'formNo': pending_work.formID.formNo if pending_work.formID else "",
            'matter': pending_work.formID.matter if pending_work.formID else "",
            'filingDays': pending_work.formID.filingDays if pending_work.formID else "",
            'companyName': pending_work.companyID.companyName if pending_work.companyID else "",
            'groupName': pending_work.companyID.groupID.groupName,
            'eventDate': pending_work.eventDate,
            'actualDueDate': pending_work.actualDueDate,
            'cutOffTime': pending_work.cutOffTime,
            'srnNo': pending_work.srnNo,
            'internalDueDate': pending_work.internalDueDate,
            'userName': pending_work.userID.userName if pending_work.userID else "",
            'status': pending_work.status,
            'srnDate': pending_work.srnDate,
            'amt': pending_work.amt,
            'remark': pending_work.remark,
            'billing': pending_work.billing,
            'fees': pending_work.fees,
            'isArchived': pending_work.isArchived,
            'isPinned': pending_work.isPinned 
        }
        print(form_data['status'])
        context['form_data'] = form_data
        return render(request, 'pendingWork/updatePendingWork.html', context)

@allow_only_client_users        
def updateAnnual(request, annualFilingID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')
    companies = query(user, UpdatedCompany)

    try:
        annual_filing = query(user, AnnualFiling).get(annualFilingID=annualFilingID)
        historyAnnualFiling = HistoryAnnualFiling.objects.filter(annualFilingID=annual_filing.annualFilingID)
    except AnnualFiling.DoesNotExist:
        messages.error(request, "Annual Filing not found.")
        return redirect('listAnnual')
    
    context = {
        'base': base,
        'user': user,
        'companies': companies,
        'historyAnnualFiling': historyAnnualFiling,
        'annual_filing': annual_filing
    }
    
    
    if request.method == 'POST':
        # Retrieve data from POST request
        company_name       = request.POST.get('companyName')
        financialYear      = request.POST.get('financialYear')
        
        statusDPT3         = request.POST.get('statusDPT3', 'N/A')
        srnNoDPT3          = request.POST.get('srnNoDPT3')
        srnDateDPT3_str    = request.POST.get('srnDateDPT3')
        amtDPT3_str        = request.POST.get('amtDPT3')
        
        statusMGT14        = request.POST.get('statusMGT14', 'N/A')
        srnNoMGT14         = request.POST.get('srnNoMGT14')
        srnDateMGT14_str   = request.POST.get('srnDateMGT14')
        amtMGT14_str       = request.POST.get('amtMGT14')
        
        statusAOC4         = request.POST.get('statusAOC4', 'N/A')
        srnNoAOC4          = request.POST.get('srnNoAOC4')
        srnDateAOC4_str    = request.POST.get('srnDateAOC4')
        amtAOC4_str        = request.POST.get('amtAOC4')
        
        statusMGT7         = request.POST.get('statusMGT7', 'N/A')
        srnNoMGT7          = request.POST.get('srnNoMGT7')
        srnDateMGT7_str    = request.POST.get('srnDateMGT7')
        amtMGT7_str        = request.POST.get('amtMGT7')
        
        statusForm11       = request.POST.get('statusForm11', 'N/A')
        srnNoForm11        = request.POST.get('srnNoForm11')
        srnDateForm11_str  = request.POST.get('srnDateForm11')
        amtForm11_str      = request.POST.get('amtForm11')
        
        statusForm8        = request.POST.get('statusForm8', 'N/A')
        srnNoForm8         = request.POST.get('srnNoForm8')
        srnDateForm8_str   = request.POST.get('srnDateForm8')
        amtForm8_str       = request.POST.get('amtForm8')
        
        isArchived = 'isArchived' in request.POST
        isPinned    = 'isPinned' in request.POST

        srnDateDPT3   = parse_date(srnDateDPT3_str)
        srnDateMGT14  = parse_date(srnDateMGT14_str)
        srnDateAOC4   = parse_date(srnDateAOC4_str)
        srnDateMGT7   = parse_date(srnDateMGT7_str)
        srnDateForm11 = parse_date(srnDateForm11_str)
        srnDateForm8  = parse_date(srnDateForm8_str)

        amtDPT3   = parse_amount(amtDPT3_str)
        amtMGT14  = parse_amount(amtMGT14_str)
        amtAOC4   = parse_amount(amtAOC4_str)
        amtMGT7   = parse_amount(amtMGT7_str)
        amtForm11 = parse_amount(amtForm11_str)
        amtForm8  = parse_amount(amtForm8_str)

        form_data = request.POST.copy()
        form_data['srnDateDPT3']   = srnDateDPT3
        form_data['srnDateMGT14']  = srnDateMGT14
        form_data['srnDateAOC4']   = srnDateAOC4
        form_data['srnDateMGT7']   = srnDateMGT7
        form_data['srnDateForm11'] = srnDateForm11
        form_data['srnDateForm8']  = srnDateForm8

        # Validate required fields (adjust as needed)
        if not company_name or not financialYear:
            messages.error(request, "Company name and Financial Year are required.")
            context['form_data'] = form_data
            return render(request, 'annualFiling/updateAnnual.html', context)

        # Look up the company record using the provided company name and current sub-admin.
        try:
            company = query(user, UpdatedCompany).get(companyName=company_name)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company not found.")
            form_data['companyName'] = annual_filing.companyID.companyName
            context['form_data'] = form_data
            return render(request, 'annualFiling/updateAnnual.html', context)

        try:
            # Update the AnnualFiling record with new values
            annual_filing.companyID     = company
            annual_filing.financialYear = financialYear
            
            annual_filing.statusDPT3    = statusDPT3
            annual_filing.srnNoDPT3     = srnNoDPT3
            annual_filing.srnDateDPT3   = srnDateDPT3
            annual_filing.amtDPT3       = amtDPT3
            
            annual_filing.statusMGT14   = statusMGT14
            annual_filing.srnNoMGT14    = srnNoMGT14
            annual_filing.srnDateMGT14  = srnDateMGT14
            annual_filing.amtMGT14      = amtMGT14
            
            annual_filing.statusAOC4    = statusAOC4
            annual_filing.srnNoAOC4     = srnNoAOC4
            annual_filing.srnDateAOC4   = srnDateAOC4
            annual_filing.amtAOC4       = amtAOC4
            
            annual_filing.statusMGT7    = statusMGT7
            annual_filing.srnNoMGT7     = srnNoMGT7
            annual_filing.srnDateMGT7   = srnDateMGT7
            annual_filing.amtMGT7       = amtMGT7
            
            annual_filing.statusForm11  = statusForm11
            annual_filing.srnNoForm11   = srnNoForm11
            annual_filing.srnDateForm11 = srnDateForm11
            annual_filing.amtForm11     = amtForm11
            
            annual_filing.statusForm8   = statusForm8
            annual_filing.srnNoForm8    = srnNoForm8
            annual_filing.srnDateForm8  = srnDateForm8
            annual_filing.amtForm8      = amtForm8
            
            annual_filing.isArchived    = isArchived
            annual_filing.isPinned      = isPinned
            annual_filing.modifiedBy = user
            annual_filing.save()

            historyaf = HistoryAnnualFiling(
                annualFilingID = annual_filing,
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedBy=user,
                modifiedDate   = annual_filing.modifiedDate
            )
            historyaf.save()
            messages.success(request, "Annual Filing updated successfully!")
            return redirect(request.path)
        except Exception as e:
            messages.error(request, f"Error updating Annual Filing")
            context['form_data'] = request.POST
            return render(request, 'annualFiling/updateAnnual.html', context)
    
    else:
        # For GET, prepopulate form_data with existing record values.
        form_data = {
            'annualFilingID': annual_filing.annualFilingID,
            'companyName': annual_filing.companyID.companyName if annual_filing.companyID else "",
            'groupName': annual_filing.companyID.groupID.groupName if annual_filing.companyID else "",
            'financialYear': annual_filing.financialYear,
            
            'statusDPT3': annual_filing.statusDPT3,
            'srnNoDPT3': annual_filing.srnNoDPT3,
            'srnDateDPT3': annual_filing.srnDateDPT3,
            'amtDPT3': annual_filing.amtDPT3,
            
            'statusMGT14': annual_filing.statusMGT14,
            'srnNoMGT14': annual_filing.srnNoMGT14,
            'srnDateMGT14': annual_filing.srnDateMGT14,
            'amtMGT14': annual_filing.amtMGT14,
            
            'statusAOC4': annual_filing.statusAOC4,
            'srnNoAOC4': annual_filing.srnNoAOC4,
            'srnDateAOC4': annual_filing.srnDateAOC4,
            'amtAOC4': annual_filing.amtAOC4,
            
            'statusMGT7': annual_filing.statusMGT7,
            'srnNoMGT7': annual_filing.srnNoMGT7,
            'srnDateMGT7': annual_filing.srnDateMGT7,
            'amtMGT7': annual_filing.amtMGT7,
            
            'statusForm11': annual_filing.statusForm11,
            'srnNoForm11': annual_filing.srnNoForm11,
            'srnDateForm11': annual_filing.srnDateForm11,
            'amtForm11': annual_filing.amtForm11,
            
            'statusForm8': annual_filing.statusForm8,
            'srnNoForm8': annual_filing.srnNoForm8,
            'srnDateForm8': annual_filing.srnDateForm8,
            'amtForm8': annual_filing.amtForm8,
            
            'isArchived': annual_filing.isArchived,
            'isPinned': annual_filing.isPinned
        }
        context['form_data'] = form_data
        return render(request, 'annualFiling/updateAnnual.html', context)

@allow_only_client_users
def updateTrademark(request, trademarkID):
    user_data = getUser(request)
    user = user_data.get('user')
    base = user_data.get('base')

    groups = query(user, UpdatedGroup)
    try:
        trademark = query(user, Trademark).get(trademarkID=trademarkID)
        historyTrademark = HistoryTrademark.objects.filter(trademarkID=trademark.trademarkID)
    except Trademark.DoesNotExist:  
        messages.error(request, "Trademark not found.")
        return redirect('listTrademark')
    context = {
        'base': base,
        'user': user,
        'groups': groups,
        'trademark': trademark,
        'historyTrademark': historyTrademark
    }
    
    if request.method == 'POST':
        # Get data from POST request
        nameOfTrademark    = request.POST.get('nameOfTrademark')            
        applicationNo     = request.POST.get('applicationNo')         
        classNo        = request.POST.get('classNo')
        nameOfApplicant   = request.POST.get('nameOfApplicant')
        dateOfApp        = request.POST.get('dateOfApp')
        status1 = request.POST.get('status1')
        status2 = request.POST.get('status2')
        hearingDate       = request.POST.get('hearingDate')
        remark            = request.POST.get('remark')
        groupName           = request.POST.get('groupName')
        oppDate           = request.POST.get('oppDate')
        lastDate           = request.POST.get('lastDate')
        expiryDate           = request.POST.get('expiryDate')
        fees              = request.POST.get('fees', '')
        feesStatus        = request.POST.get('feesStatus')
        isArchived = 'isArchived' in request.POST

        hearingDate = parse_date(hearingDate)
        oppDate = parse_date(oppDate)
        lastDate = parse_date(lastDate)
        expiryDate = parse_date(expiryDate)
        dateOfApp = parse_date(dateOfApp)
        fees = parse_amount(fees)

        form_data = request.POST.copy()
        form_data['hearingDate'] = hearingDate
        form_data['oppDate'] = oppDate
        form_data['lastDate'] = lastDate
        form_data['expiryDate'] = expiryDate
        form_data['dateOfApp'] = dateOfApp

        required_fields = [nameOfTrademark, nameOfApplicant,  status1, groupName]
        if status1 != 'Application to be filed':
            required_fields.append(applicationNo)
        if status1 == 'Registered':
            required_fields.append(expiryDate)

        # Check required fields (optional fields for srnNo, srnDate, and amt are not required)
        if not all(required_fields):
            messages.error(request, "Please fill all required fields")
            context['form_data'] = form_data
            return render(request, 'trademark/updateTrademark.html', context)

        try:
            # Look up the company by companyName and current sub-admin.
            group = query(user, UpdatedGroup).get(groupName=groupName)
        except UpdatedGroup.DoesNotExist:
            messages.error(request, "Group record not found.")
            form_data['groupName'] = trademark.groupID.groupName
            context['form_data'] = form_data
            return render(request, 'trademark/updateTrademark.html', context)
        
        if applicationNo:
            if query(user, Trademark).filter(applicationNo=applicationNo).exclude(trademarkID=trademarkID).exists():
                messages.error(request, "Application No. already exists.")
                form_data['applicationNo'] = ''
                context['form_data'] = form_data
                return render(request, 'trademark/updateTrademark.html', context)
        if classNo and (not classNo.isdigit() or not (1 <= int(classNo) <= 45)):
            messages.error(request, "Class No. must be a number between 1 and 45.")
            form_data['classNo'] = ''
            context['form_data'] = form_data
            return render(request, 'trademark/updateTrademark.html', context)
        
        try:
            trademark.nameOfTrademark=nameOfTrademark
            trademark.applicationNo=applicationNo
            trademark.classNo=classNo
            trademark.nameOfApplicant=nameOfApplicant
            trademark.dateOfApp=dateOfApp
            trademark.status1=status1
            trademark.status2=status2
            trademark.hearingDate=hearingDate
            trademark.remark=remark
            trademark.groupID=group
            trademark.oppDate=oppDate
            trademark.lastDate=lastDate
            trademark.expiryDate=expiryDate
            trademark.fees=fees
            trademark.feesStatus=feesStatus
            trademark.isArchived=isArchived
            trademark.modifiedBy=user
        
            trademark.save()

            history_trademark = HistoryTrademark(
                subAdminID=user.subAdminID,
                trademarkID=trademark,
                nameOfTrademark=trademark.nameOfTrademark,
                applicationNo=trademark.applicationNo,
                classNo=trademark.classNo,
                nameOfApplicant=trademark.nameOfApplicant,
                dateOfApp=trademark.dateOfApp,
                status1=trademark.status1,
                status2=trademark.status2,
                hearingDate=trademark.hearingDate,
                remark=trademark.remark,
                groupID=trademark.groupID,
                oppDate=trademark.oppDate,
                lastDate=trademark.lastDate,
                expiryDate=trademark.expiryDate,
                fees=trademark.fees,
                feesStatus=trademark.feesStatus,
                isArchived=trademark.isArchived,
                modifiedBy=user,
                indexSRN=trademark.indexSRN,
                modifiedDate=trademark.modifiedDate  # assuming this field exists
            )
            history_trademark.save()
            messages.success(request, "Trademark updated successfully.")
            return redirect(request.path)
        except Exception as e:
            messages.error(request, f"Error updating Trademark")
            context['form_data'] = form_data
            return render(request, 'trademark/updateTrademark.html', context)
    
    else:
        # For GET request, prepopulate form_data with existing pending_work values.
        form_data = {
            'trademarkID': trademark.trademarkID,
            'nameOfTrademark': trademark.nameOfTrademark,
            'applicationNo': trademark.applicationNo,
            'classNo': trademark.classNo,
            'nameOfApplicant': trademark.nameOfApplicant,
            'dateOfApp': trademark.dateOfApp,
            'status1': trademark.status1,
            'status2': trademark.status2,
            'hearingDate': trademark.hearingDate,
            'remark': trademark.remark,
            'groupName': trademark.groupID.groupName,
            'oppDate': trademark.oppDate,
            'lastDate': trademark.lastDate,
            'expiryDate': trademark.expiryDate,
            'fees': trademark.fees,
            'feesStatus': trademark.feesStatus,
            'isArchived': trademark.isArchived,
        }
        context['form_data'] = form_data
        return render(request, 'trademark/updateTrademark.html', context)


# All Delete Function are here
@allow_only_client_users
def deleteDSC(request):
    user = getUser(request).get('user')
    if request.method == 'POST':
        dscIDs = request.POST.getlist('dscIDs')
        confirmation = request.POST.get('deleteDSC')
        if confirmation:
            if not dscIDs:
                messages.error(request, "No DSCs selected for deletion.")
            else:
                count, _ = query(user, UpdatedDSC).filter(dscID__in=dscIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted DSC(s) successfully.")
                else:
                    messages.error(request, "No DSCs were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listDSC')

@allow_only_client_users
def deleteCompany(request):
    user = getUser(request).get('user')
    if request.method == 'POST':
        companyIDs = request.POST.getlist('companyIDs')
        confirmation = request.POST.get('deleteCompany')
        if confirmation:
            if not companyIDs:
                messages.error(request, "No companies selected for deletion.")
            else:
                companies_to_delete = query(user, UpdatedCompany).filter(companyID__in=companyIDs)
                undeletable_companies = []

                for company in companies_to_delete:
                    # Check if there are clients or DSCs associated with the company
                    has_clients = query(user, UpdatedClient).filter(companyID=company.companyID).exists()
                    has_dscs = query(user, UpdatedDSC).filter(companyID=company.companyID).exists()
                    has_pending_work = PendingWork.objects.filter(companyID=company.companyID).exists()
                    has_annual = AnnualFiling.objects.filter(companyID=company.companyID).exists()

                    if has_clients or has_dscs or has_pending_work or has_annual:
                        undeletable_companies.append(company.companyID)

                if undeletable_companies:
                    messages.error(request,f"Phone Book / DSC exist. You can't delete Company.")
                else:
                    count, _ = companies_to_delete.delete()
                    if count > 0:
                        messages.success(request, "Selected company(ies) deleted successfully.")
                    else:
                        messages.error(request, "No companies were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listCompany')

@allow_only_client_users
def deleteGroup(request): 
    if request.method == 'POST':
        groupIDs = request.POST.getlist('groupIDs')
        confirmation = request.POST.get('deleteGroup')
        if confirmation:
            if not groupIDs:
                messages.error(request, "No groups selected for deletion.")
            else:
                groups_to_delete = UpdatedGroup.objects.filter(groupID__in=groupIDs)
                undeletable_groups = []

                for group in groups_to_delete:
                    # Check if there are companies, clients, or DSCs associated with the group
                    has_companies = UpdatedCompany.objects.filter(groupID=group.groupID).exists()
                    has_clients = UpdatedClient.objects.filter(companyID__groupID=group.groupID).exists()
                    has_dscs = UpdatedDSC.objects.filter(companyID__groupID=group.groupID).exists()
                    has_pending_work = PendingWork.objects.filter(companyID__groupID=group.groupID).exists()
                    has_annual = AnnualFiling.objects.filter(companyID__groupID=group.groupID).exists()
                    has_trademark = Trademark.objects.filter(groupID=group.groupID).exists()

                    if has_companies or has_clients or has_dscs or has_pending_work or has_annual or has_trademark:
                        undeletable_groups.append(group.groupID)

                if undeletable_groups:
                    messages.error(request, "Company / Phone Book / DSC exist. You can't delete Group.")
                else:
                    count, _ = groups_to_delete.delete()
                    if count > 0:
                        messages.success(request, "Selected group(s) deleted successfully.")
                    else:
                        messages.error(request, "No groups were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listGroup')

@allow_only_client_users
def deleteClient(request):
    user = getUser(request).get('user')
    if request.method == 'POST':
        clientIDs = request.POST.getlist('clientIDs')
        confirmation = request.POST.get('deleteClient')
        if confirmation:
            if not clientIDs:
                messages.error(request, "No clients selected for deletion.")
            else:
                count, _ = query(user, UpdatedClient).filter(clientID__in=clientIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted client(s) successfully.")
                else:
                    messages.error(request, "No clients were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listClient')

@allow_only_client_users
def deleteWork(request):
    if request.method == 'POST':
        formIDs = request.POST.getlist('formIDs')  # List of selected work IDs
        confirmation = request.POST.get('deleteWork')  # Confirmation checkbox/button
        
        if confirmation:
            if not formIDs:
                messages.error(request, "No work records selected for deletion.")
            else:
                # Check if any of the selected work has pending work attached
                has_pending = PendingWork.objects.filter(formID__in=formIDs).exists()

                if has_pending:
                    messages.error(request, "Some Pending Work exist. You can't delete work.")
                else:
                    # If no pending work is attached, proceed with deletion
                    count, _ = Work.objects.filter(formID__in=formIDs).delete()
                    if count > 0:
                        messages.success(request, f"Deleted work record(s) successfully.")
                    else:
                        messages.error(request, "No work records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")

    return redirect('listWork')

@allow_only_client_users
def deletePendingWork(request):
    user = getUser(request).get('user')

    # Get the referring URL (e.g., from which page the POST came)
    referer = request.META.get('HTTP_REFERER', '')
    redirect_url = '/user/listPendingWork'  # Default

    if referer:
        parsed_url = urlparse(referer)
        if 'archived=true' in parsed_url.query:
            redirect_url = '/user/listPendingWork?archived=true'

    if request.method == 'POST':
        pendingWorkIDs = request.POST.getlist('pendingWorkIDs')
        confirmation = request.POST.get('deletePendingWork')
        if confirmation:
            if not pendingWorkIDs:
                messages.error(request, "No pending work records selected for deletion.")
            else:
                count, _ = query(user, PendingWork).filter(pendingWorkID__in=pendingWorkIDs).delete()

                if count > 0:
                    messages.success(request, f"Deleted pending work record(s) successfully.")
                else:
                    messages.error(request, "No pending work records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    return redirect(redirect_url)

@allow_only_client_users
def deleteAnnual(request):
    user = getUser(request).get('user')

    # Get the referring URL (e.g., from which page the POST came)
    referer = request.META.get('HTTP_REFERER', '')
    redirect_url = '/user/listAnnual'  # Default

    if referer:
        parsed_url = urlparse(referer)
        if 'archived=true' in parsed_url.query:
            redirect_url = '/user/listAnnual?archived=true'

    if request.method == 'POST':
        annualFilingIDs = request.POST.getlist('annualFilingIDs')
        confirmation = request.POST.get('deleteAnnual')
        if confirmation:
            if not annualFilingIDs:
                messages.error(request, "No annual filing records selected for deletion.")
            else:
                count, _ = query(user, AnnualFiling).filter(annualFilingID__in=annualFilingIDs).delete()

                if count > 0:
                    messages.success(request, f"Deleted annual filing record(s) successfully.")
                else:
                    messages.error(request, "No annual filing records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    return redirect(redirect_url)

@allow_only_client_users
def deleteTrademark(request):
    user = getUser(request).get('user')

    # Get the referring URL (e.g., from which page the POST came)
    referer = request.META.get('HTTP_REFERER', '')
    redirect_url = '/user/listTrademark'  # Default

    if referer:
        parsed_url = urlparse(referer)
        if 'archived=true' in parsed_url.query:
            redirect_url = '/user/listTrademark?archived=true'

    if request.method == 'POST':
        trademarkIDs = request.POST.getlist('trademarkIDs')
        confirmation = request.POST.get('deleteTrademark')
        if confirmation:
            if not trademarkIDs:
                messages.error(request, "No Trademark records selected for deletion.")
            else:
                count, _ = query(user, Trademark).filter(trademarkID__in=trademarkIDs).delete()
                
                if count > 0:
                    messages.success(request, f"Deleted Trademark record(s) successfully.")
                else:
                    messages.error(request, "No Trademark records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    return redirect(redirect_url)


# All Other Function are here
@allow_only_client_users
def updatePassword(request):
    user_data = getUser(request)
    user = user_data.get('user')
    subAdmin = user_data.get('subAdmin')
    superAdmin = user_data.get('superAdmin')
    base = user_data.get('base')
    
    if request.method == 'POST':
        oldPassword = request.POST.get('oldPassword')
        newPassword = request.POST.get('newPassword')
        confirmPassword = request.POST.get('confirmPassword')

        # Password validation function
        def validate_new_password(password):
            return (len(password) >= 8 and
                    re.search(r'[A-Za-z]', password) and
                    re.search(r'\d', password) and
                    re.search(r'[@$!%*?&#]', password))

        # Check if it's a user or subAdmin updating their password
        if user.isActive:
            if check_password(oldPassword, user.userPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        user.userPassword = make_password(newPassword)
                        user.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        elif subAdmin:
            if check_password(oldPassword, subAdmin.subAdminPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        subAdmin.subAdminPassword = make_password(newPassword)
                        subAdmin.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        elif superAdmin:
            if check_password(oldPassword, superAdmin.superAdminPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        superAdmin.superAdminPassword = make_password(newPassword)
                        superAdmin.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')

    context = {
        'base': base,
        'subAdmin': subAdmin,
        'user': user,
        'superAdmin': superAdmin,
    }
    return render(request, 'password/updatePassword.html', context)

@allow_only_client_users
def feedBack(request):
    user_data = getUser(request)
    user = user_data.get('user')
    subAdmin = user_data.get('subAdmin')
    base = user_data.get('base')

    context = {
        'base': base,
        'user': user,
        'subAdmin': subAdmin,
    }
    if request.method == 'POST':
        rating = request.POST.get('rating')
        feedbackText = request.POST.get('feedBack')

        Feedback.objects.create(rating=rating, feedbackText=feedbackText, subAdminID=user.subAdminID)
        messages.success(request, "Your feedback is submited successfully.")
        return redirect(request.path) 

    return render(request, 'contactUs/feedBack.html', context)


def fetchGroupName(request):
    if request.method == 'POST':
        companyName = request.POST.get('companyName')  # Corrected typo
        user = getUser(request).get('user')

        try:
            company = query(user, UpdatedCompany).get(companyName=companyName)
            groupName = company.groupID.groupName
            companyType = company.companyType
            try: 
                client = query(user, UpdatedClient).get(companyID=company.companyID)
                clientName = client.clientName
                clientPhone = client.clientPhone
            except:
                clientName = ''
                clientPhone = ''

            response_data = {
                'status': 'success',
                'group_name': groupName,
                'client_name': clientName,
                'client_phone': clientPhone,
                'company_type': companyType,  
                'exists': True
            }
    
        except UpdatedCompany.DoesNotExist:
            response_data = {
                'status': 'error',
                'message': 'Company name does not exist',
                'exists': False
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def fetchFormDetails(request):
    if request.method == 'POST':
        formNo = request.POST.get('formNo')  # Corrected typo
        user = getUser(request).get('user')

        subAdminID = user.subAdminID

        try:
            form = Work.objects.get(formNo=formNo, subAdminID=subAdminID)
            
            matter = form.matter
            filingDays = form.filingDays

            response_data = {
                'status': 'success',
                'form_matter': matter, 
                'filing_days': filingDays,
                'exists': True
            }
        except Work.DoesNotExist:
            response_data = {
                'status': 'error',
                'message': 'Form does not exist',
                'exists': False
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

import urllib.parse
def send_whatsapp_message(phone_number, client_name, status, person):
    # Clean the phone number (remove spaces and '+' signs)
    phone_number = phone_number.replace('+', '').replace(' ', '')
    
    if status == 'IN':
        # Create the message
        message = f"Hello {client_name}, your DSC is received {status} from {person}"
    elif status == 'OUT':
        # Create the message
        message = f"Hello {client_name}, your DSC is delivered {status} to {person}"
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Generate the WhatsApp URL
    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
    
    # Return the WhatsApp URL to be used in the frontend or backend
    return whatsapp_url

