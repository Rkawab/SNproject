import fnmatch
import json
import re
from pathlib import Path

EXCLUDE_DIR = "添付ファイル"
ARCHIVE_MARKER = "archive"
EXCLUDE_TAGS = {"sync-exclude", "アプリ同期除外"}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
TAGS_LINE_RE = re.compile(r"^tags\s*:\s*(.*)$")


def load_exclude_manifest(content_dir):
    """content/exclude.json を読み込む。無い場合は空定義として扱う。"""
    path = Path(content_dir) / "exclude.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {
        str(slug): [str(pattern).replace("\\", "/") for pattern in patterns]
        for slug, patterns in data.items()
        if isinstance(patterns, list)
    }


def has_excluded_dir(parts):
    """パス要素に除外フォルダ（添付ファイル / archive 系）が含まれるか。"""
    for part in parts:
        if part == EXCLUDE_DIR or ARCHIVE_MARKER in part.lower():
            return True
    return False


def is_manifest_excluded(slug, rel_path, manifest):
    """科目ごとの除外パターンに一致するか。"""
    rel = Path(rel_path)
    key = rel.as_posix()
    name = rel.name
    patterns = list(manifest.get("*", [])) + list(manifest.get(slug, []))
    for pattern in patterns:
        if fnmatch.fnmatch(key, pattern) or fnmatch.fnmatch(name, pattern):
            return True
    return False


def frontmatter_tags(text):
    """簡易的に frontmatter の tags を抽出する。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return set()

    lines = m.group(1).splitlines()
    tags = []
    i = 0
    while i < len(lines):
        line = lines[i]
        tm = TAGS_LINE_RE.match(line.strip())
        if not tm:
            i += 1
            continue

        value = tm.group(1).strip()
        if value:
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            tags.extend(value.split(","))
        else:
            i += 1
            while i < len(lines):
                item = lines[i].strip()
                if not item.startswith("- "):
                    break
                tags.append(item[2:])
                i += 1
            continue
        i += 1

    return {tag.strip().strip("\"'").lstrip("#") for tag in tags if tag.strip()}


def has_exclude_tag(path):
    try:
        tags = frontmatter_tags(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        tags = frontmatter_tags(path.read_text(encoding="utf-8"))
    return bool(tags & EXCLUDE_TAGS)


def should_exclude_md(path, root_dir, slug, manifest):
    """同期・取込対象から外す md かどうかを共通判定する。"""
    rel = path.relative_to(root_dir)
    return (
        has_excluded_dir(rel.parts)
        or is_manifest_excluded(slug, rel, manifest)
        or has_exclude_tag(path)
    )
