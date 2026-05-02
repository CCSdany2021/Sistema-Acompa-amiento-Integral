from django.contrib import admin
from .models import StudentCache

@admin.register(StudentCache)
class StudentCacheAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'code', 'grade', 'course', 'estado', 'last_synced')
    list_filter = ('estado', 'grade', 'course')
    search_fields = ('full_name', 'code', 'email')
    readonly_fields = ('last_synced', 'external_id')

    actions = ['sync_from_api']

    def sync_from_api(self, request, queryset):
        count = StudentCache.sync_from_api()
        self.message_user(request, f'✓ {count} estudiantes sincronizados')
    sync_from_api.short_description = 'Sincronizar estudiantes desde API'
