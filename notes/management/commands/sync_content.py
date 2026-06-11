"""Obsidian保管庫 → リポジトリ内 content/ への md 同期（PC専用）

同期元は content/sources.json に科目slug→保管庫パスで定義する。
例: {"aws": "D:/Codespace/03_Notes/02_学習/AWS"}
"""

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

EXCLUDE_DIR = "添付ファイル"


class Command(BaseCommand):
    help = "sources.json に従い、保管庫の md を content/<科目slug>/ へミラー同期する"

    def handle(self, *args, **options):
        content_dir = Path(settings.CONTENT_DIR)
        sources_path = content_dir / "sources.json"
        if not sources_path.exists():
            raise CommandError(f"{sources_path} がありません")

        sources = json.loads(sources_path.read_text(encoding="utf-8"))

        for slug, src in sources.items():
            src_dir = Path(src)
            if not src_dir.is_dir():
                raise CommandError(f"同期元が見つかりません: {src_dir}（科目 {slug}）")
            dest_dir = content_dir / slug

            src_files = {
                p.relative_to(src_dir): p
                for p in src_dir.rglob("*.md")
                if EXCLUDE_DIR not in p.parts
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
