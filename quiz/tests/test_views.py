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
        session[f"quiz_run_{self.question_set.id}"] = {
            "ids": [self.question.id],
            "results": [],
        }
        session.save()
        self.answer_url = reverse("quiz:answer", args=[self.question_set.id, 1])
        self.feedback_url = reverse("quiz:feedback", args=[self.question_set.id, 1])

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
        run = self.client.session[f"quiz_run_{self.question_set.id}"]
        self.assertEqual(len(run["results"]), 1)
