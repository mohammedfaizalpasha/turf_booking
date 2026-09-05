from django.urls import path
from . import views


urlpatterns = [

    # User Registration
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

    # User Logout
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

]