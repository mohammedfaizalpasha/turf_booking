from django.urls import path

from . import views


urlpatterns = [

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.user_login,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "dashboard/",
        views.user_dashboard,
        name="user_dashboard"
    ),

    path(
        "manage-users/",
        views.manage_users,
        name="manage_users"
    ),

    path(
        "manage-users/<int:user_id>/toggle/",
        views.toggle_user_status,
        name="toggle_user_status"
    ),

]