from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("request/new/", views.request_new, name="request_new"),
    path("requests/", views.my_requests, name="my_requests"),
    path("helper/", views.helper, name="helper"),

    # USER auth (separate)
    path("user/register/", views.user_register_view, name="user_register"),
    path("user/login/", views.user_login_view, name="user_login"),
    path("user/logout/", views.user_logout_view, name="user_logout"),

    # COLLECTOR auth (separate)
    path("collector/login/", views.collector_login_view, name="collector_login"),
    path("collector/logout/", views.collector_logout_view, name="collector_logout"),

    # Collector dashboard
    path("collector/", views.collector_dashboard, name="collector"),
    path("collector/<int:pk>/status/", views.update_status, name="update_status"),

    # Chatbot
    path("chatbot/", views.chatbot, name="chatbot"),
    path("api/chatbot/message/", views.chatbot_message, name="chatbot_message"),
]
