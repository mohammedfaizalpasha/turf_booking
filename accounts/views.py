from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.contrib.auth.models import User
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)


def is_super_admin(user):

    return (
        user.is_authenticated
        and user.is_superuser
    )


def register(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        ).strip()

        email = request.POST.get(
            "email"
        ).strip()

        password = request.POST.get(
            "password"
        )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            "Account created successfully. Please login."
        )

        return redirect("login")

    return render(
        request,
        "accounts/register.html"
    )


def user_login(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_active:

                messages.error(
                    request,
                    "Your account has been deactivated."
                )

                return redirect("login")

            login(
                request,
                user
            )

            if user.is_superuser or user.is_staff:

                return redirect(
                    "admin_dashboard"
                )

            return redirect(
                "user_dashboard"
            )

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )


@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")


@login_required
def user_dashboard(request):

    return render(
        request,
        "accounts/user_dashboard.html"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def manage_users(request):

    users = User.objects.filter(
        is_staff=False,
        is_superuser=False
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


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def toggle_user_status(
    request,
    user_id
):

    if request.method != "POST":

        return redirect(
            "manage_users"
        )

    user = get_object_or_404(
        User,
        id=user_id,
        is_staff=False,
        is_superuser=False
    )

    user.is_active = not user.is_active

    user.save()

    if user.is_active:

        messages.success(
            request,
            f"{user.username} has been activated."
        )

    else:

        messages.success(
            request,
            f"{user.username} has been deactivated."
        )

    return redirect(
        "manage_users"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def manage_staff(request):

    staff_members = User.objects.filter(
        is_staff=True
    ).order_by(
        "-is_superuser",
        "username"
    )

    return render(
        request,
        "accounts/manage_staff.html",
        {
            "staff_members": staff_members
        }
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def add_staff(request):

    if request.method != "POST":

        return redirect(
            "manage_staff"
        )

    username = request.POST.get(
        "username"
    ).strip()

    email = request.POST.get(
        "email"
    ).strip()

    password = request.POST.get(
        "password"
    )

    if not username or not password:

        messages.error(
            request,
            "Username and password are required."
        )

        return redirect(
            "manage_staff"
        )

    if User.objects.filter(
        username=username
    ).exists():

        messages.error(
            request,
            f'The username "{username}" already exists.'
        )

        return redirect(
            "manage_staff"
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    user.is_staff = True
    user.is_active = True
    user.is_superuser = False

    user.save()

    messages.success(
        request,
        f"Staff admin {username} created successfully."
    )

    return redirect(
        "manage_staff"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def toggle_staff_status(
    request,
    user_id
):

    if request.method != "POST":

        return redirect(
            "manage_staff"
        )

    staff = get_object_or_404(
        User,
        id=user_id,
        is_staff=True
    )

    if staff.is_superuser:

        messages.error(
            request,
            "Super Admin accounts cannot be modified."
        )

        return redirect(
            "manage_staff"
        )

    staff.is_active = not staff.is_active

    staff.save()

    if staff.is_active:

        messages.success(
            request,
            f"{staff.username} has been activated."
        )

    else:

        messages.success(
            request,
            f"{staff.username} has been deactivated."
        )

    return redirect(
        "manage_staff"
    )