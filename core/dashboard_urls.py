from django.urls import path
from . import dashboard_views as views

urlpatterns = [
    path("login/", views.dashboard_login, name="dashboard-login"),
    path("logout/", views.dashboard_logout, name="dashboard-logout"),
    path("", views.dashboard_home, name="dashboard-home"),
    path("<slug:section>/", views.section_list, name="dashboard-list"),
    path("<slug:section>/new/", views.section_create, name="dashboard-create"),
    path("<slug:section>/<int:pk>/edit/", views.section_edit, name="dashboard-edit"),
    path("<slug:section>/<int:pk>/delete/", views.section_delete, name="dashboard-delete"),
    path("<slug:section>/<int:pk>/status/", views.update_submission_status, name="dashboard-status"),
    path("<slug:section>/<int:pk>/follow-up/", views.submission_follow_up, name="dashboard-follow-up"),
]
