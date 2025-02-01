from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, User, Group, Permission
from myapp.utils import send_email, send_sms
from remed import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_proprietaire = models.BooleanField(default=False)
    objects = CustomUserManager()

    def __str__(self):
        return self.username
       
class Client(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=200)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients_created')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_created')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_owned')

    def __str__(self):
        return self.name

class Appointment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    specialist = models.ForeignKey('Specialist', on_delete=models.CASCADE)
    date = models.DateTimeField()

    def __str__(self):
        return f'Appointment with {self.specialist.user.username} for {self.service.name}'

class Specialist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    speciality = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.speciality}"

class Testimonial(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return f'Testimonial by {self.user.username}'

class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content}'

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Envoyer un email de notification
        send_email(
            subject=f'New Message from {self.sender.username}',
            content=f'<p>You have received a new message from {self.sender.username}.</p><p>Subject: {self.subject}</p>',
            recipient_list=[self.recipient.email]
        )
        # Envoyer un SMS de notification
        send_sms(
            body=f'You have received a new message from {self.sender.username}. Subject: {self.subject}',
            to=self.recipient.phone_number
        )

    def __str__(self):
        return f'Message from {self.sender.username} to {self.recipient.username}'

class Event(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    event_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Envoyer un rappel d'événement
        send_email(
            subject=f'Reminder: {self.title}',
            content=f'<p>This is a reminder for your event: {self.title}</p><p>Description: {self.description}</p><p>Date: {self.event_date}</p>',
            recipient_list=[self.user.email]
        )
        send_sms(
            body=f'Reminder: {self.title}. Description: {self.description}. Date: {self.event_date}',
            to=self.user.phone_number
        )

    def __str__(self):
        return self.title

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Envoyer une confirmation de transaction
        send_email(
            subject='Transaction Confirmation',
            content=f'<p>Dear {self.user.first_name}, your transaction of {self.amount} has been completed successfully.</p>',
            recipient_list=[self.user.email]
        )
        send_sms(
            body=f'Dear {self.user.first_name}, your transaction of {self.amount} has been completed successfully.',
            to=self.user.phone_number
        )

    def __str__(self):
        return f'Transaction of {self.amount} by {self.user.username}'

class EventRegistration(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Envoyer une confirmation d'inscription par email
        send_email(
            subject='Event Registration Confirmed',
            content=f'<p>Dear {self.user.first_name}, you have successfully registered for the event: {self.event.title}.</p>',
            recipient_list=[self.user.email]
        )
        # Envoyer une confirmation d'inscription par

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid')])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 'Pending':
            # Envoyer un rappel de paiement par email
            send_email(
                subject='Payment Reminder',
                content=f'<p>Dear {self.user.first_name}, this is a reminder that your payment of {self.amount} is due on {self.due_date}.</p>',
                recipient_list=[self.user.email]
            )
            # Envoyer un rappel de paiement par SMS
            send_sms(
                body=f'Dear {self.user.first_name}, this is a reminder that your payment of {self.amount} is due on {self.due_date}.',
                to=self.user.phone_number
            )

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username}'
