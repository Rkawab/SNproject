# StudyNotes（勉強用Webアプリ）

Obsidian保管庫の学習ノート・問題md を取り込み、スマホから「知識検索」「一問一答」「模擬試験」ができる個人用学習アプリ。

- 本番URL: `https://household-app-bacon.net/study/`
- 仕様書: `../.claude/` 配下（OVERVIEW.md / DATABASE.md / SCREENS.md / INFRA.md）

## 開発環境セットアップ

```powershell
# venv は 04_StudyNotes/snenv に作成済み
..\snenv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # ログインユーザー作成
python manage.py sync_content      # 保管庫 → content/ へ md 同期
python manage.py import_content    # content/ → DB 取込
python manage.py runserver
```

ローカルは `.env` の `dbname` を空にしておくと SQLite で動く（本番は PostgreSQL）。

## コンテンツ更新フロー（PCで実施）

1. Obsidian保管庫（`D:\Codespace\03_Notes\02_学習\AWS` 等）に md を追加・編集
2. `python manage.py sync_content`
3. git commit & push → GitHub Actions が RasPi に自動デプロイ（取込まで自動）

## 科目の追加・削除

- 追加: `content/sources.json` に `"slug": "保管庫パス"` を1行追加 → `sync_content` → push
- 削除: `python manage.py delete_subject <slug> --yes` ＋ `content/<slug>/` と sources.json のエントリを削除して push

詳細は `../.claude/OVERVIEW.md` を参照。
