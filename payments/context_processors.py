from django.contrib.auth import get_user_model


def premium_status(request):
    """
    Injects `is_premium` into every template context automatically.
    Always reads fresh from the DB to avoid stale session-cached values.

    Add to settings.py TEMPLATES → OPTIONS → context_processors:
        'payments.context_processors.premium_status'
    """
    if request.user.is_authenticated:
        User = get_user_model()
        try:
            fresh_user = User.objects.get(pk=request.user.pk)
            return {"is_premium": fresh_user.is_premium}
        except User.DoesNotExist:
            pass
    return {"is_premium": False}