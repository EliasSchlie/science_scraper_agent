from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
import json


def home(request):
    return HttpResponse("Hello! Elias's Django is live! 🚀 And I can just push changes.")


def login_view(request):
    if request.user.is_authenticated:
        return redirect('scraper:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            auth_login(request, user)
            return redirect(request.GET.get('next', 'scraper:home'))
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'core/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('scraper:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            auth_login(request, user)
            messages.success(request, f'Account created! You start with {user.profile.credits} credits.')
            return redirect('scraper:home')

    return render(request, 'core/register.html')


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')


@login_required
def account_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            email = request.POST.get('email')
            if email and email != request.user.email:
                if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                    messages.error(request, 'Email already in use')
                else:
                    request.user.email = email
                    request.user.save()
                    messages.success(request, 'Email updated successfully')

        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            new_password_confirm = request.POST.get('new_password_confirm')

            if not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect')
            elif new_password != new_password_confirm:
                messages.error(request, 'New passwords do not match')
            else:
                request.user.set_password(new_password)
                request.user.save()
                auth_login(request, request.user)
                messages.success(request, 'Password changed successfully')

        return redirect('account')

    return render(request, 'core/account.html')


@login_required
@require_http_methods(["GET"])
def credits_info(request):
    """API endpoint to get current user's credits"""
    return JsonResponse({
        'credits': float(request.user.profile.credits),
        'username': request.user.username
    })