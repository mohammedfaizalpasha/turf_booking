from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404


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

@staff_member_required
def manage_users(request):

    users = User.objects.filter(
        is_staff=False
    ).order_by(
        "-date_joined"
    )

    return render(
        request,
        "accounts/manage_users.html",
        {
            "users": users
        }
    )


@staff_member_required
def toggle_user_status(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id,
        is_staff=False
    )

    if request.method == "POST":

        user.is_active = not user.is_active

        user.save()

        messages.success(
            request,
            "User status updated successfully."
        )

    return redirect("manage_users")    

@staff_member_required
def manage_staff_admins(request):

    staff_admins = User.objects.filter(
        is_staff=True,
        is_superuser=False
    ).order_by(
        "-date_joined"
    )

    return render(
        request,
        "accounts/manage_staff_admins.html",
        {
            "staff_admins": staff_admins
        }
    )


@staff_member_required
def add_staff_admin(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

            return redirect("manage_staff_admins")

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "This username already exists."
            )

            return redirect("manage_staff_admins")

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True
        )

        messages.success(
            request,
            "Staff Admin created successfully."
        )

    return redirect("manage_staff_admins")


@staff_member_required
def toggle_staff_admin(request, user_id):

    staff_admin = get_object_or_404(
        User,
        id=user_id,
        is_staff=True,
        is_superuser=False
    )

    if request.method == "POST":

        staff_admin.is_active = not staff_admin.is_active

        staff_admin.save()

        messages.success(
            request,
            "Staff Admin status updated successfully."
        )

    return redirect("manage_staff_admins")

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404


@staff_member_required
def manage_staff(request):

    staff_members = User.objects.filter(
        is_staff=True
    ).order_by(
        "-is_superuser",
        "-date_joined"
    )

    return render(
        request,
        "accounts/manage_staff.html",
        {
            "staff_members": staff_members
        }
    )


@staff_member_required
def add_staff(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("manage_staff")

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True
        )

        messages.success(
            request,
            "Staff Admin created successfully."
        )

    return redirect("manage_staff")


@staff_member_required
def toggle_staff_status(request, staff_id):

    staff = get_object_or_404(
        User,
        id=staff_id,
        is_staff=True
    )

    if staff.is_superuser:

        messages.error(
            request,
            "Super Admin accounts cannot be disabled."
        )

        return redirect("manage_staff")

    if request.method == "POST":

        staff.is_active = not staff.is_active
        staff.save()

        messages.success(
            request,
            "Staff Admin status updated successfully."
        )

    return redirect("manage_staff")