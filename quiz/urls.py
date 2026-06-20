from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.top, name="top"),
    path("stats/", views.stats, name="stats"),
    # カスタム出題（条件で絞り込んだ問題を横断出題）
    path("start/", views.start, name="start"),
    path("q/<int:n>/", views.question, name="question"),
    path("q/<int:n>/answer/", views.answer, name="answer"),
    path("q/<int:n>/feedback/", views.feedback, name="feedback"),
    path("result/", views.result, name="result"),
    # 復習モード（最新回答が×の問題を横断出題）
    path("review/start/", views.start, {"mode": "review"}, name="review_start"),
    path("review/q/<int:n>/", views.question, {"mode": "review"}, name="review_question"),
    path("review/q/<int:n>/answer/", views.answer, {"mode": "review"}, name="review_answer"),
    path("review/q/<int:n>/feedback/", views.feedback, {"mode": "review"}, name="review_feedback"),
    path("review/result/", views.result, {"mode": "review"}, name="review_result"),
]
