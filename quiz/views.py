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
from .models import Question, QuestionSet, AnswerLog
from .services import (
    answer_letters,
    format_answer,
    is_correct_answer,
    normalize_answer,
    wrong_question_ids,
    question_answer_stats,
    shuffle_order,
    build_display,
    remap_letters,
    series_label,
    CATEGORY_ORDER,
)


# ---- セッション内の演習状態（run）管理 ----------------------------------
# run = {"ids": [問題ID...], "results": [{"qid", "correct", "chosen"}...]}
# モード（"custom"=カスタム出題 / "review"=×復習）ごとに run を分ける。
# 旧「セット単位の出題」は廃止し、常に絞り込んだID配列を run に流す方式に統一した。

# 分野チェックボックスで「未分類（category 空）」を表す値
NONE_CATEGORY = "__none__"


def _run_key(mode):
    return f"quiz_run_{mode}"


def _get_run(request, mode):
    return request.session.get(_run_key(mode))


def _save_run(request, mode, run):
    request.session[_run_key(mode)] = run
    request.session.modified = True


def _question_order(run, q):
    """この問題の選択肢シャッフル順（表示順に並んだ元記号リスト）を run から取得。
    未生成なら生成して run に保存する（保存はキー追加のみ。呼び出し側で _save_run する）。
    """
    orders = run.setdefault("orders", {})
    key = str(q.id)
    keys = list((q.choices or {}).keys())
    saved = orders.get(key)
    if not saved or sorted(saved) != sorted(keys):
        saved = shuffle_order(keys)
        orders[key] = saved
    return saved


def _url(mode, name, n=None):
    """カスタム出題（mode="custom"）と復習モード（mode="review"）で対応するURLを返す"""
    prefix = "review_" if mode == "review" else ""
    args = [] if n is None else [n]
    return reverse(f"quiz:{prefix}{name}", args=args)


# ---- 画面 ----------------------------------------------------------------

@login_required
def top(request):
    """演習トップ＝カスタム出題ビルダー。レベル→番号の入れ子と分野ごとの件数を出して選ばせる。"""
    subject, subjects = get_current_subject(request)
    level_groups, categories, review_count, total = [], [], 0, 0
    if subject:
        base = Question.objects.filter(question_set__subject=subject)

        # 分野別の件数（CATEGORY_ORDER の順に並べ、未知の分野→その後、未分類→末尾）
        order_index = {name: i for i, name in enumerate(CATEGORY_ORDER)}
        cats = []
        for row in base.values("category").annotate(n=Count("id")):
            name = row["category"] or ""
            cats.append({
                "value": name or NONE_CATEGORY,
                "label": name or "未分類",
                "count": row["n"],
                "order": order_index.get(name, 9998) if name else 9999,
            })
        categories = sorted(cats, key=lambda c: (c["order"], c["label"]))

        # レベル（出題タイプ）→ 番号（ファイル＝QuestionSet）の入れ子。
        # レベルのチェックは配下の番号を一括トグルする「親」、番号は個別の「子」。
        # 親=level / 子=set を別々にPOSTし、start で series と question_set_id を
        # それぞれAND条件にする（古い番号だけ外す／特定レベルだけ解く を1UIで両立）。
        group_map = {}
        for s in (
            QuestionSet.objects.filter(subject=subject)
            .annotate(n=Count("questions"))
            .filter(n__gt=0)
            .order_by("order", "source_filename")
        ):
            g = group_map.setdefault(
                s.series,
                {"series": s.series, "label": series_label(s.series), "count": 0, "sets": []},
            )
            g["sets"].append({"value": s.id, "label": s.source_filename, "count": s.n})
            g["count"] += s.n
        level_groups = [group_map[k] for k in sorted(group_map)]

        total = sum(g["count"] for g in level_groups)
        review_count = len(wrong_question_ids(subject))

    return render(request, "quiz/top.html", {
        "subject": subject, "subjects": subjects,
        "level_groups": level_groups, "categories": categories,
        "total_count": total, "review_count": review_count,
        "count_choices": [10, 20, 30],
    })


@login_required
def start(request, mode="custom"):
    # 復習モード: 最新回答が×の問題を横断出題（オプションなしで即開始）
    if mode == "review":
        subject, _ = get_current_subject(request)
        ids = wrong_question_ids(subject) if subject else []
        if not ids:
            messages.info(request, "復習対象（最新回答が×の問題）はありません。")
            return redirect("quiz:top")
        _save_run(request, "review", {"ids": ids, "results": []})
        return redirect(_url("review", "question", 1))

    # カスタム出題: トップのビルダーからのPOSTのみ受け付ける
    if request.method != "POST":
        return redirect("quiz:top")
    subject, _ = get_current_subject(request)
    if not subject:
        return redirect("quiz:top")

    qs = Question.objects.filter(question_set__subject=subject)

    levels = [int(x) for x in request.POST.getlist("level") if x.isdigit()]
    if levels:  # 未選択は「すべてのレベル」
        qs = qs.filter(question_set__series__in=levels)

    cats = request.POST.getlist("category")
    if cats:  # 未選択は「すべての分野」
        cond = Q()
        real = [c for c in cats if c != NONE_CATEGORY]
        if real:
            cond |= Q(category__in=real)
        if NONE_CATEGORY in cats:
            cond |= Q(category="")
        qs = qs.filter(cond)

    set_ids = [int(x) for x in request.POST.getlist("set") if x.isdigit()]
    if set_ids:  # 未選択は「すべての番号（ファイル）」
        qs = qs.filter(question_set_id__in=set_ids)

    # 直近で不正解の問題だけ（復習条件を絞り込みに統合）
    if request.POST.get("only_wrong"):
        qs = qs.filter(id__in=wrong_question_ids(subject))

    # 通算でN回以上正解した問題を除外（覚えた問題を rotation から外す）
    exclude_n = request.POST.get("exclude_correct", "")
    if exclude_n.isdigit() and int(exclude_n) > 0:
        qs = qs.annotate(
            _correct_count=Count("answer_logs", filter=Q(answer_logs__is_correct=True))
        ).filter(_correct_count__lt=int(exclude_n))

    ids = list(qs.order_by("question_set__order", "number").values_list("id", flat=True))
    if request.POST.get("order", "random") == "random":
        random.shuffle(ids)

    count = request.POST.get("count", "20")
    if count != "all" and count.isdigit():
        ids = ids[: int(count)]

    if not ids:
        messages.warning(request, "条件に合う問題がありません。レベルや分野の選択を見直してください。")
        return redirect("quiz:top")

    _save_run(request, "custom", {"ids": ids, "results": []})
    return redirect(_url("custom", "question", 1))


@login_required
def question(request, n, mode="custom"):
    run = _get_run(request, mode)
    if not run:
        return redirect("quiz:top")

    total = len(run["ids"])
    answered = len(run["results"])
    if answered >= total:
        return redirect(_url(mode, "result"))
    if n != answered + 1:
        # 進行中の問題以外へのアクセスは現在位置へ戻す
        return redirect(_url(mode, "question", answered + 1))

    q = get_object_or_404(Question, pk=run["ids"][n - 1])
    order = _question_order(run, q)
    _save_run(request, mode, run)  # この問題の表示順を確定・保存
    choices, _ = build_display(q.choices, order)
    return render(request, "quiz/question.html", {
        "q": q, "n": n, "total": total, "mode": mode,
        "answer_url": _url(mode, "answer", n),
        "result_url": _url(mode, "result"),
        "choices": choices,
    })


@require_POST
@login_required
def answer(request, n, mode="custom"):
    run = _get_run(request, mode)
    if not run:
        return redirect(_url(mode, "question", n))
    answered = len(run["results"])
    if n <= answered:
        # 既に回答済み（二重送信など）→ その問題の判定画面へ戻す。
        # ここで question へ飛ばすと次問題へ遷移してしまうため feedback を返す。
        return redirect(_url(mode, "feedback", n))
    if n != answered + 1:
        return redirect(_url(mode, "question", answered + 1))

    q = get_object_or_404(Question, pk=run["ids"][n - 1])

    chosen = normalize_answer(request.POST.getlist("choice"))
    valid_choices = set((q.choices or {}).keys())
    if not chosen or not answer_letters(chosen).issubset(valid_choices):
        messages.warning(request, "選択肢を選んでください。")
        return redirect(_url(mode, "question", n))
    correct = is_correct_answer(chosen, q.answer)

    AnswerLog.objects.create(question=q, is_correct=correct, chosen=chosen)
    run["results"].append({"qid": q.id, "correct": correct, "chosen": chosen})
    _save_run(request, mode, run)

    return redirect(_url(mode, "feedback", n))


@login_required
def feedback(request, n, mode="custom"):
    """4択問題の回答直後の判定・解説画面"""
    run = _get_run(request, mode)
    if not run or n > len(run["results"]):
        return redirect(_url(mode, "question", n))

    res = run["results"][n - 1]
    q = get_object_or_404(Question, pk=res["qid"])
    total = len(run["ids"])
    order = _question_order(run, q)
    _save_run(request, mode, run)
    choices, orig_to_disp = build_display(q.choices, order)
    answer_orig = sorted(answer_letters(q.answer))
    chosen_orig = sorted(answer_letters(res["chosen"]))
    return render(request, "quiz/feedback.html", {
        "q": q, "n": n, "total": total, "mode": mode,
        "choices": choices,
        "chosen": res["chosen"],                       # 元記号セット（ログ表示用）
        "answer_orig": answer_orig,                    # 元記号（ハイライト判定用）
        "chosen_orig": chosen_orig,
        "answer_disp": format_answer(q.answer, orig_to_disp),  # 表示記号
        "explanation_html": remap_letters(q.explanation_html, orig_to_disp),
        "correct": res["correct"],
        "next_url": _url(mode, "question", n + 1) if n < total else _url(mode, "result"),
        "is_last": n >= total,
    })


@login_required
def result(request, mode="custom"):
    run = _get_run(request, mode)
    if not run or not run["results"]:
        return redirect("quiz:top")

    results = run["results"]
    questions = Question.objects.in_bulk([r["qid"] for r in results])

    n_correct = sum(1 for r in results if r["correct"])
    total = len(results)
    ratio = n_correct / total if total else 0

    # 分野別内訳（category 優先、無ければ細目→未分類）
    orders = run.get("orders", {})
    cat_stats = {}
    wrong = []
    for r in results:
        q = questions.get(r["qid"])
        if not q:
            continue
        key = q.category or q.genre or "（未分類）"
        c = cat_stats.setdefault(key, {"total": 0, "correct": 0})
        c["total"] += 1
        c["correct"] += int(r["correct"])
        if not r["correct"]:
            # 演習中に見たシャッフル順と同じ記号で復習表示する
            order = orders.get(str(q.id)) or list((q.choices or {}).keys())
            _, orig_to_disp = build_display(q.choices, order)
            wrong.append({
                "q": q,
                "answer_disp": format_answer(q.answer, orig_to_disp),
                "chosen_disp": format_answer(r["chosen"], orig_to_disp),
                "explanation_html": remap_letters(q.explanation_html, orig_to_disp),
            })

    subject = get_current_subject(request)[0]
    pass_ratio = subject.pass_ratio if subject else 0.8
    return render(request, "quiz/result.html", {
        "mode": mode,
        "n_correct": n_correct, "total": total,
        "percent": round(ratio * 100),
        "show_pass_line": mode != "review",
        "passed": ratio >= pass_ratio,
        "pass_percent": round(pass_ratio * 100),
        "cat_stats": cat_stats, "wrong": wrong,
    })


@login_required
def stats(request):
    subject, subjects = get_current_subject(request)
    logs = AnswerLog.objects.filter(question__question_set__subject=subject) if subject else AnswerLog.objects.none()

    total = logs.count()
    n_correct = logs.filter(is_correct=True).count()

    cat_rows = (
        logs.values("question__category")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
        .order_by("question__category")
    )
    cat_stats = sorted(
        [
            {
                "category": row["question__category"] or "未分類",
                "total": row["total"],
                "correct": row["correct"],
                "percent": round(row["correct"] / row["total"] * 100) if row["total"] else 0,
            }
            for row in cat_rows
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

    # 問題ごとの成績（正解数○・不正解数×・直近○×、×が多い順）
    q_stats = (
        question_answer_stats(subject).order_by("-wrong_count", "-last_answered_at")
        if subject else []
    )

    return render(request, "quiz/stats.html", {
        "subject": subject, "subjects": subjects,
        "total": total, "n_correct": n_correct,
        "percent": round(n_correct / total * 100) if total else 0,
        "cat_stats": cat_stats, "daily": daily, "q_stats": q_stats,
    })


@require_POST
@login_required
def reset_stats(request):
    """現在の科目の回答履歴(AnswerLog)を全削除して成績をリセットする。"""
    subject, _ = get_current_subject(request)
    if subject:
        AnswerLog.objects.filter(question__question_set__subject=subject).delete()
        messages.success(request, f"{subject.name} の回答履歴（正解数・不正解数）をリセットしました。")
    return redirect("quiz:stats")
