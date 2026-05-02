from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Section, Course, Student, Report, Observation, Recommendation, Educador

User = get_user_model()

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'grado', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'section', 'section_name', 'created_at']


class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True, allow_null=True)
    section_name = serializers.CharField(source='course.section.name', read_only=True, allow_null=True)

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'code', 'email', 'section', 'grado',
            'course', 'course_name', 'section_name', 'imagen',
            'external_id', 'last_synced', 'created_at'
        ]


class ObservationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Observation
        fields = [
            'id', 'report', 'title', 'content', 'created_by',
            'created_by_name', 'correo_institucional', 'fin_educativo', 'date_log'
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            'id', 'report', 'content', 'created_by',
            'created_by_name', 'correo_institucional', 'fin_educativo', 'date_log'
        ]


class EducadorSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    seccion_asignada_nombre = serializers.CharField(source='seccion_asignada.name', read_only=True, allow_null=True)

    class Meta:
        model = Educador
        fields = [
            'id', 'user', 'user_full_name', 'user_email',
            'rol', 'seccion_asignada', 'seccion_asignada_nombre',
            'is_active', 'created_at'
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado del reporte con observaciones y recomendaciones anidadas"""
    student_data = StudentSerializer(source='student', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)
    observations = ObservationSerializer(many=True, read_only=True)
    recommendations = RecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'student', 'student_data', 'purpose', 'status',
            'fines_educativos', 'objective', 'academic_period',
            'is_accomplished', 'cumple_acompanamiento',
            'institucional_quien_atiende', 'datos_adjuntos',
            'imagen', 'recuento', 'fecha_cierre',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name',
            'observations', 'recommendations',
            'created_at', 'updated_at'
        ]


class ReportListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar reportes"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_code = serializers.CharField(source='student.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = [
            'id', 'student', 'student_name', 'student_code',
            'purpose', 'fines_educativos', 'status', 'objective', 'academic_period',
            'is_accomplished', 'cumple_acompanamiento', 'recuento', 'fecha_cierre',
            'created_by_name', 'assigned_to_name',
            'created_at', 'updated_at'
        ]


class ReportCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar reportes"""

    class Meta:
        model = Report
        fields = [
            'student', 'purpose', 'status',
            'fines_educativos', 'objective', 'academic_period',
            'is_accomplished', 'cumple_acompanamiento',
            'institucional_quien_atiende', 'datos_adjuntos',
            'imagen', 'assigned_to'
        ]

    def validate(self, data):
        """Validación: Un reporte activo por estudiante + fin educativo"""
        student = data.get('student')
        purpose = data.get('purpose')
        fines_educativos = data.get('fines_educativos', [])
        status = data.get('status')

        # Excluir reportes cerrados
        active_statuses = ['PROGRAMADO', 'SEGUIMIENTO']
        if status in active_statuses:
            if purpose:
                existing = Report.objects.filter(
                    student=student,
                    purpose=purpose,
                    status__in=active_statuses
                ).exclude(pk=self.instance.pk if self.instance else None)

                if existing.exists():
                    raise serializers.ValidationError(
                        f"Ya existe un reporte activo para {student.full_name} con fin educativo {purpose}"
                    )

            if fines_educativos and not isinstance(fines_educativos, list):
                raise serializers.ValidationError("fines_educativos debe ser una lista de valores")

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
