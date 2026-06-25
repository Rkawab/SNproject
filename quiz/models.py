from django.db import models

from notes.models import Subject


class QuestionSet(models.Model):
    """問題セット（mdファイル1つ＝1レコード）"""

    TYPE_EXAM = "exam"
    TYPE_CHOICES = [
        (TYPE_EXAM, "4択問題"),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="question_sets")
    set_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=300)
    # 元mdファイル名（拡張子なし）
    source_filename = models.CharField(max_length=300, unique=True)
    order = models.IntegerField(default=999)
    # レベル（出題タイプ）。ファイル名先頭桁から自動設定: 1=用途確認/2=比較/3=シナリオ/4=模試/5=外部サイト模擬試験。判定不能は0
    series = models.IntegerField(default=0)
    imported_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "source_filename"]

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    """4択問題"""

    question_set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, related_name="questions")
    number = models.IntegerField()
    # 分野（統制リスト＝ノート16分野フォルダ表示名）。`## 第N問（分野 / 細目）` の分野部分。未指定は空
    category = models.CharField(max_length=200, blank=True)
    # 細目（旧ジャンル）。`## 第N問（分野 / 細目）` の細目部分、または1語見出しの全体
    genre = models.CharField(max_length=200, blank=True)
    question_html = models.TextField()
    # {"A": "...", "B": "..."}
    choices = models.JSONField(null=True, blank=True)
    # 正解の記号（"B"）
    answer = models.CharField(max_length=300)
    explanation_html = models.TextField(blank=True)

    class Meta:
        ordering = ["question_set", "number"]
        unique_together = [("question_set", "number")]

    def __str__(self):
        return f"{self.question_set.source_filename} Q{self.number}"

class AnswerLog(models.Model):
    """回答履歴（シングルユーザーのため user は持たない）"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_logs")
    is_correct = models.BooleanField()
    # 選んだ記号
    chosen = models.CharField(max_length=10, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]
