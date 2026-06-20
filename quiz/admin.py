from django.contrib import admin

from .models import QuestionSet, Question, AnswerLog


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "set_type", "series", "order", "imported_at")
    list_filter = ("subject", "set_type", "series")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_set", "number", "category", "genre", "answer")
    list_filter = ("question_set", "category")


@admin.register(AnswerLog)
class AnswerLogAdmin(admin.ModelAdmin):
    list_display = ("question", "is_correct", "chosen", "answered_at")
    list_filter = ("is_correct",)
