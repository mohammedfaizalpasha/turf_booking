from django.urls import path

from . import views


urlpatterns = [

    path(
        "turfs/",
        views.superadmin_turfs,
        name="superadmin_turfs"
    ),

    path(
        "superadmin/turfs/add/",
        views.add_turf,
        name="add_turf"
    ),

    path(
        "superadmin/turfs/<int:turf_id>/edit/",
        views.edit_turf,
        name="edit_turf"
    ),

    path(
        "superadmin/turfs/<int:turf_id>/toggle/",
        views.toggle_turf,
        name="toggle_turf"
    ),

    path(
        "superadmin/turfs/<int:turf_id>/delete/",
        views.delete_turf,
        name="delete_turf"
    ),

]