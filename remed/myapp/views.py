
from cmath import e
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
import logging
from django.core.paginator import Paginator

from myapp.exceptions import UnauthorizedError

from .forms import (
    ChangeUserRoleForm,
    ConvertToProprietorForm,
    SignUpForm,
    LoginForm,
    ServiceForm,
    ClientForm,
    CustomUserCreationForm,
    CustomUserChangeForm,
    AppointmentCreationForm,
    SpecialistForm
)
from .models import (
    CustomUser,
    Client,
    Service,
    Appointment,
    Specialist,
    Testimonial,
    Comment,
    Event,
    EventRegistration,
    Payment,
    Notification,
    Transaction
)
from .utils import send_custom_notification, send_email, send_sms


logger = logging.getLogger(__name__)

def welcome(request):
    return render(request, 'welcome.html')

def is_admin(user): 
    return user.is_staff

@login_required
@user_passes_test(is_admin, login_url='login', redirect_field_name=None)
def admin_dashboard(request):
    users = CustomUser.objects.exclude(username=request.user.username)
    context = {
        'total_clients': Client.objects.count(),
        'total_users': CustomUser.objects.count(),
        'users': users,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login', redirect_field_name=None)
def add_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                role = form.cleaned_data['role']
                group = Group.objects.get(name=role)
                user.groups.add(group)

                send_email(
                    subject='Welcome to Our Platform',
                    content='<p>Thank you for signing up!</p>',
                    recipient_list=[user.email]
                )
                send_sms(
                    body='Thank you for signing up!',
                    to=user.phone_number
                )
                messages.success(request, 'User added successfully!')
                return redirect('user_list')
        except UnauthorizedError as e:
            error_message = str(e)  # Utiliser str(e) pour obtenir le message d'erreur
            messages.error(request, error_message)
        except Exception as e:
            error_message = str(e)  # Utiliser str(e) pour obtenir le message d'erreur
            messages.error(request, error_message)
    else:
        form = CustomUserCreationForm()
    return render(request, 'admin/add_user.html', {'form': form})

@login_required
def edit_user_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        try:
            form = CustomUserChangeForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                # Envoyer un email de notification
                send_email(
                    subject='Account Information Updated',
                    content=f'<p>Dear {user.first_name}, your account information has been updated successfully.</p>',
                    recipient_list=[user.email]
                )
                # Envoyer un SMS de notification
                send_sms(
                    body=f'Dear {user.first_name}, your account information has been updated successfully.',
                    to=user.phone_number
                )
                messages.success(request, 'User updated successfully!')
                return redirect('user_list')
        except Exception as e:
            error_message = str(e)  # Obtenir le message d'erreur générique
            logger.error(f"Unexpected error: {error_message}")
            logger.error(traceback.format_exc())
            messages.error(request, "An unexpected error occurred. Please try again later.")  # Message générique
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'admin/edit_user.html', {'form': form})

@login_required
def user_list_view(request):
    users = CustomUser.objects.all()
    return render(request, 'admin/user_list.html', {'users': users})

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == "POST":
        user.delete()
        return redirect('admin_dashboard')
    return render(request, 'admin/delete_user_confirm.html', {'user': user})

def is_proprietor(user):
    return user.groups.filter(name='Proprietor').exists() or user.is_superuser

@login_required
@user_passes_test(is_proprietor)
def proprietor_dashboard(request):
    services = Service.objects.filter(created_by=request.user)
    clients = Client.objects.filter(created_by=request.user)
    comments = Comment.objects.all()

    paginator_services = Paginator(services, 10)
    paginator_clients = Paginator(clients, 10)

    page_number_services = request.GET.get('page_services')
    page_services = paginator_services.get_page(page_number_services)
    
    page_number_clients = request.GET.get('page_clients')
    page_clients = paginator_clients.get_page(page_number_clients)

    context = {
        'services': services,
        'clients': clients,
        'page_services': page_services, 
        'page_clients': page_clients,
        'total_services': services.count(),
        'total_clients': clients.count(),
        'comments': comments,
    }
    return render(request, 'proprietor/proprietor_dashboard.html', context)

def is_allowed_to_add_service(user): 
    return user.groups.filter(name='Proprietor').exists() or user.is_staff

@login_required
@user_passes_test(is_allowed_to_add_service, login_url='login', redirect_field_name=None)
def create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, user=request.user)
        if form.is_valid(): 
            form.save()
            messages.success(request, 'Service added successfully!')
            return redirect('dashboard')
    else:
        form = ServiceForm(user=request.user)
    return render(request, 'proprietor/create_service.html', {'form': form})

@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, 'proprietor/client_list.html', {'clients': clients})

@login_required
def create_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST, user=request.user)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            messages.success(request, 'Client added successfully!')
            return redirect('client_list')
    else:
        form = ClientForm(user=request.user)
    return render(request, 'proprietor/create_client.html', {'form': form})

@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id, owner=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'proprietor/edit_client.html', {'form': form})

@login_required
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id, owner=request.user)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'proprietor/delete_client.html', {'client': client})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('welcome')
            else:
                messages.error(request, "Authentication failed. Please try again.")
        else:
            messages.error(request, "Error occurred during sign up.")
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Rediriger les utilisateurs déjà authentifiés vers le tableau de bord

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('welcome')

@login_required
def home(request):
    services = Service.objects.all()
    return render(request, 'home.html', {'services': services})

@login_required
def redirect_user_view(request):
    if request.user.is_authenticated:
        if request.user.is_proprietaire:  # Utilisez 'is_proprietaire' et non 'is_proprietor'
            return redirect('proprietor_dashboard')
        elif request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    return redirect('login')


@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    elif request.user.is_proprietaire:
        return redirect('proprietor_dashboard')
    else:
        return redirect('user_dashboard')

@login_required
def user_dashboard(request):
    services = Service.objects.all()
    appointments = Appointment.objects.filter(user=request.user)
    proprietors = CustomUser.objects.filter(groups__name='Proprietors')
    specialists = Specialist.objects.filter(user__in=proprietors)
    testimonials = Testimonial.objects.all()
    comments = Comment.objects.all()

    context = {
        'services': services,
        'appointments': appointments,
        'specialists': specialists,
        'testimonials': testimonials,
        'comments': comments,
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def add_comment(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        Testimonial.objects.create(user=request.user, comment=comment)
        return redirect('user_dashboard')

@login_required
def add_appointment(request):
    if request.method == 'POST':
        form = AppointmentCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment added successfully!')
            return redirect('proprietor_dashboard')
    else:
        form = AppointmentCreationForm()
    return render(request, 'proprietor/add_appointment.html', {'form': form})


def some_event_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    # Logique de l'événement
    event = "Some Important Event"
    send_custom_notification(user, event)
    messages.success(request, 'Event processed and notification sent!')
    return redirect('some_view')

@login_required
def block_user_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    user.is_active = False
    user.save()
    # Envoyer une notification
    send_email(
        subject='Your Account has been Blocked',
        content=f'<p>Dear {user.first_name}, your account has been blocked by the administrator.</p>',
        recipient_list=[user.email]
    )
    send_sms(
        body=f'Dear {user.first_name}, your account has been blocked by the administrator.',
        to=user.phone_number
    )
    messages.success(request, 'User has been blocked.')
    return redirect('user_list')

@login_required
def make_transaction_view(request, user_id, amount):
    user = get_object_or_404(CustomUser, id=user_id)
    transaction = Transaction(user=user, amount=amount)
    transaction.save()
    messages.success(request, 'Transaction completed and notification sent.')
    return redirect('transaction_list')

def password_reset_request_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        associated_users = CustomUser.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                subject = 'Password Reset Requested'
                email_template_name = 'registration/password_reset_email.html'
                context = {
                    'email': user.email,
                    'domain': request.META['HTTP_HOST'],
                    'site_name': 'YourSite',
                    'uid': uid,
                    'user': user,
                    'token': token,
                    'protocol': 'http',
                }
                email_content = render_to_string(email_template_name, context)
                send_email(subject, email_content, 'admin@yoursite.com', [user.email], fail_silently=False)
                # Envoi d'un SMS de notification
                send_sms(
                    body=f'Dear {user.first_name}, a password reset request has been initiated for your account.',
                    to=user.phone_number
                )
            messages.success(request, 'A message with reset password instructions has been sent to your inbox.')
            return redirect("login")
    return render(request, "registration/password_reset.html")

@login_required
def register_for_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    registration = EventRegistration(user=user, event=event)
    registration.save()
    messages.success(request, 'You have successfully registered for the event and a confirmation has been sent.')
    return redirect('event_list')

@login_required
def security_alert_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    # Logique pour détecter une activité suspecte
    send_email(
        subject='Security Alert: Suspicious Activity Detected',
        content=f'<p>Dear {user.first_name}, we have detected suspicious activity on your account. Please review your account activity immediately.</p>',
        recipient_list=[user.email]
    )
    send_sms(
        body=f'Dear {user.first_name}, we have detected suspicious activity on your account. Please review your account activity immediately.',
        to=user.phone_number
    )
    messages.success(request, 'Security alert sent to the user.')
    return redirect('user_list')

@login_required
def process_payment_view(request, user_id, amount):
    user = get_object_or_404(CustomUser, id=user_id)
    due_date = timezone.now() + timedelta(days=7)  # Par exemple, date d'échéance dans une semaine
    payment = Payment(user=user, amount=amount, due_date=due_date, status='Pending')
    payment.save()
    messages.success(request, 'Payment processed and reminder sent.')
    return redirect('payment_list')

def register_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Envoyer un email de bienvenue
            send_email(
                subject='Welcome to Our Platform!',
                content=f'<p>Dear {user.first_name}, welcome to our platform! We are excited to have you.</p>',
                recipient_list=[user.email]
            )
            # Envoyer un SMS de bienvenue
            send_sms(
                body=f'Dear {user.first_name}, welcome to our platform! We are excited to have you.',
                to=user.phone_number
            )
            messages.success(request, 'Registration successful and welcome message sent.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def change_user_role_view(request, user_id, new_role):
    user = get_object_or_404(CustomUser, id=user_id)
    # Modifier le rôle de l'utilisateur
    user.groups.clear()
    user.groups.add(new_role)
    user.save()
    # Envoyer une notification
    send_email(
        subject='Role Change Notification',
        content=f'<p>Dear {user.first_name}, your role on the platform has been changed to {new_role.name}.</p>',
        recipient_list=[user.email]
    )
    send_sms(
        body=f'Dear {user.first_name}, your role on the platform has been changed to {new_role.name}.',
        to=user.phone_number
    )
    messages.success(request, 'User role changed and notification sent.')
    return redirect('user_list')



# Configuration du logger
logger = logging.getLogger(__name__)

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin, login_url='login', redirect_field_name=None)
def change_user_role_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = ChangeUserRoleForm(request.POST, instance=user)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            assign_role(user, new_role)
            messages.success(request, 'User role updated successfully!')
            return redirect('user_list')
    else:
        form = ChangeUserRoleForm(instance=user)
    return render(request, 'admin/change_user_role.html', {'form': form, 'user': user})

def assign_role(user, role_name):
    group = Group.objects.get(name=role_name)
    user.groups.clear()
    user.groups.add(group)
    user.save()
    # Envoyer une notification
    send_email(
        subject='Role Change Notification',
        content=f'<p>Dear {user.first_name}, your role on the platform has been changed to {group.name}.</p>',
        recipient_list=[user.email]
    )
    send_sms(
        body=f'Dear {user.first_name}, your role on the platform has been changed to {group.name}.',
        to=user.phone_number
    )
    logger.info(f'Role {group.name} assigned to user {user.username}')


@login_required
@user_passes_test(lambda u: u.is_staff)
def convert_to_proprietor_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = ConvertToProprietorForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            # Ajouter l'utilisateur au groupe "Proprietor"
            proprietor_group = Group.objects.get(name='Proprietor')
            user.groups.add(proprietor_group)
            messages.success(request, f'User {user.username} has been converted to Proprietor!')
            return redirect('user_list')
    else:
        form = ConvertToProprietorForm(instance=user)
    return render(request, 'admin/convert_to_proprietor.html', {'form': form, 'user': user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_specialist_view(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST)
        if form.is_valid():
            specialist = form.save(commit=False)
            specialist.user = request.user
            specialist.save()
            messages.success(request, 'Specialist added successfully!')
            return redirect('specialist_list')
    else:
        form = SpecialistForm()
    return render(request, 'admin/add_specialist.html', {'form': form})
