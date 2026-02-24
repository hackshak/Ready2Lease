import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Payment
from django.shortcuts import render


User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request):
    # Prevent paying twice
    if request.user.is_premium:
        return redirect("already_premium")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.build_absolute_uri("/payments/success/"),
            cancel_url=request.build_absolute_uri("/payments/cancel/"),
            customer_email=request.user.email,
            metadata={
                "user_id": request.user.id
            }
        )

        return redirect(session.url)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle successful payment
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = session["metadata"].get("user_id")
        payment_intent = session.get("payment_intent")

        try:
            user = User.objects.get(id=user_id)

            # Prevent duplicate activation
            if not user.is_premium:
                user.is_premium = True
                user.save()

            # Store payment record (idempotent)
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
            pass

    return HttpResponse(status=200)






def payment_success(request):
    return render(request, "payments/payment_success.html")


def payment_cancel(request):
    return render(request, "payments/payment_cancel.html")


@login_required
def already_premium_view(request):
    return render(request, "payments/already_premium.html")