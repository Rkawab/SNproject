"""一問一答・模擬試験mdのパーサ

書式の前提（.claude/OVERVIEW.md「md書式の前提」参照）:

一問一答:
    ## ジャンル見出し
    **Q1.** 問題文
    > [!success]- 答え：**答えテキスト**
    > 解説...

模擬試験:
    ## 第N問（ジャンル）
    問題文
    - A. 選択肢
    - B. 選択肢
    > [!success]- 答え：**B**（補足）
    > 解説...
"""

import re

SECTION_RE = re.compile(r"^##\s+(.+)$")
EXAM_SECTION_RE = re.compile(r"^##\s*第(\d+)問[（(](.*?)[）)]")
BASIC_Q_RE = re.compile(r"^\*\*Q(\d+)[.．]\*\*\s*(.*)$")
CHOICE_RE = re.compile(r"^-\s*([A-D])[.．]\s*(.*)$")
ANSWER_HEAD_RE = re.compile(r"^>\s*\[!success\]-?\s*(.*)$", re.IGNORECASE)
ANSWER_TEXT_RE = re.compile(r"答え\s*[：:]\s*(.*)$")
EXAM_ANSWER_LETTER_RE = re.compile(r"\*\*([A-D])\*\*")


def _collect_callout_body(lines, i):
    """i行目以降の引用ブロック（> ...）を集めて (本文行リスト, 次の行番号) を返す"""
    body = []
    while i < len(lines) and lines[i].startswith(">"):
        body.append(re.sub(r"^>\s?", "", lines[i]))
        i += 1
    return body, i


def parse_basic(text):
    """一問一答mdをパースし、問題のリストを返す。

    戻り値: [{number, genre, question_md, answer, explanation_md}, ...]
    """
    lines = text.split("\n")
    questions = []
    genre = ""
    i = 0
    while i < len(lines):
        line = lines[i]

        sec = SECTION_RE.match(line)
        if sec:
            genre = sec.group(1).strip()
            i += 1
            continue

        q = BASIC_Q_RE.match(line)
        if not q:
            i += 1
            continue

        number = int(q.group(1))
        q_lines = [q.group(2)]
        i += 1
        # 答えコールアウトが始まるまでを問題文として収集
        while i < len(lines) and not ANSWER_HEAD_RE.match(lines[i]) and not BASIC_Q_RE.match(lines[i]):
            q_lines.append(lines[i])
            i += 1

        answer = ""
        explanation_lines = []
        head = ANSWER_HEAD_RE.match(lines[i]) if i < len(lines) else None
        if head:
            am = ANSWER_TEXT_RE.search(head.group(1))
            if am:
                # **答え** の強調記号を外してプレーンに
                answer = am.group(1).replace("**", "").strip()
            i += 1
            explanation_lines, i = _collect_callout_body(lines, i)

        questions.append({
            "number": number,
            "genre": genre,
            "question_md": "\n".join(q_lines).strip(),
            "answer": answer,
            "explanation_md": "\n".join(explanation_lines).strip(),
        })
    return questions


def parse_exam(text):
    """模擬試験mdをパースし、問題のリストを返す。

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
            lm = EXAM_ANSWER_LETTER_RE.search(head.group(1))
            if lm:
                current["answer"] = lm.group(1)
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
