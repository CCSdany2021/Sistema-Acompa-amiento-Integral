from django.contrib import admin
from .models import Section, Course, Student, Report, Observation, Recommendation, Educador, AuditoriaAccion

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    list_filter = ('section',)
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'code', 'course', 'section')
    list_filter = ('course__section',)
    search_fields = ('full_name', 'code', 'external_id')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'purpose', 'status', 'cumple_acompanamiento', 'created_at')
    list_filter = ('status', 'purpose', 'created_at')
    search_fields = ('student__full_name', 'student__code')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('report', 'created_by', 'date_log')
    list_filter = ('date_log',)
    search_fields = ('content',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('report', 'created_by', 'date_log')
    list_filter = ('date_log',)
    search_fields = ('content',)


@admin.register(Educador)
class EducadorAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'seccion_asignada', 'is_active', 'created_at')
    list_filter = ('rol', 'is_active', 'seccion_asignada')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')


@admin.register(AuditoriaAccion)
class AuditoriaAccionAdmin(admin.ModelAdmin):
    list_display = ('creado_en', 'accion', 'actor', 'autor_original', 'estudiante_nombre', 'report')
    list_filter = ('accion', 'creado_en')
    search_fields = ('estudiante_nombre', 'actor__username', 'actor__email', 'autor_original__email', 'detalle')
    readonly_fields = ('report', 'accion', 'actor', 'autor_original', 'estudiante_nombre', 'detalle', 'creado_en')
    ordering = ('-creado_en',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
