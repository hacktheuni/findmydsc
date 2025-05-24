from django.contrib import admin
from .models import *

@admin.register(SignUP)
class SignUPAdmin(admin.ModelAdmin):
    list_display = ('subAdminName', 'subAdminType', 'subAdminEmail', 'subAdminPhone', 'subAdminCity', 'subAdminRegisterDate')
    search_fields = ('subAdminName', 'subAdminEmail', 'subAdminPhone', 'subAdminCity')

@admin.register(UpdatedUser)
class UpdatedUserAdmin(admin.ModelAdmin):
    list_display = ('userName', 'userPhone', 'userUsername', 'userModifiedDate', 'subAdminID')
    search_fields = ('userName', 'userUsername', 'userPhone')
    list_filter = ('userModifiedDate', 'subAdminID')

@admin.register(HistoryUser)
class HistoryUserAdmin(admin.ModelAdmin):
    list_display = ('userName', 'userPhone', 'userUsername', 'userModifiedDate', 'subAdminID')
    search_fields = ('userName', 'userUsername', 'userPhone')
    list_filter = ('userModifiedDate', 'subAdminID')

@admin.register(UpdatedGroup)
class UpdatedGroupAdmin(admin.ModelAdmin):
    list_display = ('groupName', 'userID', 'groupModifiedDate', 'subAdminID')
    search_fields = ('groupName',)
    list_filter = ('groupModifiedDate', 'subAdminID')

@admin.register(HistoryGroup)
class HistoryGroupAdmin(admin.ModelAdmin):
    list_display = ('groupName', 'userID', 'groupModifiedDate', 'subAdminID')
    search_fields = ('groupName',)
    list_filter = ('groupModifiedDate', 'subAdminID')

@admin.register(UpdatedCompany)
class UpdatedCompanyAdmin(admin.ModelAdmin):
    list_display = ('companyName', 'groupID', 'userID', 'companyModifiedDate', 'subAdminID')
    search_fields = ('companyName',)
    list_filter = ('companyModifiedDate', 'subAdminID')

@admin.register(HistoryCompany)
class HistoryCompanyAdmin(admin.ModelAdmin):
    list_display = ('companyName', 'groupID', 'userID', 'companyModifiedDate', 'subAdminID')
    search_fields = ('companyName',)
    list_filter = ('companyModifiedDate', 'subAdminID')

@admin.register(UpdatedClient)
class UpdatedClientAdmin(admin.ModelAdmin):
    list_display = ('clientName', 'clientPhone', 'companyID', 'userID', 'clientModifiedDate', 'subAdminID')
    search_fields = ('clientName', 'clientPhone')
    list_filter = ('clientModifiedDate', 'subAdminID')

@admin.register(HistoryClient)
class HistoryClientAdmin(admin.ModelAdmin):
    list_display = ('clientName', 'clientPhone', 'companyID', 'userID', 'clientModifiedDate', 'subAdminID')
    search_fields = ('clientName', 'clientPhone')
    list_filter = ('clientModifiedDate', 'subAdminID')

@admin.register(UpdatedDSC)
class UpdatedDSCAdmin(admin.ModelAdmin):
    list_display = ('dscID', 'clientName', 'companyID', 'receivedBy', 'receivedFrom', 'deliveredTo', 'status', 'location', 'renewalDate', 'clientPhone', 'modifiedDate', 'userID', 'subAdminID')
    search_fields = ('clientName', 'status', 'location')
    list_filter = ('renewalDate', 'modifiedDate', 'status', 'subAdminID')

@admin.register(HistoryDSC)
class HistoryDSCAdmin(admin.ModelAdmin):
    list_display = ('dscID','historyDSCID', 'clientName', 'companyID', 'receivedBy', 'receivedFrom', 'deliveredTo', 'status', 'location', 'renewalDate', 'clientPhone', 'modifiedDate', 'userID', 'subAdminID')
    search_fields = ('clientName', 'status', 'location')
    list_filter = ('renewalDate', 'modifiedDate', 'status', 'subAdminID')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('rating', 'feedbackText', 'subAdminID')  
    search_fields = ('rating', 'feedbackText')  
    list_filter = ('rating',)  

@admin.register(SuperAdmin)
class SuperAdminAdmin(admin.ModelAdmin):
    list_display = ('superAdminUserID', 'superAdminID')
    fields = ('superAdminID', 'superAdminUserID', 'superAdminPassword')
    readonly_fields = ('superAdminID',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('planID', 'planName', 'planMonthlyPrice', 'planDuration', 'is_active')
    search_fields = ('planName',)
    list_filter = ('planDuration',)
    ordering = ('planMonthlyPrice',)

    def is_active(self, obj):
        # Determines if the plan is active based on the monthly price
        return obj.planMonthlyPrice > 0  # Example logic for active plans

    is_active.boolean = True  # Displays a boolean icon in the adminl
    is_active.short_description = 'Active'  # Column name in the admin interface

# Customizing the admin view for SubAdminSubscription
@admin.register(SubAdminSubscription)
class SubAdminSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subAdminID', 'planID', 'startDate', 'endDate', 'isActive', 'paymentStatus')
    search_fields = ('subAdminID__subAdminName', 'planID__planName')
    list_filter = ('isActive', 'paymentStatus', 'planID')
    ordering = ('startDate',)

# Customizing the admin view for RazorpayPaymentLog
@admin.register(RazorpayPaymentLog)
class RazorpayPaymentLogAdmin(admin.ModelAdmin):
    list_display = ('subAdminID', 'orderID', 'amountPaid', 'status', 'created_at')
    search_fields = ('orderID', 'subAdminID__subAdminName')
    list_filter = ('status', 'currency')
    ordering = ('created_at',)

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('formID', 'formNo', 'matter', 'filingDays')
    search_fields = ('formNo', 'matter')

@admin.register(PendingWork)
class PendingWorkAdmin(admin.ModelAdmin):
    list_display = ('pendingWorkID', 'formID', 'companyID', 'eventDate', 'status', 'srnNo', 'srnDate', 'amt', 'isArchived', 'isPinned')
    search_fields = ('formID__formNo', 'companyID__companyName', 'status')
    list_filter = ('isArchived', 'isPinned', 'status')

@admin.register(AnnualFiling)
class AnnualFilingAdmin(admin.ModelAdmin):
    list_display = ('annualFilingID', 'companyID', 'financialYear', 'isArchived', 'isPinned')
    search_fields = ('companyID__companyName', 'financialYear')
    list_filter = ('isArchived', 'isPinned')