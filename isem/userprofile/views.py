import os
from django.forms import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.views import LoginView as Loginview
from django.db import models
from userprofile.models import Profile
from patient.models import Patient
from appointment.models import Appointment
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.contrib.auth.password_validation import validate_password
import os
from django import forms
#pagination import
from django.core.paginator import Paginator
from django.shortcuts import render

from django.views.decorators.cache import never_cache

#PasswordReset - Mobile imports
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import requests
from decouple import config

class RoleBasedLoginView(Loginview):
    template_name = 'userprofile/sign-in.html'
    
    def form_valid(self, form):
        """Override to add custom logic after successful authentication"""
        # Login the user
        login(self.request, form.get_user())
        user = form.get_user()
        
        # Check if first-time login AND check if profile is incomplete
        if not user.is_staff and not user.is_superuser:
            patient = getattr(user, 'patient_patient', None)
            
            # Check if patient exists and has incomplete profile (age=0 or no gender)
            if patient and (patient.age == 0 or not patient.gender):
                messages.info(self.request, "Welcome! Please complete your profile.")
                return redirect("userprofile:patient_data")
        
        # Auto-link patient records if email matches
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
        messages.success(self.request, "Login successful.")
        if user.is_superuser:
            return '/dashboard/'
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
                            pass  # Will fail in authentication
                    
                    #  FIX: Authenticate WITHOUT password validation
                    self.user_cache = authenticate(
                        self.request,
                        username=username,
                        password=password
                    )
                    
                    if self.user_cache is None:
                        raise forms.ValidationError(
                            "Please enter a correct username and password.",
                            code='invalid_login',
                        )
                    else:
                        self.confirm_login_allowed(self.user_cache)
                
                return self.cleaned_data
        
        return EmailOrUsernameAuthForm
    
    def form_invalid(self, form):
        """Keep username/email when login fails"""
        messages.error(self.request, "Invalid username/email or password. Please try again.")
        return super().form_invalid(form)



import random
from django.views import View
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError 
from django.db.models import Q
from .models import Profile


def generate_otp():
    """Generate 6-digit OTP"""
    # Generate a random number between 100000 and 999999
    # Convert to string for easy storage and transmission
    return str(random.randint(100000, 999999))


def send_otp_sms(mobile, otp_code):
    """Send OTP via Semaphore SMS API"""
    try:
        # API
        api_key = config('SEMAPHORE_API_KEY')  
        message = f"Tactay-Billedo Dental: Your password reset code is {otp_code}. Valid for 5 minutes."
        
        # Send POST request to Semaphore SMS API
        response = requests.post(
            'https://api.semaphore.co/api/v4/messages',
            data={
                'apikey': api_key,
                'number': mobile,   
                'message': message,
            },
            timeout=10  # 10 second timeout to prevent hanging
        )
        
        # Attempt to parse JSON response from API
        try:
            result = response.json()
        except:
            result = None
        
        # Check if request was successful (HTTP 200)
        if response.status_code == 200:
            # Handle dictionary response (most common)
            if isinstance(result, dict):
                # Success: message_id present means SMS was queued
                if 'message_id' in result:
                    return {'success': True, 'message_id': result['message_id']}
                else:
                    # Error response in dict format
                    error_msg = result.get('message', result.get('error', 'Unknown error'))
                    return {'success': False, 'error': error_msg}
            
            # Handle list response (sometimes API returns empty array on error)
            elif isinstance(result, list):
                if len(result) > 0:
                    first_item = result[0]
                    if isinstance(first_item, dict) and 'message_id' in first_item:
                        return {'success': True, 'message_id': first_item['message_id']}
                # Empty list means error
                return {'success': False, 'error': 'API returned empty response'}
            else:
                # Unexpected response format
                return {'success': False, 'error': f'Unexpected response: {result}'}
        else:
            # Non-200 HTTP status code
            error_msg = f'HTTP {response.status_code}: {response.text}'
            return {'success': False, 'error': error_msg}
            
    except requests.exceptions.Timeout:
        # Request took longer than 10 seconds
        return {'success': False, 'error': 'Request timeout'}
    except requests.exceptions.RequestException as e:
        # Network errors (no internet, DNS failure, etc.)
        return {'success': False, 'error': f'Network error: {str(e)}'}
    except Exception as e:
        # Catch any other unexpected errors
        return {'success': False, 'error': str(e)}


class ForgotPasswordView(View):
    """Step 1: Verify username/email and send OTP"""
    
    def get(self, request):
        # Display the password reset form
        return render(request, 'userprofile/password_reset.html')
    
    def post(self, request):
        # Get username or email from form and remove whitespace
        username_or_email = request.POST.get('email', '').strip()
        
        # Validate that input was provided
        if not username_or_email:
            messages.error(request, "Please enter your username or email.")
            return redirect('userprofile:password_reset')
        
        try:
            # Search for user by username OR email using Q objects
            user = User.objects.filter(
                Q(username=username_or_email) | Q(email=username_or_email)
            ).first()
            
            # Check if user exists
            if not user:
                messages.error(request, "No account found with this username or email.")
                return redirect('userprofile:password_reset')
            
            # Get or create user profile (handles case where profile doesn't exist)
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Verify user has a mobile number registered
            if not profile.mobile:
                messages.error(
                    request, 
                    "No mobile number registered for this account. Please contact support."
                )
                return redirect('userprofile:password_reset')
            
            # Generate 6-digit OTP code
            otp_code = generate_otp()
            
            # Save OTP to profile with timestamp and unverified status
            profile.otp_code = otp_code
            profile.otp_created_at = timezone.now()
            profile.otp_verified = False
            profile.save()
            
            # Send OTP via SMS
            result = send_otp_sms(profile.mobile, otp_code)
            
            # Check if SMS was sent successfully
            if result.get('success'):
                # Store user ID in session for next step
                request.session['reset_user_id'] = user.id
                
                # Mask mobile number for security (e.g., +6399****6110)
                if len(profile.mobile) > 8:
                    masked_mobile = profile.mobile[:5] + '****' + profile.mobile[-4:]
                else:
                    masked_mobile = '****' + profile.mobile[-4:]
                request.session['masked_mobile'] = masked_mobile
                
                messages.success(
                    request, 
                    f"Verification code sent to {masked_mobile}"
                )
                return redirect('userprofile:password_reset_done')
            else:
                # SMS sending failed, show error to user
                error_msg = result.get('error', 'Unknown error')
                messages.error(request, f"Failed to send SMS: {error_msg}")
                return redirect('userprofile:password_reset')
                
        except Exception as e:
            # Handle any unexpected errors
            messages.error(request, f"Error: {str(e)}")
            return redirect('userprofile:password_reset')


class PasswordResetDoneView(View):
    """Step 2: Enter OTP"""
    
    def get(self, request):
        # Verify user came from step 1 (has session data)
        if 'reset_user_id' not in request.session:
            messages.error(request, "Please start the password reset process.")
            return redirect('userprofile:password_reset')
        
        # Get user and check if locked
        user_id = request.session.get('reset_user_id')
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            
            # Check if account is locked
            if profile.is_password_reset_locked():
                lockout_time = profile.password_reset_locked_until
                time_remaining = (lockout_time - timezone.now()).total_seconds() / 60
                messages.error(
                    request, 
                    f"Account locked. Try again in {int(time_remaining)} minutes."
                )
                return redirect('userprofile:password_reset')
        except User.DoesNotExist:
            messages.error(request, "Session expired. Please try again.")
            return redirect('userprofile:password_reset')
        
        # Get masked mobile number from session
        masked_mobile = request.session.get('masked_mobile', 'your phone')
        
        # Calculate remaining attempts
        remaining_attempts = 5 - profile.password_reset_attempts
        
        # Pass data to template
        context = {
            'masked_mobile': masked_mobile,
            'remaining_attempts': remaining_attempts,
            'attempts': profile.password_reset_attempts,
        }
        return render(request, 'userprofile/password_reset_done.html', context)
    
    def post(self, request):  # ← NOW PROPERLY INDENTED INSIDE THE CLASS
        """Handle OTP verification with 5-attempt limit"""
        user_id = request.session.get('reset_user_id')

        # Verify session exists
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('userprofile:password_reset')

        # Collect 6-digit OTP from individual input fields
        otp_digits = [
            request.POST.get('digit1', ''),
            request.POST.get('digit2', ''),
            request.POST.get('digit3', ''),
            request.POST.get('digit4', ''),
            request.POST.get('digit5', ''),
            request.POST.get('digit6', ''),
        ]
        otp_entered = ''.join(otp_digits)

        # Validate all digits entered
        if len(otp_entered) != 6:
            messages.error(request, "Please enter the complete 6-digit code.")
            return redirect('userprofile:password_reset_done')

        try:
            user = User.objects.get(id=user_id)
            profile = user.profile

            # CHECK 1: Is account locked?
            if profile.is_password_reset_locked():
                remaining = profile.get_lockout_time_remaining()
                messages.error(
                    request,
                    f"Account locked due to too many failed attempts. Try again in {remaining} minute(s)."
                )
                return redirect('userprofile:password_reset')

            # CHECK 2: Has OTP expired?
            if not profile.is_otp_valid():
                messages.error(request, "OTP has expired. Please request a new one.")
                # Clear session and force restart
                request.session.pop('reset_user_id', None)
                request.session.pop('masked_mobile', None)
                return redirect('userprofile:password_reset')

            # CHECK 3: Is OTP correct?
            if profile.otp_code == otp_entered:
                # SUCCESS: Mark as verified and reset security counters
                profile.otp_verified = True
                profile.password_reset_attempts = 0
                profile.password_reset_locked_until = None
                profile.save()

                messages.success(request, "Code verified! Set your new password.")
                return redirect('userprofile:password_reset_confirm_otp')

            # WRONG OTP: Increment attempt counter
            else:
                profile.password_reset_attempts += 1

                # Check if maximum attempts reached
                if profile.password_reset_attempts >= 5:
                    # LOCK ACCOUNT: Set time lockout
                    profile.password_reset_locked_until = timezone.now() + timedelta(hours=24)#can change time herein failing attempts
                    profile.save()

                    # Clear session to prevent further attempts
                    request.session.pop('reset_user_id', None)
                    request.session.pop('masked_mobile', None)

                    messages.error(
                        request,
                        "Too many failed attempts. Your account has been locked for 30 minutes."
                    )
                    return redirect('userprofile:password_reset')
                else:
                    # Still have attempts left - save and show remaining
                    profile.save()
                    remaining_attempts = 5 - profile.password_reset_attempts

                    messages.error(
                        request,
                        f"Invalid verification code. {remaining_attempts} attempt(s) remaining."
                    )
                    return redirect('userprofile:password_reset_done')

        except User.DoesNotExist:
            messages.error(request, "Invalid session. Please try again.")
            return redirect('userprofile:password_reset')


class PasswordResetConfirmOTPView(View):
    """Step 3: Set new password"""
    
    def get(self, request):
        # Get user ID from session
        user_id = request.session.get('reset_user_id')
        
        # Verify session exists
        if not user_id:
            messages.error(request, "Please complete OTP verification first.")
            return redirect('userprofile:password_reset')
        
        try:
            # Get user and profile
            user = User.objects.get(id=user_id)
            profile = user.profile
            
            # Verify OTP was successfully verified in previous step
            if not profile.otp_verified:
                messages.error(request, "Please verify your OTP first.")
                return redirect('userprofile:password_reset_done')
            
        except User.DoesNotExist:
            messages.error(request, "Invalid session.")
            return redirect('userprofile:password_reset')
        
        # Show password reset form
        context = {
            'validlink': True,
        }
        return render(request, 'userprofile/password_reset_confirm.html', context)
    
    def post(self, request):
        # Get user ID from session
        user_id = request.session.get('reset_user_id')
        
        # Verify session is still valid
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('userprofile:password_reset')
        
        # Get both password fields
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Verify passwords match
        if new_password1 != new_password2:
            messages.error(request, "Passwords do not match.")
            return redirect('userprofile:password_reset_confirm_otp')
        
        # Validate password strength (min 8 chars, not too common, etc.)
        try:
            validate_password(new_password1)
        except ValidationError as e:
            # Show all validation errors to user
            for error in e.messages:
                messages.error(request, error)
            return redirect('userprofile:password_reset_confirm_otp')
        
        try:
            # Get user and update password
            user = User.objects.get(id=user_id)
            # Hash and save new password
            user.password = make_password(new_password1)
            user.save()
            
            # Clean up OTP data from profile
            profile = user.profile
            profile.otp_code = None
            profile.otp_created_at = None
            profile.otp_verified = False
            profile.save()
            
            # Clear session data
            request.session.pop('reset_user_id', None)
            request.session.pop('masked_mobile', None)
            
            messages.success(request, "Password changed successfully! You can now log in.")
            return redirect('userprofile:password_reset_complete')
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('userprofile:password_reset')


class PasswordResetCompleteView(View):
    """Step 4: Success page"""
    
    def get(self, request):
        # Show success page with link to sign in
        return render(request, 'userprofile/password_reset_complete.html')


class ResendOTPView(View):
    """Resend OTP code"""
    
    def post(self, request):
        # Get user ID from session
        user_id = request.session.get('reset_user_id')
        
        # Verify session is valid
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('userprofile:password_reset')
        
        try:
            # Get user and profile
            user = User.objects.get(id=user_id)
            profile = user.profile
            
            # Generate new OTP code
            otp_code = generate_otp()
            
            # Save new OTP with fresh timestamp
            profile.otp_code = otp_code
            profile.otp_created_at = timezone.now()
            profile.save()
            
            # Send new OTP via SMS
            result = send_otp_sms(profile.mobile, otp_code)
            
            # Check if SMS was sent successfully
            if result.get('success'):
                messages.success(request, "New verification code sent!")
            else:
                error_msg = result.get('error', 'Unknown error')
                messages.error(request, f"Failed to send SMS: {error_msg}")
                
        except User.DoesNotExist:
            messages.error(request, "Invalid session.")
        
        # Return to OTP entry page
        return redirect('userprofile:password_reset_done')


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
                birthdate=None,
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
@never_cache
def profile(request):
    if not request.user.is_authenticated:
        return redirect("userprofile:signin")
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        mobile = request.POST.get("mobile")
        country_code = request.POST.get("country_code", "+63")

        user = request.user
        
        # Validate and save username
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, "Username already taken.")
                return redirect("userprofile:profile")
            user.username = username
        
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
        
        # ✅ FIXED: Save mobile with better error handling
        if mobile:
            full_mobile = f"{country_code}{mobile}"
            
            # Save to Profile
            profile.mobile = full_mobile
            profile.save()
            print(f"✅ Saved to Profile: {full_mobile}")
            
            # ✅ FIXED: Sync to Patient with proper error handling
            from patient.models import Patient
            
            try:
                # Try multiple ways to find patient
                patient = None
                
                # Method 1: Try by user relationship
                try:
                    patient = Patient.objects.get(user=user)
                    print(f"✅ Found patient by user: {patient.name}")
                except Patient.DoesNotExist:
                    print("⚠️ No patient linked by user")
                
                # Method 2: Try by email
                if not patient:
                    try:
                        patient = Patient.objects.get(email=user.email)
                        print(f"✅ Found patient by email: {patient.name}")
                        # Link the patient to user
                        patient.user = user
                    except Patient.DoesNotExist:
                        print(f"⚠️ No patient found with email: {user.email}")
                    except Patient.MultipleObjectsReturned:
                        # If multiple, get the non-guest one
                        patient = Patient.objects.filter(email=user.email, is_guest=False).first()
                        if patient:
                            print(f"✅ Found non-guest patient: {patient.name}")
                            patient.user = user
                
                # Update patient telephone
                if patient:
                    patient.telephone = full_mobile
                    patient.save()
                    print(f"✅ Synced to Patient: {patient.name} - {full_mobile}")
                    messages.success(request, "Profile and patient record updated successfully.")
                else:
                    print("⚠️ No patient record found to sync")
                    messages.success(request, "Profile updated successfully. (No patient record found)")
                    
            except Exception as e:
                print(f"❌ Patient sync error: {type(e).__name__}: {e}")
                messages.warning(request, f"Profile updated, but patient sync failed: {e}")
            
        # Handle avatar upload with validation
        if 'avatar' in request.FILES:
            uploaded_file = request.FILES['avatar']
            
            # Check file extension
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            valid_extensions = ['.png', '.jpg', '.jpeg']
            
            if ext not in valid_extensions:
                messages.error(request, "Only PNG and JPEG files are allowed.")
                return redirect("userprofile:profile")
            
            # Check file size (5MB)
            max_size = 5 * 1024 * 1024
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
                uploaded_file.seek(0)
            except Exception:
                messages.error(request, "Invalid image file.")
                return redirect("userprofile:profile")
            
            # Delete old avatar
            if profile.avatar:
                profile.avatar.delete()
            
            # Save new avatar
            profile.avatar = uploaded_file
            profile.save()
            
            if not mobile:
                messages.success(request, "Profile picture updated successfully!")
        else:
            if not mobile:
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
    messages.info(request, "You have been logged out.")
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
        birthdate = request.POST.get("birthdate")
        if birthdate:
            try:
                patient.birthdate = birthdate  
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

    return render(request, 'userprofile/patient_data.html', {'patient': patient, 'today': date.today()})

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

# ---------------- CREATE VIEWS ---------------- #
from appointment.models import Dentist, Service, Branch

@login_required
def dentist_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        specialization = request.POST.get("specialization")
        contact_number = request.POST.get("contact_number")
        email = request.POST.get("email")

        Dentist.objects.create(
            name=name,
            specialization=specialization,
            contact_number=contact_number,
            email=email,
        )

        messages.success(request, "Dentist added successfully!")

    return redirect("userprofile:admin_dashboard")

@login_required
def service_create(request):
    if request.method == "POST":
        service_name = request.POST.get("service_name")
        category = request.POST.get("category")
        duration = request.POST.get("duration")
        price = request.POST.get("price")

        Service.objects.create(
            service_name=service_name,
            category=category,
            duration=duration,
            price=price,
        )

        messages.success(request, "Service added successfully!")
    
    return redirect("userprofile:admin_dashboard")

@login_required
def dentist_delete(request, pk):
    Dentist.objects.filter(pk=pk).delete()
    messages.success(request, "Dentist deleted successfully!")
    return redirect("userprofile:admin_dashboard")


@login_required
def service_delete(request, pk):
    Service.objects.filter(pk=pk).delete()
    messages.success(request, "Service deleted successfully!")
    return redirect("userprofile:admin_dashboard")

@login_required
def dentist_update(request, pk):
    dentist = Dentist.objects.get(pk=pk)

    if request.method == "POST":
        dentist.name = request.POST.get("name")
        dentist.specialization = request.POST.get("specialization")
        dentist.contact_number = request.POST.get("contact_number")
        dentist.email = request.POST.get("email")
        dentist.save()

    messages.success(request, "Dentist updated successfully!")

    return redirect("userprofile:admin_dashboard")


@login_required
def service_update(request, pk):
    service = Service.objects.get(pk=pk)

    if request.method == "POST":
        service.service_name = request.POST.get("service_name")
        service.category = request.POST.get("category")
        service.duration = request.POST.get("duration")
        service.price = request.POST.get("price")
        service.save()

    messages.success(request, "Service updated successfully!")

    return redirect("userprofile:admin_dashboard")


@login_required
def branch_update(request, pk):
    branch = Branch.objects.get(pk=pk)

    if request.method == "POST":
        branch.name = request.POST.get("name")
        branch.address = request.POST.get("address")
        branch.contact_number = request.POST.get("contact_number")
        branch.save()

    messages.success(request, "Branch updated successfully!")

    return redirect("userprofile:admin_dashboard")

@login_required
def homepage(request):
    if request.user.is_superuser:
        return redirect('userprofile:admin_dashboard')
    elif request.user.is_staff:
        return redirect('dashboard:index')
    else:
        return patient_dashboard(request)
