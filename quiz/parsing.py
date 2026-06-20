"""`【問題】` 付き選択式問題mdのパーサ（4〜5択 / A〜E）

書式の前提（.claude/OVERVIEW.md「md書式の前提」参照）:

選択式問題（ファイル名に「【問題】」を含むmd。分類は import_content 側）:
    ## 第N問（ジャンル）
    問題文
    - A. 選択肢
    - B. 選択肢
    （SAA公式サンプルに合わせ A〜E の最大5択。複数選択問題は5択を推奨）
    > [!success]- 答え：**B**（補足）
    > [!success]- 答え：**A, C**（複数正答）
    > 解説...
"""

import re

# 認識する選択肢記号の上限（SAA本番は最大5択のため A〜E に固定）
CHOICE_LETTERS = "ABCDE"

EXAM_SECTION_RE = re.compile(r"^##\s*第(\d+)問[（(](.*?)[）)]")
CHOICE_RE = re.compile(r"^-\s*([A-E])[.．]\s*(.*)$")
ANSWER_HEAD_RE = re.compile(r"^>\s*\[!success\]-?\s*(.*)$", re.IGNORECASE)
ANSWER_TEXT_RE = re.compile(r"答え\s*[：:]\s*(.*)$")
ANSWER_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ANSWER_GROUP_RE = re.compile(r"^\s*[A-E](?:\s*[,、・/]\s*[A-E])*\s*$", re.IGNORECASE)
ANSWER_LETTER_RE = re.compile(r"[A-E]", re.IGNORECASE)


def _collect_callout_body(lines, i):
    """i行目以降の引用ブロック（> ...）を集めて (本文行リスト, 次の行番号) を返す"""
    body = []
    while i < len(lines) and lines[i].startswith(">"):
        body.append(re.sub(r"^>\s?", "", lines[i]))
        i += 1
    return body, i


def _normalize_answer_letters(letters):
    ordered = []
    for letter in letters:
        letter = letter.upper()
        if letter in CHOICE_LETTERS and letter not in ordered:
            ordered.append(letter)
    return ",".join(sorted(ordered))


def _extract_answer(text):
    """答え行の bold 記号から `B` / `A,C` を抽出する。"""
    letters = []
    for value in ANSWER_BOLD_RE.findall(text):
        if ANSWER_GROUP_RE.match(value):
            letters.extend(ANSWER_LETTER_RE.findall(value))
    return _normalize_answer_letters(letters)


def parse_exam(text):
    """4択問題mdをパースし、問題のリストを返す。

    戻り値: [{number, genre, question_md, choices, answer, explanation_md}, ...]
    """
    lines = text.split("\n")
    questions = []
    i = 0
    current = None

    def _finish(cur):
        if cur and cur["choices"]:
            cur["question_md"] = "\n".join(cur.pop("q_lines")).strip()
            questions.append(cur)

    while i < len(lines):
        line = lines[i]

        sec = EXAM_SECTION_RE.match(line)
        if sec:
            _finish(current)
            current = {
                "number": int(sec.group(1)),
                "genre": sec.group(2).strip(),
                "q_lines": [],
                "choices": {},
                "answer": "",
                "explanation_md": "",
            }
            i += 1
            continue

        if current is None:
            i += 1
            continue

        choice = CHOICE_RE.match(line)
        if choice:
            current["choices"][choice.group(1)] = choice.group(2).strip()
            i += 1
            continue

        head = ANSWER_HEAD_RE.match(line)
        if head:
            answer = _extract_answer(head.group(1))
            if answer:
                current["answer"] = answer
            # コールアウト1行目の補足（**B**（NACL）等）も解説の先頭に含める
            extra = ANSWER_TEXT_RE.search(head.group(1))
            first = f"答え：{extra.group(1)}" if extra else head.group(1)
            i += 1
            body, i = _collect_callout_body(lines, i)
            current["explanation_md"] = "\n".join([first] + body).strip()
            continue

        if not current["choices"] and not current["answer"]:
            current["q_lines"].append(line)
        i += 1

    _finish(current)
    return questions
