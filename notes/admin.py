from django.contrib import admin

from .models import Subject, Folder, Note


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "order", "pass_ratio")
    list_editable = ("name", "order", "pass_ratio")


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "display_name", "order", "is_out_of_scope")
    list_filter = ("subject",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "folder", "imported_at")
    list_filter = ("subject", "folder")
    search_fields = ("title", "filename")
