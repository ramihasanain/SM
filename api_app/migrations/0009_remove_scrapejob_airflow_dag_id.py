from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0008_google_totp_auth'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scrapejob',
            name='airflow_dag_id',
        ),
    ]
