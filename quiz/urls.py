from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.top, name="top"),
    path("stats/", views.stats, name="stats"),
    path("set/<int:set_id>/start/", views.start, name="start"),
    path("set/<int:set_id>/q/<int:n>/", views.question, name="question"),
    path("set/<int:set_id>/q/<int:n>/answer/", views.answer, name="answer"),
    path("set/<int:set_id>/q/<int:n>/feedback/", views.feedback, name="feedback"),
    path("set/<int:set_id>/result/", views.result, name="result"),
    # 復習モード（最新回答が×の問題を横断出題）
    path("review/start/", views.start, {"set_id": None}, name="review_start"),
    path("review/q/<int:n>/", views.question, {"set_id": None}, name="review_question"),
    path("review/q/<int:n>/answer/", views.answer, {"set_id": None}, name="review_answer"),
    path("review/q/<int:n>/feedback/", views.feedback, {"set_id": None}, name="review_feedback"),
    path("review/result/", views.result, {"set_id": None}, name="review_result"),
]
