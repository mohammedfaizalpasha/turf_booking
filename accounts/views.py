from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages


def user_login(request):

    if request.user.is_authenticated:

        if request.user.is_staff:
            return redirect("admin_dashboard")

        return redirect("user_dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Prevent admin accounts from using User Login
            if user.is_staff:

                messages.error(
                    request,
                    "Please use the Admin Login page."
                )

                return redirect("login")

            login(request, user)

            return redirect("user_dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "registration/login.html"
    )

def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Check passwords
        if password1 != password2:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("register")

        # Check username
        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists. Please choose another username."
            )

            return redirect("register")

        # Create normal user account
        User.objects.create_user(
            username=username,
            password=password1
        )

        messages.success(
            request,
            "Account created successfully! Please login."
        )

        # Go to User Login
        return redirect("login")

    return render(
        request,
        "registration/register.html"
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")

@login_required(login_url="login")
def user_dashboard(request):

    return render(
        request,
        "registration/user_dashboard.html"
    )