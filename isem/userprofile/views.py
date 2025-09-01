from django.shortcuts import render

# Create your views here.
def signin(request):
    return render(request, 'userprofile/sign-in.html')

def signup(request):
    return render(request, 'userprofile/sign-up.html')