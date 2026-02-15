from django.contrib import admin
from .models import Notice, Response


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status', 'owner', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('title', 'description')


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('notice', 'responder', 'created_at')
