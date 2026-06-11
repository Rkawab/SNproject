import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import Subject, Note
from quiz.models import QuestionSet
from quiz.services import wrong_question_ids


def get_current_subject(request):
    """選択中の科目を返す（?subject=<id> で切替、セッション保持）"""
    subjects = list(Subject.objects.all())
    if not subjects:
        return None, []
    sid = request.GET.get("subject")
    if sid and sid.isdigit() and any(s.id == int(sid) for s in subjects):
        request.session["subject_id"] = int(sid)
    selected = request.session.get("subject_id")
    subject = next((s for s in subjects if s.id == selected), subjects[0])
    return subject, subjects


@login_required
def home(request):
    subject, subjects = get_current_subject(request)
    context = {"subject": subject, "subjects": subjects}
    if subject:
        context.update({
            "note_count": subject.notes.count(),
            "basic_sets": QuestionSet.objects.filter(subject=subject, set_type=QuestionSet.TYPE_BASIC).count(),
            "exam_sets": QuestionSet.objects.filter(subject=subject, set_type=QuestionSet.TYPE_EXAM).count(),
            "review_count": len(wrong_question_ids(subject)),
        })
    return render(request, "home.html", context)


@login_required
def note_list(request):
    subject, subjects = get_current_subject(request)
    folders = subject.folders.prefetch_related("notes") if subject else []
    return render(request, "notes/list.html", {
        "subject": subject, "subjects": subjects, "folders": folders,
    })


def _make_excerpt(text, query, width=60):
    """ヒット箇所の前後を抜粋し、クエリを <mark> で強調したHTMLを返す"""
    low = text.casefold()
    idx = low.find(query.casefold())
    if idx < 0:
        snippet = text[: width * 2]
    else:
        start = max(0, idx - width)
        snippet = ("…" if start > 0 else "") + text[start: idx + len(query) + width] + "…"
    escaped = escape(snippet)
    pattern = re.compile(re.escape(escape(query)), re.IGNORECASE)
    return mark_safe(pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped))


@login_required
def search(request):
    subject, subjects = get_current_subject(request)
    query = request.GET.get("q", "").strip()
    results = []
    if subject and query:
        ql = query.casefold()
        # 個人利用・百件規模のため全件をPython側で絞り込む（タグも対象にできる）
        for note in Note.objects.filter(subject=subject).select_related("folder"):
            haystack = f"{note.title}\n{note.body_md}\n{' '.join(note.tags)}"
            if ql in haystack.casefold():
                results.append({
                    "note": note,
                    "excerpt": _make_excerpt(note.body_md, query),
                })
    return render(request, "notes/search.html", {
        "subject": subject, "subjects": subjects, "query": query, "results": results,
    })


@login_required
def detail(request, pk):
    note = get_object_or_404(Note.objects.select_related("folder", "subject"), pk=pk)
    return render(request, "notes/detail.html", {"note": note})
