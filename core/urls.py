from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("request/new/", views.request_new, name="request_new"),
    path("requests/", views.my_requests, name="my_requests"),
    path("helper/", views.helper, name="helper"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("collector/", views.collector_dashboard, name="collector"),
    path("collector/<int:pk>/status/", views.update_status, name="update_status"),
]
