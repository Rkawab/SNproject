from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Subject
from quiz.models import AnswerLog, Question, QuestionSet


class QuizAnswerTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="tester", password="password")
        self.client.force_login(user)
        subject = Subject.objects.create(slug="aws", name="AWS")
        self.question_set = QuestionSet.objects.create(
            subject=subject,
            set_type=QuestionSet.TYPE_EXAM,
            title="Test set",
            source_filename="test-set",
        )
        self.question = Question.objects.create(
            question_set=self.question_set,
            number=1,
            question_html="<p>Question</p>",
            choices={"A": "Alpha", "B": "Beta"},
            answer="A",
        )
        session = self.client.session
        session["quiz_run_custom"] = {
            "ids": [self.question.id],
            "results": [],
        }
        session.save()
        self.answer_url = reverse("quiz:answer", args=[1])
        self.feedback_url = reverse("quiz:feedback", args=[1])

    def test_answer_redirects_to_feedback_and_records_once(self):
        response = self.client.post(self.answer_url, {"choice": "A"})

        self.assertRedirects(response, self.feedback_url, fetch_redirect_response=False)
        self.assertEqual(AnswerLog.objects.count(), 1)
        log = AnswerLog.objects.get()
        self.assertTrue(log.is_correct)
        self.assertEqual(log.chosen, "A")

    def test_multiple_answers_require_exact_set(self):
        self.question.choices = {"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"}
        self.question.answer = "A,B"
        self.question.save(update_fields=["choices", "answer"])

        response = self.client.post(self.answer_url, {"choice": ["B", "A"]})

        self.assertRedirects(response, self.feedback_url, fetch_redirect_response=False)
        log = AnswerLog.objects.get()
        self.assertTrue(log.is_correct)
        self.assertEqual(log.chosen, "A,B")

    def test_multiple_answers_are_wrong_when_incomplete(self):
        self.question.answer = "A,B"
        self.question.save(update_fields=["answer"])

        self.client.post(self.answer_url, {"choice": "A"})

        log = AnswerLog.objects.get()
        self.assertFalse(log.is_correct)

    def test_duplicate_answer_returns_to_same_feedback_without_new_log(self):
        self.client.post(self.answer_url, {"choice": "A"})

        response = self.client.post(self.answer_url, {"choice": "A"})

        self.assertRedirects(response, self.feedback_url, fetch_redirect_response=False)
        self.assertEqual(AnswerLog.objects.count(), 1)
        run = self.client.session["quiz_run_custom"]
        self.assertEqual(len(run["results"]), 1)


class QuizCustomStartTests(TestCase):
    """カスタム出題：レベル・分野・問題数の絞り込みで run（ID配列）を作る。"""

    def setUp(self):
        user = get_user_model().objects.create_user(username="c", password="password")
        self.client.force_login(user)
        self.subject = Subject.objects.create(slug="aws", name="AWS")
        self.set1 = QuestionSet.objects.create(
            subject=self.subject, set_type=QuestionSet.TYPE_EXAM,
            title="用途", source_filename="101_x", order=101, series=1,
        )
        self.set3 = QuestionSet.objects.create(
            subject=self.subject, set_type=QuestionSet.TYPE_EXAM,
            title="シナリオ", source_filename="301_x", order=301, series=3,
        )
        self.q_s3 = Question.objects.create(
            question_set=self.set1, number=1, category="S3",
            question_html="<p>q</p>", choices={"A": "a", "B": "b"}, answer="A",
        )
        self.q_net = Question.objects.create(
            question_set=self.set1, number=2, category="ネットワーク",
            question_html="<p>q</p>", choices={"A": "a", "B": "b"}, answer="A",
        )
        self.q_scn = Question.objects.create(
            question_set=self.set3, number=1, category="データベース",
            question_html="<p>q</p>", choices={"A": "a", "B": "b"}, answer="A",
        )

    def test_filters_by_level_and_category(self):
        resp = self.client.post(reverse("quiz:start"), {
            "level": ["1"], "category": ["S3"], "count": "all", "order": "normal",
        })
        self.assertRedirects(resp, reverse("quiz:question", args=[1]), fetch_redirect_response=False)
        run = self.client.session["quiz_run_custom"]
        self.assertEqual(run["ids"], [self.q_s3.id])

    def test_limits_question_count(self):
        self.client.post(reverse("quiz:start"), {"count": "1", "order": "normal"})
        run = self.client.session["quiz_run_custom"]
        self.assertEqual(len(run["ids"]), 1)

    def test_no_match_warns_and_returns_to_top(self):
        resp = self.client.post(reverse("quiz:start"), {"level": ["2"], "count": "all"})
        self.assertRedirects(resp, reverse("quiz:top"), fetch_redirect_response=False)
        self.assertNotIn("quiz_run_custom", self.client.session)
