from django.forms import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.views import LoginView as Loginview
from django.db import models
from userprofile.models import Profile
from patient.models import Patient
from appointment.models import Appointment
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.contrib.auth.password_validation import validate_password

#pagination import
from django.core.paginator import Paginator
from django.shortcuts import render

from django.views.decorators.cache import never_cache

class RoleBasedLoginView(Loginview):
    template_name = 'userprofile/sign-in.html'
    
    def form_valid(self, form):
        """Override to add custom logic after successful authentication"""
        # Login the user
        login(self.request, form.get_user())
        user = form.get_user()
        
        #  Check if first-time login AND check if profile is incomplete
        if not user.is_staff and not user.is_superuser:
            patient = getattr(user, 'patient_patient', None)
            
            # Check if patient exists and has incomplete profile (age=0 or no gender)
            if patient and (patient.age == 0 or not patient.gender):
                messages.info(self.request, "Welcome! Please complete your profile.")
                return redirect("userprofile:patient_data")
        
        #  Auto-link patient records if email matches
        if not user.is_staff and not user.is_superuser:
            try:
                existing_patient = Patient.objects.filter(
                    email=user.email, 
                    user__isnull=True
                ).first()
                
                if existing_patient:
                    existing_patient.user = user
                    existing_patient.save()
                    messages.success(self.request, "Your patient record has been linked!")
            except Exception as e:
                print(f"Patient linking error: {e}")
        
        messages.success(self.request, "Login successful.")
        return super().form_valid(form)
    
    def get_success_url(self):
        """Role-based redirect"""
        user = self.request.user
        
        # Check if patient needs to complete profile (age=0 or no gender)
        if not user.is_staff and not user.is_superuser:
            patient = getattr(user, 'patient_patient', None)
            if patient and (patient.age == 0 or not patient.gender):
                return '/user/patient_data/'
        
        # Normal role-based redirect
        if user.is_superuser:
            return '/user/admin/dashboard/'
        elif user.is_staff:
            return '/dashboard/'
        else:
            return '/user/homepage/'
    
    def get_form_class(self):
        """Use custom form that accepts email OR username"""
        from django.contrib.auth.forms import AuthenticationForm
        
        class EmailOrUsernameAuthForm(AuthenticationForm):
            def clean(self):
                username = self.cleaned_data.get('username')
                password = self.cleaned_data.get('password')
                
                if username and password:
                    #  Try email login if @ is present
                    if '@' in username:
                        try:
                            user_obj = User.objects.get(email=username)
                            username = user_obj.username
                            self.cleaned_data['username'] = username
                        except User.DoesNotExist:
                            pass  # Will fail in parent clean()
                
                return super().clean()
        
        return EmailOrUsernameAuthForm
    
def form_invalid(self, form):
        """Keep username/email when login fails"""
        messages.error(self.request, "Invalid username/email or password. Please try again.")
        return super().form_invalid(form)

@login_required
def patient_dashboard(request):
    user = request.user

    # Get patient profile
    patient = Patient.objects.filter(user=user).first()

    today = timezone.now().date()
    next_week = today + timedelta(days=7)

    # All appointments of this user
    appointments = Appointment.objects.filter(user=user)

    total_appointments = appointments.count()

    upcoming_appointments = appointments.filter(
        date__gte=today,
        status__in=["not_arrived", "arrived", "ongoing"]
    ).count()

    cancelled_appointments = appointments.filter(
        status="cancelled",
        date__gte=today - timedelta(days=7)
    ).count()

    # Next appointment
    next_appointment = appointments.filter(
        date__gte=today,
        status__in=["not_arrived", "arrived"]
    ).order_by("date", "time").first()

    context = {
        "patient": patient,
        "total_appointments": total_appointments,
        "upcoming_appointments": upcoming_appointments,
        "cancelled_appointments": cancelled_appointments,
        "next_appointment": next_appointment,
    }

    return render(request, "userprofile/homepage.html", context)

def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        terms = request.POST.get("terms")
        role = request.POST.get("role")

        if not terms:
            messages.error(request, "You must agree to the terms and conditions.") 
            return redirect("userprofile:signup")
        
        #password matching
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("userprofile:signup")
        #minimum password length
          # ✅ NEW: Validate password strength
        try:
            validate_password(password1)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect("userprofile:signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("userprofile:signup")
    
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:signup")
        
        #user creation role based
        if role == "patient":
            print("DEBUG: Creating patient user")
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name
            )
            patient_group, created = Group.objects.get_or_create(name='Patient')
            user.groups.add(patient_group)
            print("DEBUG: Creating Patient object")
            Patient.objects.create(
                user=user,
                name=f"{first_name} {last_name}",
                email=email,
                address="",
                telephone="",
                age=0,
                occupation="",
                is_guest=False,

                gender="",
                particular_condition="",
                allergy="",
                pregnancy_status="",
                medications="",
                abnormal_bleeding_history=""
            )
            print("DEBUG: Logging in user")
            login(request, user)
            print("DEBUG: About to redirect")
            messages.success(request, "Account created successfully. Please complete your patient data.")
            return redirect("userprofile:patient_data")

        elif role == "staff":
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name,
                is_active=False,   
                is_staff=False     
            )
            staff_group, created = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            messages.success(request,
                "Staff request submitted. An admin must approve your account before you can log in."
            )

        return redirect("userprofile:signin")

    return render(request, 'userprofile/sign-up.html')

@never_cache
def profile(request):
    if not request.user.is_authenticated:
        return redirect("userprofile:signin")
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        user = request.user
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, "Email already exists.")
                return redirect("userprofile:profile")
            user.email = email
        
        user.save()

        # ✅ Handle avatar upload with validation
        if 'avatar' in request.FILES:
            uploaded_file = request.FILES['avatar']
            
            # Check file extension
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            valid_extensions = ['.png', '.jpg', '.jpeg']
            
            if ext not in valid_extensions:
                messages.error(request, "Only PNG and JPEG files are allowed.")
                return redirect("userprofile:profile")
            
            # Check file size (5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if uploaded_file.size > max_size:
                messages.error(request, f"File size must be less than 5MB. Your file: {uploaded_file.size / 1024 / 1024:.2f}MB")
                return redirect("userprofile:profile")
            
            # Verify it's actually an image
            try:
                from PIL import Image
                img = Image.open(uploaded_file)
                if img.format not in ['JPEG', 'PNG']:
                    messages.error(request, "Only JPEG and PNG images are supported.")
                    return redirect("userprofile:profile")
                uploaded_file.seek(0)  # Reset file pointer after reading
            except Exception:
                messages.error(request, "Invalid image file.")
                return redirect("userprofile:profile")
            
            # Delete old avatar
            if profile.avatar:
                profile.avatar.delete()
            
            # Save new avatar
            profile.avatar = uploaded_file
            profile.save()
            messages.success(request, "Profile picture updated successfully!")
        else:
            messages.success(request, "Profile updated successfully.")
        
        return redirect("userprofile:profile")
    
    return render(request, 'userprofile/profile.html')

@login_required
def delete_avatar(request):
    """Delete user's profile avatar"""
    if request.method == "POST":
        profile = request.user.profile
        
        if profile.avatar:
            # Delete the file from disk
            profile.avatar.delete()
            profile.save()
            messages.success(request, "Profile picture removed successfully.")
        else:
            messages.info(request, "No profile picture to remove.")
        
        return redirect('userprofile:profile')
    
    return redirect('userprofile:profile')

def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("userprofile:signin")

def is_patient(user):
    
    return hasattr(user, 'patient') or not user.is_staff

@login_required
@never_cache
def patient_data(request):
    patient = getattr(request.user, 'patient_patient', None)
 
    if not patient:
        print("DEBUG: No patient found, redirecting to homepage")
        return redirect('userprofile:homepage')
    
    if request.method == "POST":

        age = request.POST.get("age")
        if age:
            try:
                patient.age = int(age)
            except ValueError:
                    pass
        
        patient.gender = request.POST.get("gender") or getattr(patient, "gender", "")
        patient.occupation = request.POST.get("occupation") or patient.occupation
        patient.telephone = request.POST.get("telephone") or patient.telephone
        patient.address = request.POST.get("address") or patient.address

        patient.particular_condition = request.POST.get("particular_condition") or getattr(patient, "particular_condition", "")
        patient.allergy = request.POST.get("allergy") or getattr(patient, "allergy", "")
        patient.pregnancy_status = request.POST.get("pregnancy_status") or getattr(patient, "pregnancy_status", "")
        patient.medications = request.POST.get("medications") or getattr(patient, "medications", "")
        patient.abnormal_bleeding_history = request.POST.get("abnormal_bleeding_history") or getattr(patient, "abnormal_bleeding_history", "")

        patient.profile_completed = True
        patient.save()
        return redirect("userprofile:homepage")

    return render(request, 'userprofile/patient_data.html', {'patient': patient})

@never_cache
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    pending_staff = User.objects.filter(is_staff=False, is_active=False)
    
    # Get all users and paginate
    all_users_qs = User.objects.all().order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(all_users_qs, 10)  # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Import models
    from appointment.models import Service, Dentist, Branch
    
    # Services Pagination
    services_qs = Service.objects.all().order_by('service_name')
    services_paginator = Paginator(services_qs, 10)  # 10 services per page
    services_page_number = request.GET.get('services_page')
    services_page_obj = services_paginator.get_page(services_page_number)

    branches = Branch.objects.all()
    return render(request, 'userprofile/admin/admin-dashboard.html', {
        'pending_staff': pending_staff,
        'all_users': page_obj.object_list,  # Paginated users
        'page_obj': page_obj,  # Pagination object
        'services_page_obj': services_page_obj,  # Paginated services
        # 'services': Service.objects.all(),
        'dentists': Dentist.objects.all(),
        'branches': branches,
    })
@never_cache
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def add_staff(request):
    """Admin can add staff directly (already active)"""
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("userprofile:admin_dashboard")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("userprofile:admin_dashboard")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:admin_dashboard")
        
        # Create staff user (active and is_staff=True)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_active=True
        )
        
        staff_group, created = Group.objects.get_or_create(name='Staff')
        user.groups.add(staff_group)
        
        messages.success(request, f"Staff {username} added successfully!")
        return redirect("userprofile:admin_dashboard")
    
    return redirect("userprofile:admin_dashboard")

@never_cache
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    """Admin can add patient users"""
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("userprofile:admin_dashboard")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("userprofile:admin_dashboard")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:admin_dashboard")
        
        # Create patient user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        
        patient_group, created = Group.objects.get_or_create(name='Patient')
        user.groups.add(patient_group)
        
        # Create patient record
        Patient.objects.create(
            user=user,
            name=f"{first_name} {last_name}",
            email=email,
            address="",
            telephone="",
            age=0,
            occupation="",
            is_guest=False,
            gender="",
            particular_condition="",
            allergy="",
            pregnancy_status="",
            medications="",
            abnormal_bleeding_history=""
        )
        
        messages.success(request, f"Patient user {username} added successfully!")
        return redirect("userprofile:admin_dashboard")
    
    return redirect("userprofile:admin_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def edit_user(request, user_id):
    """Edit user information with role management"""
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        # Update basic info
        user_to_edit.first_name = request.POST.get("first_name")
        user_to_edit.last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        
        # Check if email already exists for another user
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:admin_dashboard")
        
        user_to_edit.email = email
        
        #  Handle Role Change
        new_role = request.POST.get("role")
        
        # Prevent non-superuser from creating admins
        if new_role == "admin" and not request.user.is_superuser:
            messages.error(request, "Only admins can assign admin role.")
            return redirect("userprofile:admin_dashboard")
        
        # Prevent editing superuser's role (except by themselves)
        if user_to_edit.is_superuser and request.user.id != user_to_edit.id:
            messages.error(request, "Cannot change admin role.")
            return redirect("userprofile:admin_dashboard")
        
        # Apply role changes
        if new_role == "admin":
            user_to_edit.is_superuser = True
            user_to_edit.is_staff = True
        elif new_role == "staff":
            user_to_edit.is_superuser = False
            user_to_edit.is_staff = True
            # Add to Staff group
            staff_group, _ = Group.objects.get_or_create(name='Staff')
            user_to_edit.groups.clear()
            user_to_edit.groups.add(staff_group)
        elif new_role == "patient":
            user_to_edit.is_superuser = False
            user_to_edit.is_staff = False
            # Add to Patient group
            patient_group, _ = Group.objects.get_or_create(name='Patient')
            user_to_edit.groups.clear()
            user_to_edit.groups.add(patient_group)
        
        user_to_edit.save()
        
        messages.success(request, f"User {user_to_edit.username} updated successfully!")
        return redirect("userprofile:admin_dashboard")
    
    return redirect("userprofile:admin_dashboard")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    """Delete user"""
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        # Prevent deleting superuser
        if user_to_delete.is_superuser:
            messages.error(request, "Cannot delete admin users.")
            return redirect("userprofile:admin_dashboard")
        
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User {username} deleted successfully!")
        return redirect("userprofile:admin_dashboard")
    
from django.http import JsonResponse
from appointment.models import Service

def search_services(request):
    """AJAX endpoint for service search"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '').strip()
        
        if search_query:
            services = Service.objects.filter(
                models.Q(service_name__icontains=search_query) |
                models.Q(category__icontains=search_query)
            ).filter(is_active=True)[:10]  # Limit to 10 results
            
            services_data = [{
                'id': s.id,
                'service_name': s.service_name,
                'price': float(s.price) if s.price else 0,
                'duration': s.duration,
                'category': s.category,
            } for s in services]
            
            return JsonResponse({'services': services_data})
        else:
            return JsonResponse({'services': []})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def homepage(request):
    if request.user.is_superuser:
        return redirect('userprofile:admin_dashboard')
    elif request.user.is_staff:
        return redirect('dashboard:index')
    else:
        return patient_dashboard(request)
