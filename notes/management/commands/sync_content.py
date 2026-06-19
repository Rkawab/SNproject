"""Obsidian保管庫 → リポジトリ内 content/ への md 同期（PC専用）

同期元は content/sources.json に科目slug→保管庫パスで定義する。
例: {"aws": "D:/Codespace/03_Notes/02_学習/AWS"}
除外対象は content/exclude.json と md frontmatter tags で定義する。
"""

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from notes.content_rules import load_exclude_manifest, should_exclude_md


def _source_path(src):
    """Windowsの `D:/...` 指定をWSL上でも読めるようにする。"""
    path = Path(src)
    if path.is_dir():
        return path
    if len(src) >= 3 and src[1:3] == ":/":
        wsl_path = Path("/mnt") / src[0].lower() / src[3:]
        if wsl_path.is_dir():
            return wsl_path
    return path


class Command(BaseCommand):
    help = "sources.json に従い、保管庫の md を content/<科目slug>/ へミラー同期する"

    def handle(self, *args, **options):
        content_dir = Path(settings.CONTENT_DIR)
        sources_path = content_dir / "sources.json"
        if not sources_path.exists():
            raise CommandError(f"{sources_path} がありません")

        sources = json.loads(sources_path.read_text(encoding="utf-8"))
        excludes = load_exclude_manifest(content_dir)

        for slug, src in sources.items():
            src_dir = _source_path(src)
            if not src_dir.is_dir():
                raise CommandError(f"同期元が見つかりません: {src_dir}（科目 {slug}）")
            dest_dir = content_dir / slug

            src_files = {
                p.relative_to(src_dir): p
                for p in src_dir.rglob("*.md")
                if not should_exclude_md(p, src_dir, slug, excludes)
            }

            copied = 0
            for rel, src_path in src_files.items():
                dest_path = dest_dir / rel
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                copied += 1

            # 同期元から消えたファイルは削除（ミラー）
            removed = 0
            if dest_dir.is_dir():
                for p in list(dest_dir.rglob("*.md")):
                    if p.relative_to(dest_dir) not in src_files:
                        p.unlink()
                        removed += 1
                # 空フォルダ掃除
                for d in sorted(dest_dir.rglob("*"), reverse=True):
                    if d.is_dir() and not any(d.iterdir()):
                        d.rmdir()

            self.stdout.write(self.style.SUCCESS(
                f"[{slug}] コピー {copied} 件 / 削除 {removed} 件 → {dest_dir}"
            ))

        self.stdout.write("同期完了。git commit & push でデプロイすると本番に反映されます。")
