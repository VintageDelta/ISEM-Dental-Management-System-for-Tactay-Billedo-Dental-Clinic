import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages 

# Create your views here.
def signin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print("DEBUG - Username:", username)
        print("DEBUG - Password:", password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'userprofile/sign-in.html')

def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        terms = request.POST.get("terms")

        if not terms:
            messages.error(request, "You must agree to the terms and conditions.") 
            return redirect("userprofile:signup")
        
        #password matching
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("userprofile:signup")
       
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("userprofile:signup")
    
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:signup")
        
        #user_creation
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = full_name
        user.save()
        messages.success(request, "Account created successfully. Please sign in.")
        return redirect("userprofile:signin")
    
    return render(request, 'userprofile/sign-up.html')