"""科目の全データ削除（試験終了後の撤去用）

DBのみ削除する。content/<slug>/ フォルダと sources.json のエントリは
別途手動で削除して push すること（Obsidian保管庫の元mdには影響しない）。
"""

from django.core.management.base import BaseCommand, CommandError

from notes.models import Subject


class Command(BaseCommand):
    help = "指定科目のノート・問題・回答履歴をDBから一括削除する"

    def add_arguments(self, parser):
        parser.add_argument("slug", help="削除する科目のslug（例: aws）")
        parser.add_argument("--yes", action="store_true", help="確認なしで削除を実行する")

    def handle(self, *args, **options):
        slug = options["slug"]
        try:
            subject = Subject.objects.get(slug=slug)
        except Subject.DoesNotExist:
            raise CommandError(f"科目 '{slug}' は存在しません")

        n_notes = subject.notes.count()
        n_sets = subject.question_sets.count()

        if not options["yes"]:
            self.stdout.write(self.style.WARNING(
                f"科目 '{slug}'（ノート {n_notes} 件・問題セット {n_sets} 件・回答履歴含む）を削除します。\n"
                f"実行するには --yes を付けてください。"
            ))
            return

        subject.delete()
        self.stdout.write(self.style.SUCCESS(f"科目 '{slug}' を削除しました（ノート {n_notes} 件・問題セット {n_sets} 件）"))
        self.stdout.write("content/ 配下のフォルダと sources.json のエントリも不要なら削除して push してください。")
