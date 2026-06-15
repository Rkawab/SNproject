import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notes.views import get_current_subject
from .models import QuestionSet, Question, AnswerLog
from .services import wrong_question_ids


# ---- セッション内の演習状態（run）管理 ----------------------------------
# run = {"ids": [問題ID...], "results": [{"qid", "correct", "chosen"}...]}
# キーは問題セットごと（復習モードは "review"）に分ける

def _run_key(set_id):
    return f"quiz_run_{set_id or 'review'}"


def _get_run(request, set_id):
    return request.session.get(_run_key(set_id))


def _save_run(request, set_id, run):
    request.session[_run_key(set_id)] = run
    request.session.modified = True


def _url(set_id, name, n=None):
    """セット演習と復習モードで対応するURLを返す"""
    if set_id:
        args = [set_id] if n is None else [set_id, n]
        return reverse(f"quiz:{name}", args=args)
    args = [] if n is None else [n]
    return reverse(f"quiz:review_{name}", args=args)


# ---- 画面 ----------------------------------------------------------------

@login_required
def top(request):
    subject, subjects = get_current_subject(request)
    exam_sets, review_count = [], 0
    if subject:
        # annotate(Count) を付けると Meta.ordering が SQL に反映されないため、
        # 番号順（先頭番号）を保証するよう明示的に order_by を指定する。
        exam_sets = QuestionSet.objects.filter(
            subject=subject,
            set_type=QuestionSet.TYPE_EXAM,
        ).annotate(n_questions=Count("questions")).order_by("order", "source_filename")
        review_count = len(wrong_question_ids(subject))
    return render(request, "quiz/top.html", {
        "subject": subject, "subjects": subjects,
        "exam_sets": exam_sets,
        "review_count": review_count,
    })


@login_required
def start(request, set_id):
    # 復習モード: 最新回答が×の問題を横断出題（オプションなしで即開始）
    if set_id is None:
        subject, _ = get_current_subject(request)
        ids = wrong_question_ids(subject) if subject else []
        if not ids:
            messages.info(request, "復習対象（最新回答が×の問題）はありません。")
            return redirect("quiz:top")
        _save_run(request, None, {"ids": ids, "results": []})
        return redirect(_url(None, "question", 1))

    qset = get_object_or_404(QuestionSet, pk=set_id)
    genres = list(qset.questions.order_by("number").values_list("genre", flat=True).distinct())

    if request.method == "POST":
        questions = qset.questions.order_by("number")
        genre = request.POST.get("genre", "")
        if genre:
            questions = questions.filter(genre=genre)
        ids = list(questions.values_list("id", flat=True))
        if request.POST.get("order") == "random":
            random.shuffle(ids)
        if not ids:
            messages.warning(request, "出題対象の問題がありません。")
            return redirect("quiz:start", set_id=set_id)
        _save_run(request, set_id, {"ids": ids, "results": []})
        return redirect(_url(set_id, "question", 1))

    return render(request, "quiz/start.html", {"qset": qset, "genres": genres})


@login_required
def question(request, set_id, n):
    run = _get_run(request, set_id)
    if not run:
        return redirect(_url(set_id, "start") if set_id else "quiz:top")

    total = len(run["ids"])
    answered = len(run["results"])
    if answered >= total:
        return redirect(_url(set_id, "result"))
    if n != answered + 1:
        # 進行中の問題以外へのアクセスは現在位置へ戻す
        return redirect(_url(set_id, "question", answered + 1))

    q = get_object_or_404(Question, pk=run["ids"][n - 1])
    return render(request, "quiz/question.html", {
        "q": q, "n": n, "total": total, "set_id": set_id,
        "answer_url": _url(set_id, "answer", n),
    })


@require_POST
@login_required
def answer(request, set_id, n):
    run = _get_run(request, set_id)
    if not run:
        return redirect(_url(set_id, "question", n))
    answered = len(run["results"])
    if n <= answered:
        # 既に回答済み（二重送信など）→ その問題の判定画面へ戻す。
        # ここで question へ飛ばすと次問題へ遷移してしまうため feedback を返す。
        return redirect(_url(set_id, "feedback", n))
    if n != answered + 1:
        return redirect(_url(set_id, "question", answered + 1))

    q = get_object_or_404(Question, pk=run["ids"][n - 1])

    chosen = request.POST.get("choice", "")
    if chosen not in (q.choices or {}):
        messages.warning(request, "選択肢を選んでください。")
        return redirect(_url(set_id, "question", n))
    correct = chosen == q.answer

    AnswerLog.objects.create(question=q, is_correct=correct, chosen=chosen)
    run["results"].append({"qid": q.id, "correct": correct, "chosen": chosen})
    _save_run(request, set_id, run)

    return redirect(_url(set_id, "feedback", n))


@login_required
def feedback(request, set_id, n):
    """4択問題の回答直後の判定・解説画面"""
    run = _get_run(request, set_id)
    if not run or n > len(run["results"]):
        return redirect(_url(set_id, "question", n))

    res = run["results"][n - 1]
    q = get_object_or_404(Question, pk=res["qid"])
    total = len(run["ids"])
    return render(request, "quiz/feedback.html", {
        "q": q, "n": n, "total": total, "set_id": set_id,
        "chosen": res["chosen"], "correct": res["correct"],
        "next_url": _url(set_id, "question", n + 1) if n < total else _url(set_id, "result"),
        "is_last": n >= total,
    })


@login_required
def result(request, set_id):
    run = _get_run(request, set_id)
    if not run or not run["results"]:
        return redirect("quiz:top")

    qset = get_object_or_404(QuestionSet, pk=set_id) if set_id else None
    results = run["results"]
    questions = Question.objects.in_bulk([r["qid"] for r in results])

    n_correct = sum(1 for r in results if r["correct"])
    total = len(results)
    ratio = n_correct / total if total else 0

    # ジャンル別内訳
    genre_stats = {}
    wrong = []
    for r in results:
        q = questions.get(r["qid"])
        if not q:
            continue
        g = genre_stats.setdefault(q.genre or "（未分類）", {"total": 0, "correct": 0})
        g["total"] += 1
        g["correct"] += int(r["correct"])
        if not r["correct"]:
            wrong.append({"q": q, "chosen": r["chosen"]})

    subject = qset.subject if qset else get_current_subject(request)[0]
    pass_ratio = subject.pass_ratio if subject else 0.8
    return render(request, "quiz/result.html", {
        "qset": qset, "set_id": set_id,
        "n_correct": n_correct, "total": total,
        "percent": round(ratio * 100),
        "show_pass_line": qset is not None,
        "passed": ratio >= pass_ratio,
        "pass_percent": round(pass_ratio * 100),
        "genre_stats": genre_stats, "wrong": wrong,
    })


@login_required
def stats(request):
    subject, subjects = get_current_subject(request)
    logs = AnswerLog.objects.filter(question__question_set__subject=subject) if subject else AnswerLog.objects.none()

    total = logs.count()
    n_correct = logs.filter(is_correct=True).count()

    genre_rows = (
        logs.values("question__genre")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
        .order_by("question__genre")
    )
    genre_stats = sorted(
        [
            {
                "genre": row["question__genre"] or "（未分類）",
                "total": row["total"],
                "correct": row["correct"],
                "percent": round(row["correct"] / row["total"] * 100) if row["total"] else 0,
            }
            for row in genre_rows
        ],
        key=lambda x: x["percent"],
    )

    # 直近14日の回答数
    since = timezone.localdate() - timezone.timedelta(days=13)
    daily = (
        logs.filter(answered_at__date__gte=since)
        .annotate(day=TruncDate("answered_at"))
        .values("day")
        .annotate(count=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
        .order_by("day")
    )

    # 苦手問題（×回数が多い順）
    worst = (
        Question.objects.filter(question_set__subject=subject)
        .annotate(wrong_count=Count("answer_logs", filter=Q(answer_logs__is_correct=False)))
        .filter(wrong_count__gt=0)
        .select_related("question_set")
        .order_by("-wrong_count")[:10]
    ) if subject else []

    return render(request, "quiz/stats.html", {
        "subject": subject, "subjects": subjects,
        "total": total, "n_correct": n_correct,
        "percent": round(n_correct / total * 100) if total else 0,
        "genre_stats": genre_stats, "daily": daily, "worst": worst,
    })
