"""content/ 配下の md をパースして DB へ取り込む

分類ルール（科目に依存しない）:
- ファイル名に「一問一答」を含む → 一問一答セット
- ファイル名に「模擬試験」を含む → 模擬試験セット
- それ以外 → 知識ノート
- フォルダ名に「範囲外」を含む → 範囲外フラグ付きノート
"""

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from notes.models import Subject, Folder, Note
from notes.rendering import strip_frontmatter, extract_title, render_markdown
from quiz.models import QuestionSet, Question
from quiz.parsing import parse_basic, parse_exam

EXCLUDE_DIR = "添付ファイル"
LEADING_NUM_RE = re.compile(r"^(\d+)")


def _leading_number(name, default=999):
    m = LEADING_NUM_RE.match(name)
    return int(m.group(1)) if m else default


def _display_name(folder_name):
    """`01_EC2` → `EC2` のように先頭番号を除いた表示名"""
    return re.sub(r"^\d+_?", "", folder_name) or folder_name


class Command(BaseCommand):
    help = "content/<科目slug>/ の md をパースして DB へ取り込む（ファイル単位で洗い替え）"

    def handle(self, *args, **options):
        content_dir = Path(settings.CONTENT_DIR)
        if not content_dir.is_dir():
            self.stdout.write(self.style.WARNING(f"{content_dir} がありません。先に sync_content を実行してください。"))
            return

        for subject_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
            self._import_subject(subject_dir)

    def _import_subject(self, subject_dir):
        slug = subject_dir.name
        subject, created = Subject.objects.get_or_create(
            slug=slug,
            defaults={"name": slug.upper(), "order": Subject.objects.count()},
        )
        if created:
            self.stdout.write(f"科目を新規作成: {slug}")

        md_files = [p for p in subject_dir.rglob("*.md") if EXCLUDE_DIR not in p.parts]
        note_files, basic_files, exam_files = [], [], []
        for p in md_files:
            if "一問一答" in p.stem:
                basic_files.append(p)
            elif "模擬試験" in p.stem:
                exam_files.append(p)
            else:
                note_files.append(p)

        # --- pass1: ノート本体を保存（HTMLは後で） ---
        note_stems = set()
        for path in note_files:
            rel = path.relative_to(subject_dir)
            folder_name = rel.parts[0] if len(rel.parts) > 1 else ""
            folder, _ = Folder.objects.update_or_create(
                subject=subject,
                name=folder_name,
                defaults={
                    "display_name": _display_name(folder_name) if folder_name else "その他",
                    "order": _leading_number(folder_name) if folder_name else 999,
                    "is_out_of_scope": "範囲外" in folder_name,
                },
            )
            body, tags = strip_frontmatter(path.read_text(encoding="utf-8-sig"))
            note_stems.add(path.stem)
            Note.objects.update_or_create(
                subject=subject,
                filename=path.stem,
                defaults={
                    "folder": folder,
                    "title": extract_title(body) or path.stem,
                    "tags": tags,
                    "body_md": body,
                    "source_path": str(rel),
                },
            )

        # 消えたノート・空フォルダを削除
        Note.objects.filter(subject=subject).exclude(filename__in=note_stems).delete()
        Folder.objects.filter(subject=subject, notes__isnull=True).delete()

        # --- wikilink 解決マップ（ファイル名 → ノート詳細URL） ---
        link_map = {
            n.filename: reverse("notes:detail", args=[n.id])
            for n in Note.objects.filter(subject=subject)
        }

        # --- pass2: ノートHTMLレンダリング ---
        for note in Note.objects.filter(subject=subject):
            note.body_html = render_markdown(note.body_md, link_map)
            note.save(update_fields=["body_html", "imported_at"])

        # --- 問題セット ---
        set_stems = set()
        n_questions = 0
        for path, set_type, parser in (
            [(p, QuestionSet.TYPE_BASIC, parse_basic) for p in basic_files]
            + [(p, QuestionSet.TYPE_EXAM, parse_exam) for p in exam_files]
        ):
            body, _tags = strip_frontmatter(path.read_text(encoding="utf-8-sig"))
            items = parser(body)
            if not items:
                self.stdout.write(self.style.WARNING(f"問題を抽出できません（書式確認）: {path.name}"))
                continue
            set_stems.add(path.stem)
            qset, _ = QuestionSet.objects.update_or_create(
                source_filename=path.stem,
                defaults={
                    "subject": subject,
                    "set_type": set_type,
                    "title": extract_title(body) or path.stem,
                    "order": _leading_number(path.stem),
                },
            )
            numbers = []
            for item in items:
                numbers.append(item["number"])
                Question.objects.update_or_create(
                    question_set=qset,
                    number=item["number"],
                    defaults={
                        "genre": item["genre"],
                        "question_html": render_markdown(item["question_md"], link_map),
                        "choices": item.get("choices"),
                        "answer": item["answer"],
                        "explanation_html": render_markdown(item["explanation_md"], link_map),
                    },
                )
            # mdから消えた問題を削除（番号維持なら AnswerLog は引き継がれる）
            qset.questions.exclude(number__in=numbers).delete()
            n_questions += len(numbers)

        QuestionSet.objects.filter(subject=subject).exclude(source_filename__in=set_stems).delete()

        self.stdout.write(self.style.SUCCESS(
            f"[{slug}] ノート {len(note_stems)} 件 / 問題セット {len(set_stems)} 件（{n_questions} 問）を取込"
        ))
