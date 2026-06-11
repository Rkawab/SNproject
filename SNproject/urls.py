from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from notes import views as notes_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", notes_views.home, name="home"),
    path("notes/", include("notes.urls")),
    path("quiz/", include("quiz.urls")),
]
