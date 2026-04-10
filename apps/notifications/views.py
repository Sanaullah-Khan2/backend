import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

# ── NOTIFICATION SYSTEM ───────────────────────────────────────────────────────
# In production: integrate SendGrid (email) or Twilio (SMS).
# For demo: simulate sending and log to console.

@api_view(['POST'])
@permission_classes([AllowAny])
def send_email(request):
    """
    Simulate sending an email notification.
    Body: { "to": "email@example.com", "subject": "...", "body": "..." }
    """
    try:
        to = request.data.get('to', '')
        subject = request.data.get('subject', '')
        body = request.data.get('body', '')

        if not to or not subject:
            return Response({"success": False, "error": "Missing 'to' or 'subject'"}, status=400)

        # --- REAL SENDGRID INTEGRATION (uncomment when ready) ---
        # import sendgrid
        # from sendgrid.helpers.mail import Mail
        # sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        # message = Mail(from_email='noreply@eduaims.com', to_emails=to, subject=subject, plain_text_content=body)
        # sg.send(message)

        print(f"[EMAIL SIMULATION] To: {to} | Subject: {subject} | Body: {body[:80]}...")

        return Response({
            "success": True,
            "message": f"Email sent to {to}",
            "simulated": True
        })
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_sms(request):
    """
    Simulate sending an SMS notification.
    Body: { "to": "+923001234567", "message": "..." }
    """
    try:
        to = request.data.get('to', '')
        message = request.data.get('message', '')

        if not to or not message:
            return Response({"success": False, "error": "Missing 'to' or 'message'"}, status=400)

        # --- REAL TWILIO INTEGRATION (uncomment when ready) ---
        # from twilio.rest import Client
        # client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        # client.messages.create(body=message, from_=os.getenv('TWILIO_PHONE'), to=to)

        print(f"[SMS SIMULATION] To: {to} | Message: {message[:80]}...")

        return Response({
            "success": True,
            "message": f"SMS sent to {to}",
            "simulated": True
        })
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_bulk_alert(request):
    """
    Send a bulk alert to all red/yellow risk students' parents.
    Body: { "level": "red" | "yellow" | "all", "message": "..." }
    """
    try:
        level = request.data.get('level', 'all')
        message = request.data.get('message', '')

        if not message:
            return Response({"success": False, "error": "Missing 'message'"}, status=400)

        # In production: query risk_scores + students + parents, batch send.
        # For demo, simulate counts:
        counts = {"red": 8, "yellow": 15, "all": 23}
        sent_to = counts.get(level, 23)

        print(f"[BULK ALERT] Level: {level} | Sent to {sent_to} parents | Message: {message[:80]}...")

        return Response({
            "success": True,
            "message": f"Bulk alert sent to {sent_to} parent(s) for {level} risk students.",
            "sent_count": sent_to,
            "simulated": True
        })
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def notification_log(request):
    """Return a mock log of recent sent notifications."""
    data = [
        {"id": 1, "type": "email", "to": "parent1@example.com", "subject": "Risk Alert: Ali Hassan", "sent_at": "2024-03-28 09:15", "status": "delivered"},
        {"id": 2, "type": "sms",   "to": "+923001234567",        "subject": "Attendance Warning",     "sent_at": "2024-03-27 14:30", "status": "delivered"},
        {"id": 3, "type": "email", "to": "parent2@example.com", "subject": "Weekly Report Ready",    "sent_at": "2024-03-25 08:00", "status": "delivered"},
        {"id": 4, "type": "sms",   "to": "+923007654321",        "subject": "Grade Drop Alert",       "sent_at": "2024-03-24 11:45", "status": "failed"},
        {"id": 5, "type": "email", "to": "parent3@example.com", "subject": "Risk Alert: Bilal Khan", "sent_at": "2024-03-22 10:00", "status": "delivered"},
    ]
    return Response({"success": True, "data": data, "count": len(data)})
