from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acompanamiento', '0008_report_year_external_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='educador',
            name='secciones',
            field=models.ManyToManyField(
                blank=True,
                related_name='educadores_m2m',
                to='acompanamiento.section',
                verbose_name='Secciones asignadas',
            ),
        ),
    ]
