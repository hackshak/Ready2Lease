import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Payment

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


# ─── CREATE CHECKOUT SESSION ───────────────────────────────────────────────────
@login_required
def create_checkout_session(request):
    # Re-fetch user from DB to avoid stale session cache
    user = User.objects.get(pk=request.user.pk)

    if user.is_premium:
        return redirect("already_premium")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="payment",  # one-time payment (not "subscription")
            success_url=(
                request.build_absolute_uri("/payments/success/")
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=request.build_absolute_uri("/payments/cancel/"),
            customer_email=user.email,
            metadata={
                "user_id": str(user.id)  # metadata values must be strings
            }
        )
        return redirect(session.url)

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


# ─── STRIPE WEBHOOK ────────────────────────────────────────────────────────────
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # metadata values are always strings — cast explicitly
        user_id = session["metadata"].get("user_id")
        payment_intent = session.get("payment_intent")

        try:
            user = User.objects.get(id=int(user_id))

            if not user.is_premium:
                user.is_premium = True
                user.save()

            # Idempotent — safe to call multiple times (webhook may fire >once)
            Payment.objects.get_or_create(
                stripe_session_id=session["id"],
                defaults={
                    "user": user,
                    "stripe_payment_intent": payment_intent,
                    "amount": session["amount_total"],
                    "currency": session["currency"],
                }
            )

        except User.DoesNotExist:
            # Log this in production — it should never happen
            pass

    return HttpResponse(status=200)


# ─── PAYMENT SUCCESS ───────────────────────────────────────────────────────────
# Immediately activates premium by querying Stripe directly.
# The webhook above is the reliable backup — both are idempotent.
@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")

    if session_id:
        user = User.objects.get(pk=request.user.pk)

        if not user.is_premium:
            try:
                stripe_session = stripe.checkout.Session.retrieve(session_id)

                # SECURITY: ensure this session belongs to the logged-in user
                session_user_id = stripe_session.metadata.get("user_id")
                if str(user.id) != str(session_user_id):
                    # Silently ignore — don't reveal that the session exists
                    return render(request, "payments/payment_success.html")

                if stripe_session.payment_status == "paid":
                    user.is_premium = True
                    user.save()

                    # Idempotent — safe if webhook already created the record
                    Payment.objects.get_or_create(
                        stripe_session_id=stripe_session.id,
                        defaults={
                            "user": user,
                            "stripe_payment_intent": stripe_session.payment_intent,
                            "amount": stripe_session.amount_total,
                            "currency": stripe_session.currency,
                        }
                    )

            except stripe.error.StripeError:
                # Webhook will handle it — don't crash the success page
                pass

    return render(request, "payments/payment_success.html")


# ─── PAYMENT CANCEL ────────────────────────────────────────────────────────────
def payment_cancel(request):
    return render(request, "payments/payment_cancel.html")


# ─── ALREADY PREMIUM ───────────────────────────────────────────────────────────
@login_required
def already_premium_view(request):
    return render(request, "payments/already_premium.html")