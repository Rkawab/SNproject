from django.db import models


class Subject(models.Model):
    """科目（AWS等）。import_content 実行時に content/ 配下のフォルダから自動作成される"""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    # 4択問題セットの合格ライン（SAA=8割）
    pass_ratio = models.FloatField(default=0.8)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Folder(models.Model):
    """ジャンル（取込元のフォルダ）"""

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    order = models.IntegerField(default=999)
    is_out_of_scope = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "name"]
        unique_together = [("subject", "name")]

    def __str__(self):
        return f"{self.subject.slug}/{self.name}"


class Note(models.Model):
    """知識ノート（mdファイル1つ＝1レコード）"""

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="notes")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="notes")
    # 元mdファイル名（拡張子なし）。wikilink の解決キー
    filename = models.CharField(max_length=300)
    title = models.CharField(max_length=300)
    tags = models.JSONField(default=list, blank=True)
    body_md = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    source_path = models.CharField(max_length=500)
    imported_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["folder__order", "filename"]
        unique_together = [("subject", "filename")]

    def __str__(self):
        return self.title
