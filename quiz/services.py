from django.db.models import OuterRef, Subquery

from .models import Question, AnswerLog


def wrong_question_ids(subject):
    """最新の回答が不正解の問題ID一覧（復習モード用）"""
    latest = AnswerLog.objects.filter(question=OuterRef("pk")).order_by("-answered_at")
    return list(
        Question.objects.filter(question_set__subject=subject)
        .annotate(last_correct=Subquery(latest.values("is_correct")[:1]))
        .filter(last_correct=False)
        .order_by("question_set__order", "number")
        .values_list("id", flat=True)
    )
