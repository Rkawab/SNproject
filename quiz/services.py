import random
import re

from django.db.models import OuterRef, Subquery

from .models import Question, AnswerLog

# ---- 選択肢ランダム化（表示時シャッフル＋記号振り直し） --------------------
# 仕様: .claude/OVERVIEW.md「選択肢のランダム化」参照。
# choices/answer/explanation_html は元記号（A〜D）のまま保存し、表示時にのみ
# 並びを振り直す。解説HTML内の記号参照も表示記号へ補正して見せる。

DISPLAY_LETTERS = "ABCDEFGHIJ"

# 答え記号: <strong>X</strong>（単独大文字boldは答え記号のみ＝誤爆しない）
_STRONG_LETTER_RE = re.compile(r"(<strong>)([A-Z])(</strong>)")
# 不正解理由マーカー: 行頭 '- X：' / グループ '- A・B・D：' '- A/C：'（区切りは ・ or /、
# 後ろは全角/半角コロン）。グループ内の各記号を個別に置換し、区切り文字は保持する。
_REASON_MARK_RE = re.compile(r"(?<=- )([A-Z](?:[・/][A-Z])*)(?=[：:])")
_SINGLE_LETTER_RE = re.compile(r"[A-Z]")


def shuffle_order(choice_keys):
    """選択肢キー（元記号）を並び替えた「表示順に並んだ元記号リスト」を返す"""
    keys = list(choice_keys)
    random.shuffle(keys)
    return keys


def build_display(choices, order):
    """order（表示順の元記号リスト）から表示用データと記号対応表を作る。

    戻り値:
      items: [{"letter": 表示記号, "orig": 元記号, "text": 選択肢文}, ...]
      orig_to_disp: {元記号: 表示記号}
    """
    items, orig_to_disp = [], {}
    for i, orig in enumerate(order):
        disp = DISPLAY_LETTERS[i] if i < len(DISPLAY_LETTERS) else orig
        orig_to_disp[orig] = disp
        items.append({"letter": disp, "orig": orig, "text": (choices or {}).get(orig, "")})
    return items, orig_to_disp


def remap_letters(html, orig_to_disp):
    """解説HTML内の選択肢記号参照を表示記号へ置換する。

    対象は2形式のみ（OVERVIEW.md「選択肢ランダム化の前提」参照）:
      - 答え記号  <strong>X</strong>
      - 不正解理由 行頭 '- X：' / グループ '- A・B・D：'
    orig_to_disp に無い記号は変更しない。re.sub は置換後テキストを再走査しない
    ため、A↔C のような相互入替でも一度の置換で安全に処理できる。
    """
    if not html or not orig_to_disp:
        return html

    def _strong(m):
        return m.group(1) + orig_to_disp.get(m.group(2), m.group(2)) + m.group(3)

    def _mark(m):
        # 区切り文字（・ or /）を保ったまま各記号だけ置換する
        return _SINGLE_LETTER_RE.sub(lambda mm: orig_to_disp.get(mm.group(0), mm.group(0)), m.group(1))

    html = _STRONG_LETTER_RE.sub(_strong, html)
    html = _REASON_MARK_RE.sub(_mark, html)
    return html


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
