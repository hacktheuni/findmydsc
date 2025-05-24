from django.utils import timezone
from user.models import SubAdminSubscription, SignUP

def deactivate_expire_account():
    # Get the current time
    now = timezone.now()

    # Find all subscriptions where the end date has passed and the subscription is still active
    expired_subscriptions = SubAdminSubscription.objects.filter(endDate__lt=now, isActive=True)

    for subscription in expired_subscriptions:
        # Deactivate the user associated with this expired subscription
        user = subscription.subAdminID
        user.hasChosenPlan = False
        user.save()

        # Deactivate the subscription
        subscription.isActive = False
        subscription.save()

    
