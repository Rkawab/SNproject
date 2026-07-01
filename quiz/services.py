import random
import re

from django.db.models import Count, OuterRef, Q, Subquery

from .models import Question, AnswerLog

# ---- 選択肢ランダム化（表示時シャッフル＋記号振り直し） --------------------
# 仕様: .claude/OVERVIEW.md「選択肢のランダム化」参照。
# choices/answer/explanation_html は元記号（A〜D）のまま保存し、表示時にのみ
# 並びを振り直す。解説HTML内の記号参照も表示記号へ補正して見せる。

DISPLAY_LETTERS = "ABCDEFGHIJ"
# 正答・回答として認識する選択肢記号（A〜E＝最大5択。parsing.CHOICE_LETTERS と揃える）
CHOICE_LETTERS = "ABCDE"

# レベル（出題タイプ）のラベル。QuestionSet.series（ファイル名先頭桁）と対応する。
SERIES_LABELS = {
    1: "サービス用途確認",
    2: "類似サービス比較",
    3: "シナリオ",
    4: "SAA模擬試験レベル",
    5: "外部サイト模擬試験",
    6: "読解・用語ドリル",
}


def series_label(series):
    """series（1〜5 / 0）を表示ラベルにする。未知の値は「その他」。"""
    return SERIES_LABELS.get(series, "その他")


# 分野（category）の統制リスト兼 表示順。カスタム出題のチェックボックスはこの順に並べる。
# md見出しの分野はこのいずれかに揃える（`## 第N問（Storage ｜ 細目）` 等）。
CATEGORY_ORDER = [
    "Compute",
    "Storage",
    "Database",
    "Networking / CDN / LB",
    "Security / IAM",
    "Management / Monitoring",
    "Application Integration",
    "Serverless",
    "Containers",
    "Analytics",
    "Migration / Transfer",
    "Cost Optimization",
    "Machine Learning",
    # 問題文の読み方・一般IT用語のドリル（6xx系列）専用。サービス系問題には使わない
    "読解・用語",
]

# 答え記号: <strong>X</strong> / <strong>A, C</strong>
_STRONG_LETTER_RE = re.compile(r"(<strong>)([A-Z](?:\s*[,、・/]\s*[A-Z])*)(</strong>)")
# 理由マーカー: 行頭 '- X：' またはHTMLリスト化後の '<li>X：'。
# グループ '- A・B・D：' '- A/C：' '- A, C：'（区切りは ・ or / or ,、
# 後ろは全角/半角コロン）。グループ内の各記号を個別に置換し、区切り文字は保持する。
_REASON_MARK_RE = re.compile(r"(?:(?<=- )|(?<=<li>))([A-Z](?:\s*[,、・/]\s*[A-Z])*)(?=[：:])")
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


def answer_letters(value):
    """`B` / `A,C` / ["A", "C"] を正答セットとして扱う。"""
    if not value:
        return set()
    if isinstance(value, str):
        return {letter for letter in _SINGLE_LETTER_RE.findall(value.upper()) if letter in CHOICE_LETTERS}
    return {str(letter).upper() for letter in value if str(letter).upper() in CHOICE_LETTERS}


def normalize_answer(value):
    """保存用に `A,C` のようなカンマ区切りへ正規化する。"""
    return ",".join(sorted(answer_letters(value)))


def format_answer(value, orig_to_disp=None):
    """表示用に `A, C` のような読みやすい記号列へ変換する。"""
    letters = sorted(answer_letters(value))
    if orig_to_disp:
        letters = sorted(orig_to_disp.get(letter, letter) for letter in letters)
    return ", ".join(letters)


def is_correct_answer(chosen, answer):
    return answer_letters(chosen) == answer_letters(answer)


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
        return m.group(1) + format_answer(m.group(2), orig_to_disp) + m.group(3)

    def _mark(m):
        # 区切り文字（・ or / or , or 、）を保ったまま各記号だけ置換する
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


def question_answer_stats(subject):
    """各問題の 正解数 / 不正解数 / 直近の○× を注釈した Question クエリセット（回答ありのみ）。

    専用の集計テーブルは持たず、AnswerLog（全履歴）を集計して算出する。
    成績ページの「問題ごとの成績」表示に使う。
    """
    latest = AnswerLog.objects.filter(question=OuterRef("pk")).order_by("-answered_at")
    return (
        Question.objects.filter(question_set__subject=subject)
        .select_related("question_set")
        .annotate(
            correct_count=Count("answer_logs", filter=Q(answer_logs__is_correct=True)),
            wrong_count=Count("answer_logs", filter=Q(answer_logs__is_correct=False)),
            answered_count=Count("answer_logs"),
            last_correct=Subquery(latest.values("is_correct")[:1]),
            last_answered_at=Subquery(latest.values("answered_at")[:1]),
        )
        .filter(answered_count__gt=0)
    )
