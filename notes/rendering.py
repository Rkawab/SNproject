"""Obsidian風md → HTML レンダラ

取込対象mdの書式（frontmatter / [[wikilink]] / > [!type] コールアウト）を
アプリ表示用のHTMLに変換する。書式の前提は .claude/OVERVIEW.md を参照。
"""

import re

import markdown as md_lib

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "nl2br"]

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TAGS_RE = re.compile(r"^tags:\s*\[(.*?)\]", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(#[^\[\]|]*)?(?:\|([^\[\]]+))?\]\]")
CALLOUT_HEAD_RE = re.compile(r"^>\s*\[!(\w+)\](-?)\s*(.*)$")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

# Obsidianコールアウト種別 → 表示ラベル（タイトル省略時に使用）
CALLOUT_DEFAULT_TITLES = {
    "info": "Info",
    "note": "Note",
    "tip": "Tip",
    "success": "答え",
    "warning": "注意",
    "danger": "警告",
    "question": "Question",
    "example": "例",
    "quote": "引用",
}


def strip_frontmatter(text):
    """frontmatter を除去し (本文, tagsリスト) を返す"""
    tags = []
    m = FRONTMATTER_RE.match(text)
    if m:
        tm = TAGS_RE.search(m.group(1))
        if tm:
            tags = [t.strip() for t in tm.group(1).split(",") if t.strip()]
        text = text[m.end():]
    return text, tags


def extract_title(text):
    """先頭の # 見出しをタイトルとして返す（なければ None）"""
    m = H1_RE.search(text)
    return m.group(1).strip() if m else None


def resolve_wikilinks(text, link_map):
    """[[name]] / [[name#sec]] / [[name|alias]] をリンクまたはプレーン表示に変換する。

    link_map: {ファイル名(拡張子なし): URL}
    """

    def _repl(m):
        target = m.group(1).strip()
        alias = (m.group(3) or target).strip()
        url = link_map.get(target)
        if url:
            return f"[{alias}]({url})"
        return alias

    return WIKILINK_RE.sub(_repl, text)


def _render_inline(text):
    """1行テキストをHTML化（外側の <p> を除去）"""
    html = md_lib.markdown(text, extensions=MD_EXTENSIONS)
    html = re.sub(r"^<p>|</p>$", "", html.strip())
    return html


def convert_callouts(text):
    """Obsidianコールアウト（> [!type]±）をHTMLブロックに変換する。

    `-` 付きは <details>（折りたたみ）、なしは <div> にする。
    コールアウトでない通常の引用はそのまま残す。
    """
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = CALLOUT_HEAD_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        ctype = m.group(1).lower()
        collapsed = m.group(2) == "-"
        title = m.group(3).strip() or CALLOUT_DEFAULT_TITLES.get(ctype, ctype)

        body_lines = []
        i += 1
        while i < len(lines) and lines[i].startswith(">"):
            body_lines.append(re.sub(r"^>\s?", "", lines[i]))
            i += 1

        title_html = _render_inline(title)
        body_html = md_lib.markdown("\n".join(body_lines), extensions=MD_EXTENSIONS)

        if collapsed:
            block = (
                f'<details class="callout callout-{ctype}">'
                f'<summary>{title_html}</summary>'
                f'<div class="callout-body">{body_html}</div>'
                f"</details>"
            )
        else:
            block = (
                f'<div class="callout callout-{ctype}">'
                f'<div class="callout-title">{title_html}</div>'
                f'<div class="callout-body">{body_html}</div>'
                f"</div>"
            )
        # 前後に空行を入れて markdown にHTMLブロックとして認識させる
        out.extend(["", block, ""])
    return "\n".join(out)


def render_markdown(text, link_map=None):
    """md本文（frontmatter除去済み）をHTMLに変換する"""
    text = resolve_wikilinks(text, link_map or {})
    text = convert_callouts(text)
    return md_lib.markdown(text, extensions=MD_EXTENSIONS)
