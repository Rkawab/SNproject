from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("search/", views.search, name="search"),
    path("<int:pk>/", views.detail, name="detail"),
]
