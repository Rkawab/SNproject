"""選択肢ランダム化（表示時シャッフル＋記号振り直し＋解説remap）のテスト"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Subject
from quiz.models import Question, QuestionSet
from quiz.services import build_display, remap_letters


class BuildDisplayTests(TestCase):
    def test_assigns_sequential_display_letters_in_order(self):
        choices = {"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"}
        # 表示順 = 元記号 C,A,B,D
        items, orig_to_disp = build_display(choices, ["C", "A", "B", "D"])

        self.assertEqual([i["letter"] for i in items], ["A", "B", "C", "D"])
        self.assertEqual([i["orig"] for i in items], ["C", "A", "B", "D"])
        self.assertEqual([i["text"] for i in items], ["Gamma", "Alpha", "Beta", "Delta"])
        # 元記号→表示記号の対応
        self.assertEqual(orig_to_disp, {"C": "A", "A": "B", "B": "C", "D": "D"})


class RemapLettersTests(TestCase):
    def setUp(self):
        # 元記号 C,A,B,D を A,B,C,D に振り直したときの対応
        self.orig_to_disp = {"C": "A", "A": "B", "B": "C", "D": "D"}

    def test_remaps_answer_strong_letter(self):
        html = "<p>答え：<strong>B</strong>（EFS）</p>"
        self.assertEqual(remap_letters(html, self.orig_to_disp),
                         "<p>答え：<strong>C</strong>（EFS）</p>")

    def test_remaps_answer_strong_letter_group(self):
        html = "<p>答え：<strong>A, C</strong></p>"
        self.assertEqual(remap_letters(html, self.orig_to_disp),
                         "<p>答え：<strong>A, B</strong></p>")

    def test_remaps_reason_bullet_markers_including_group(self):
        html = ("<p>答え：<strong>B</strong>（EFS）<br />\n"
                "- A：理由A<br />\n- C：理由C<br />\n- D：理由D</p>")
        out = remap_letters(html, self.orig_to_disp)
        # A→B, C→A, D→D, 答え B→C
        self.assertIn("<strong>C</strong>", out)
        self.assertIn("- B：理由A", out)
        self.assertIn("- A：理由C", out)
        self.assertIn("- D：理由D", out)

    def test_remaps_grouped_reason(self):
        html = "<p>- A・B・D：いずれもRDB</p>"
        # A→B, B→C, D→D
        self.assertEqual(remap_letters(html, self.orig_to_disp),
                         "<p>- B・C・D：いずれもRDB</p>")

    def test_remaps_html_list_reason_marker(self):
        html = "<ul><li>A, C：正解</li><li>D：不正解</li></ul>"
        out = remap_letters(html, self.orig_to_disp)
        self.assertIn("<li>B, A：正解</li>", out)
        self.assertIn("<li>D：不正解</li>", out)

    def test_remaps_slash_grouped_reason_preserving_separator(self):
        # 区切りが半角スラッシュのグループ（- A/C：）も区切りを保って置換
        html = "<p>- A/C：SQSは消える<br />\n- C/D：SG/NACL</p>"
        out = remap_letters(html, self.orig_to_disp)
        self.assertIn("- B/A：SQSは消える", out)  # A→B, C→A
        self.assertIn("- A/D：SG/NACL", out)       # C→A, D→D（後段 SG/NACL は - 始まりでないため不変）

    def test_does_not_touch_multichar_bold_labels(self):
        html = "<p><strong>覚えるべきキーワード</strong>：EFS</p>"
        self.assertEqual(remap_letters(html, self.orig_to_disp), html)


class FeedbackDisplayTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="t", password="p")
        self.client.force_login(user)
        subject = Subject.objects.create(slug="aws", name="AWS")
        self.qset = QuestionSet.objects.create(
            subject=subject, set_type=QuestionSet.TYPE_EXAM,
            title="set", source_filename="set",
        )
        self.q = Question.objects.create(
            question_set=self.qset, number=1,
            question_html="<p>Q</p>",
            choices={"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
            answer="B",
            explanation_html=("<p>答え：<strong>B</strong>（Beta）<br />\n"
                              "- A：だめA<br />\n- C：だめC<br />\n- D：だめD</p>"),
        )
        # 表示順を固定（元C,A,B,D → 表示A,B,C,D）して乱数依存をなくす
        session = self.client.session
        session[f"quiz_run_{self.qset.id}"] = {
            "ids": [self.q.id],
            "results": [{"qid": self.q.id, "correct": False, "chosen": "A"}],
            "orders": {str(self.q.id): ["C", "A", "B", "D"]},
        }
        session.save()

    def test_feedback_shows_remapped_answer_and_explanation(self):
        url = reverse("quiz:feedback", args=[self.qset.id, 1])
        html = self.client.get(url).content.decode()

        # 正解の元記号 B は表示記号 C に振り直されている
        self.assertIn("正解は C", html)
        # 解説の記号参照も表示記号へ補正
        self.assertIn("答え：<strong>C</strong>", html)
        self.assertIn("- B：だめA", html)   # 元A→表示B
        self.assertIn("- A：だめC", html)   # 元C→表示A
        self.assertIn("- D：だめD", html)   # 元D→D


class QuestionDisplayTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="t", password="p")
        self.client.force_login(user)
        subject = Subject.objects.create(slug="aws", name="AWS")
        self.qset = QuestionSet.objects.create(
            subject=subject, set_type=QuestionSet.TYPE_EXAM,
            title="set", source_filename="set",
        )
        self.q = Question.objects.create(
            question_set=self.qset, number=1, question_html="<p>Q</p>",
            choices={"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"}, answer="B",
        )
        session = self.client.session
        session[f"quiz_run_{self.qset.id}"] = {
            "ids": [self.q.id], "results": [],
            "orders": {str(self.q.id): ["C", "A", "B", "D"]},
        }
        session.save()

    def test_choices_rendered_with_orig_letter_submitted(self):
        url = reverse("quiz:question", args=[self.qset.id, 1])
        html = self.client.get(url).content.decode()

        # 全選択肢が表示される
        for text in ("Alpha", "Beta", "Gamma", "Delta"):
            self.assertIn(text, html)
        # 採点は元記号で行うため value には元記号が入る
        for orig in ("A", "B", "C", "D"):
            self.assertIn(f'value="{orig}"', html)
