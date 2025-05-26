from django.db import models
from django.utils import timezone

# SubAdmin model for handling sub-admins
class SignUP(models.Model):
    subAdminID = models.AutoField(primary_key=True)
    subAdminName = models.CharField(max_length=255)
    subAdminType = models.CharField(max_length=50)
    subAdminEmail = models.EmailField(unique=True)
    subAdminPhone = models.CharField(max_length=15)
    subAdminCity = models.CharField(max_length=100)
    subAdminState = models.CharField(max_length=100)
    subAdminPinCode = models.CharField(max_length=10)
    subAdminPassword = models.CharField(max_length=255)
    subAdminReferralEmail = models.EmailField(null=True, blank=True)
    subAdminLogo = models.ImageField(upload_to='logos/', null=True, blank=True)
    isActive = models.BooleanField(default=True)
    subAdminRegisterDate = models.DateTimeField(auto_now_add=True)
    freeUser = models.BooleanField(default=False)  

    # Subscription-related fields
    hasChosenPlan = models.BooleanField(default=False)  # Tracks if the user has chosen a plan
    isFirstLogin = models.BooleanField(default=True)  # Tracks if this is the user's first login
    hasUsedFreePlan = models.BooleanField(default=False)  # Tracks if the user has used the free plan

    def __str__(self):
        return f'{self.subAdminName} ({self.subAdminID})'


# Subscription plans available for sub-admins
class SubscriptionPlan(models.Model):
    planID = models.AutoField(primary_key=True)
    planName = models.CharField(max_length=100)  # Example: 'Basic', 'Pro', 'Premium'
    planDescription = models.TextField()
    planMonthlyPrice = models.DecimalField(max_digits=10, decimal_places=2)  # Subscription price
    planAnnualPrice = models.DecimalField(max_digits=10, decimal_places=2)  # Subscription price
    DSCInPlan = models.CharField(max_length=100, default='')
    planDuration = models.IntegerField()  # Duration in days

    def __str__(self):
        return f'{self.planName} - ₹{self.planMonthlyPrice}'


# Linking sub-admins to their subscription plans
class SubAdminSubscription(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    planID = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE)
    startDate = models.DateTimeField(default=timezone.now)
    endDate = models.DateTimeField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    razorpayOrderID = models.CharField(max_length=100, null=True, blank=True)
    razorpayPaymentID = models.CharField(max_length=100, null=True, blank=True)
    razorpaySignature = models.CharField(max_length=255, null=True, blank=True)
    paymentStatus = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ], default='Pending')

    def __str__(self):
        return f'Subscription for {self.subAdminID.subAdminName} - {self.planID.planName}'

    def is_subscription_active(self):
        """Check if the subscription is currently active."""
        return self.endDate and self.endDate >= timezone.now()


# Razorpay payment logs for tracking transaction details
class RazorpayPaymentLog(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    planID = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE)
    orderID = models.CharField(max_length=100)  # Razorpay Order ID
    paymentID = models.CharField(max_length=100, null=True, blank=True)  # Razorpay Payment ID
    signature = models.CharField(max_length=255, null=True, blank=True)  # Razorpay Signature
    amountPaid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed')
    ], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.orderID} - {self.status}'




class UpdatedUser(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.SET_NULL, null=True, blank=True)
    userID = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=255)
    userPhone = models.CharField(max_length=15)
    userUsername = models.CharField(max_length=50)
    userPassword = models.CharField(max_length=255)
    isActive = models.BooleanField(default=True)
    deactivatedBy = models.CharField(max_length=20, null=True, blank=True)
    userModifiedDate = models.DateTimeField(auto_now=True)

    isClientUser = models.BooleanField(default=False)
    accessToPendingWork = models.BooleanField(default=False)
    accessToAnnual = models.BooleanField(default=False)
    accessToTrademark = models.BooleanField(default=False)
    canReadOnly = models.BooleanField(default=False)
    canReadWrite = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.userID}'

class HistoryUser(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.SET_NULL, null=True, blank=True)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    userName = models.CharField(max_length=255)
    userPhone = models.CharField(max_length=15)
    userUsername = models.CharField(max_length=50)
    userPassword = models.CharField(max_length=255)
    isActive = models.BooleanField(default=True)
    deactivatedBy = models.CharField(max_length=20, null=True, blank=True)
    userModifiedDate = models.DateTimeField()

    isClientUser = models.BooleanField(default=False)
    accessToPendingWork = models.BooleanField(default=False)
    accessToAnnual = models.BooleanField(default=False)
    accessToTrademark = models.BooleanField(default=False)
    canReadOnly = models.BooleanField(default=False)
    canReadWrite = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.userID}'

class UpdatedGroup(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    groupID = models.AutoField(primary_key=True)
    groupName = models.CharField(max_length=255)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    groupModifiedDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.groupID}'

class HistoryGroup(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.CASCADE)
    groupName = models.CharField(max_length=255)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    groupModifiedDate = models.DateTimeField()

    def __str__(self):
        return f'{self.groupID}'

class UpdatedCompany(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    companyID = models.AutoField(primary_key=True)
    companyName = models.CharField(max_length=255)
    companyType = models.CharField(max_length=255, default='')
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.CASCADE)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    companyModifiedDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.companyID}'

class HistoryCompany(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    companyName = models.CharField(max_length=255)
    companyType = models.CharField(max_length=255, default='')
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.CASCADE)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    companyModifiedDate = models.DateTimeField()

    def __str__(self):
        return f'{self.companyID}'

class UpdatedClient(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    clientID = models.AutoField(primary_key=True)
    clientName = models.CharField(max_length=255)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    clientPhone = models.CharField(max_length=15)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    clientModifiedDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.clientID}'

class HistoryClient(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    clientID = models.ForeignKey('UpdatedClient', on_delete=models.CASCADE)
    clientName = models.CharField(max_length=255)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    clientPhone = models.CharField(max_length=15)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    clientModifiedDate = models.DateTimeField()

    def __str__(self):
        return f'{self.clientID}'

class UpdatedDSC(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    dscID = models.AutoField(primary_key=True)
    clientName = models.CharField(max_length=255)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    receivedBy = models.CharField(max_length=255, default='')
    receivedFrom = models.CharField(max_length=255, default='')
    deliveredTo = models.CharField(max_length=255, default='')
    deliveredBy = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    renewalDate = models.DateTimeField(null=True, blank=True)
    clientPhone = models.CharField(max_length=15)
    modifiedDate = models.DateTimeField(auto_now=True)
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.dscID}'

class HistoryDSC(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    historyDSCID = models.AutoField(primary_key=True)
    dscID = models.ForeignKey('UpdatedDSC', on_delete=models.CASCADE)
    clientName = models.CharField(max_length=255)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    receivedBy = models.CharField(max_length=255, default='')
    receivedFrom = models.CharField(max_length=255, default='')
    deliveredTo = models.CharField(max_length=255, default='')
    deliveredBy = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    renewalDate = models.DateTimeField(null=True, blank=True)
    clientPhone = models.CharField(max_length=15)
    modifiedDate = models.DateTimeField()
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.dscID}'


class Feedback(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    rating = models.IntegerField()
    feedbackText = models.TextField()
    feedbackDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rating: {self.rating}, Feedback: {self.feedbackText[:50]}"
    

class SuperAdmin(models.Model):
    superAdminID = models.AutoField(primary_key=True)
    superAdminUserID = models.CharField(unique=True, max_length=255)
    superAdminPassword = models.CharField(max_length=255)
    isActive = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.superAdminUserID}'


class Work(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    formID = models.AutoField(primary_key=True)
    formNo = models.CharField(max_length=100)
    matter = models.CharField(max_length=255)
    filingDays = models.IntegerField()
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE, null=True, blank=True, default=1)
    modifiedDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.formNo} ({self.formID})"


class PendingWork(models.Model):
    pendingWorkID = models.AutoField(primary_key=True)
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    formID = models.ForeignKey('Work', on_delete=models.CASCADE)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    eventDate = models.DateField()
    cutOffTime = models.CharField(max_length=50, default='')
    actualDueDate = models.DateField()
    internalDueDate = models.DateField(default='')
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    srnNo = models.CharField(max_length=50, default='', blank=True, null=True)
    srnDate = models.DateField(blank=True, null=True)
    amt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remark = models.CharField(max_length=100, default='')
    billing = models.CharField(max_length=100)
    isArchived = models.BooleanField(default=False)
    isPinned = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField(auto_now=True)
    modifiedBy = models.CharField(max_length=100)
    # New field for auto-incremented SRN index per subAdmin
    indexSRN = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"PendingWork {self.pendingWorkID}"


class AnnualFiling(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    annualFilingID = models.AutoField(primary_key=True)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    financialYear = models.CharField(max_length=50, blank=True, null=True)
    
    statusDPT3 = models.CharField(max_length=50, blank=True, null=True)
    srnNoDPT3 = models.CharField(max_length=100, blank=True, null=True)
    srnDateDPT3 = models.DateField(blank=True, null=True, default='')
    amtDPT3 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusMGT14 = models.CharField(max_length=50, blank=True, null=True)
    srnNoMGT14 = models.CharField(max_length=100, blank=True, null=True)
    srnDateMGT14 = models.DateField(blank=True, null=True, default='')
    amtMGT14 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusAOC4 = models.CharField(max_length=50, blank=True, null=True)
    srnNoAOC4 = models.CharField(max_length=100, blank=True, null=True)
    srnDateAOC4 = models.DateField(blank=True, null=True, default='')
    amtAOC4 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusMGT7 = models.CharField(max_length=50, blank=True, null=True)
    srnNoMGT7 = models.CharField(max_length=100, blank=True, null=True)
    srnDateMGT7 = models.DateField(blank=True, null=True, default='')
    amtMGT7 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusForm11 = models.CharField(max_length=50, blank=True, null=True)
    srnNoForm11 = models.CharField(max_length=100, blank=True, null=True)
    srnDateForm11 = models.DateField(blank=True, null=True, default='')
    amtForm11 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusForm8 = models.CharField(max_length=50, blank=True, null=True)
    srnNoForm8 = models.CharField(max_length=100, blank=True, null=True)
    srnDateForm8 = models.DateField(blank=True, null=True, default='')
    amtForm8 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    isArchived = models.BooleanField(default=False)
    isPinned = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField(auto_now=True)
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE, null=True, blank=True, default=1)
    # New field for auto-incremented SRN index per subAdmin
    indexSRN = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"AnnualFiling {self.annualFilingID}"


class HistoryWork(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    historyFormID = models.AutoField(primary_key=True)
    formID = models.ForeignKey('Work', on_delete=models.CASCADE)
    formNo = models.CharField(max_length=100)
    matter = models.CharField(max_length=255)
    filingDays = models.IntegerField()
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE, null=True, blank=True, default=1)
    modifiedDate = models.DateTimeField()

    def __str__(self):
        return f"{self.formNo} ({self.formID})"


class HistoryPendingWork(models.Model):
    historyPendingWorkID = models.AutoField(primary_key=True)
    pendingWorkID = models.ForeignKey('PendingWork', on_delete=models.CASCADE)
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    formID = models.ForeignKey('Work', on_delete=models.CASCADE)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    eventDate = models.DateField()
    cutOffTime = models.CharField(max_length=50, default='')
    actualDueDate = models.DateField()
    internalDueDate = models.DateField(default='')
    userID = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    srnNo = models.CharField(max_length=50, default='', blank=True, null=True,)
    srnDate = models.DateField(blank=True, null=True)
    amt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remark = models.CharField(max_length=100, default='')
    billing = models.CharField(max_length=100)
    isArchived = models.BooleanField(default=False)
    isPinned = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField()
    modifiedBy = models.CharField(max_length=100)
    # New field for auto-incremented SRN index per subAdmin
    indexSRN = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"PendingWork {self.pendingWorkID}"


class HistoryAnnualFiling(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    historyAnnualFilingID = models.AutoField(primary_key=True)
    annualFilingID = models.ForeignKey('AnnualFiling', on_delete=models.CASCADE)
    companyID = models.ForeignKey('UpdatedCompany', on_delete=models.CASCADE)
    financialYear = models.CharField(max_length=50, blank=True, null=True)
    
    statusDPT3 = models.CharField(max_length=50, blank=True, null=True)
    srnNoDPT3 = models.CharField(max_length=100, blank=True, null=True)
    srnDateDPT3 = models.DateField(blank=True, null=True, default='')
    amtDPT3 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusMGT14 = models.CharField(max_length=50, blank=True, null=True)
    srnNoMGT14 = models.CharField(max_length=100, blank=True, null=True)
    srnDateMGT14 = models.DateField(blank=True, null=True, default='')
    amtMGT14 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusAOC4 = models.CharField(max_length=50, blank=True, null=True)
    srnNoAOC4 = models.CharField(max_length=100, blank=True, null=True)
    srnDateAOC4 = models.DateField(blank=True, null=True, default='')
    amtAOC4 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusMGT7 = models.CharField(max_length=50, blank=True, null=True)
    srnNoMGT7 = models.CharField(max_length=100, blank=True, null=True)
    srnDateMGT7 = models.DateField(blank=True, null=True, default='')
    amtMGT7 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusForm11 = models.CharField(max_length=50, blank=True, null=True)
    srnNoForm11 = models.CharField(max_length=100, blank=True, null=True)
    srnDateForm11 = models.DateField(blank=True, null=True, default='')
    amtForm11 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    statusForm8 = models.CharField(max_length=50, blank=True, null=True)
    srnNoForm8 = models.CharField(max_length=100, blank=True, null=True)
    srnDateForm8 = models.DateField(blank=True, null=True, default='')
    amtForm8 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    isArchived = models.BooleanField(default=False)
    isPinned = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField()
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE, null=True, blank=True, default=1)
    # New field for auto-incremented SRN index per subAdmin
    indexSRN = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"AnnualFiling {self.annualFilingID}"


class Trademark(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    trademarkID = models.AutoField(primary_key=True)
    nameOfTrademark = models.CharField(max_length=255)
    applicationNo = models.CharField(max_length=100, default='')
    classNo = models.CharField(max_length=100, default='')
    nameOfApplicant = models.CharField(max_length=255)
    dateOfApp = models.DateField(null=True, blank=True)
    status1 = models.CharField(max_length=50, default='')
    status2 = models.CharField(max_length=50, default='')
    hearingDate = models.DateField(null=True, blank=True)
    remark = models.CharField(max_length=100, default='')
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.CASCADE)
    oppDate = models.DateField(null=True, blank=True)
    lastDate = models.DateField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    feesStatus = models.CharField(max_length=50, default='', null=True, blank=True)
    expiryDate = models.DateField(null=True, blank=True)
    isArchived = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField(auto_now=True)
    indexSRN = models.IntegerField(null=True, blank=True)
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.trademarkID}'

class HistoryTrademark(models.Model):
    subAdminID = models.ForeignKey('SignUP', on_delete=models.CASCADE)
    trademarkID = models.ForeignKey('Trademark', on_delete=models.CASCADE)
    nameOfTrademark = models.CharField(max_length=255)
    applicationNo = models.CharField(max_length=100, default='')
    classNo = models.CharField(max_length=100, default='')
    nameOfApplicant = models.CharField(max_length=255)
    dateOfApp = models.DateField(null=True, blank=True)
    status1 = models.CharField(max_length=50, default='')
    status2 = models.CharField(max_length=50, default='', null=True, blank=True)
    hearingDate = models.DateField(null=True, blank=True)
    remark = models.CharField(max_length=100, default='')
    groupID = models.ForeignKey('UpdatedGroup', on_delete=models.CASCADE)
    oppDate = models.DateField(null=True, blank=True)
    lastDate = models.DateField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    feesStatus = models.CharField(max_length=50, default='', null=True, blank=True)
    expiryDate = models.DateField(null=True, blank=True)
    isArchived = models.BooleanField(default=False)
    modifiedDate = models.DateTimeField()
    indexSRN = models.IntegerField(null=True, blank=True)
    modifiedBy = models.ForeignKey('UpdatedUser', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.trademarkID}'