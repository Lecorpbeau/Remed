from django.core.exceptions import PermissionDenied
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
from twilio.rest import Client

from myapp.exceptions import UnauthorizedError

def check_group(user, group_name):
    if not user.groups.filter(name=group_name).exists():
        raise PermissionDenied

def send_email(subject, content, recipient_list):
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=recipient_list,
            subject=subject,
            html_content=content,
        )
    
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
        pass 
    except UnauthorizedError as e: 
        print(str(e)) # Utiliser str(e) pour obtenir le message d'erreur 
    except Exception as e: 
        print(str(e))

# utils.py


def send_sms(body, to):
    try :
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        return message.sid
        pass 
    except UnauthorizedError as e: 
        print(str(e)) # Utiliser str(e) pour obtenir le message d'erreur 
    except Exception as e: 
        print(str(e))
        
def send_custom_notification(user, event):
    subject = f'Notification: {event}'
    content = f'<p>Dear {user.first_name},</p><p>This is to notify you about the following event: {event}</p>'
    body = f'Dear {user.first_name}, this is to notify you about the following event: {event}.'
    send_email(subject, content, [user.email])
    send_sms(body, user.phone_number)
