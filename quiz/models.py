from django.db import models

from notes.models import Subject


class QuestionSet(models.Model):
    """問題セット（mdファイル1つ＝1レコード）"""

    TYPE_BASIC = "basic"
    TYPE_EXAM = "exam"
    TYPE_CHOICES = [
        (TYPE_BASIC, "一問一答"),
        (TYPE_EXAM, "模擬試験"),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="question_sets")
    set_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=300)
    # 元mdファイル名（拡張子なし）
    source_filename = models.CharField(max_length=300, unique=True)
    order = models.IntegerField(default=999)
    imported_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "source_filename"]

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    """問題（一問一答・模擬試験 共通）"""

    question_set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, related_name="questions")
    number = models.IntegerField()
    genre = models.CharField(max_length=200, blank=True)
    question_html = models.TextField()
    # 模擬試験のみ {"A": "...", "B": "..."}。一問一答は null
    choices = models.JSONField(null=True, blank=True)
    # 模擬試験=正解の記号（"B"）/ 一問一答=答えのテキスト
    answer = models.CharField(max_length=300)
    explanation_html = models.TextField(blank=True)

    class Meta:
        ordering = ["question_set", "number"]
        unique_together = [("question_set", "number")]

    def __str__(self):
        return f"{self.question_set.source_filename} Q{self.number}"

    @property
    def is_exam(self):
        return self.choices is not None


class AnswerLog(models.Model):
    """回答履歴（シングルユーザーのため user は持たない）"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_logs")
    is_correct = models.BooleanField()
    # 模擬試験で選んだ記号（一問一答は null）
    chosen = models.CharField(max_length=10, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]
