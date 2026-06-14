from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="questionset",
            name="set_type",
            field=models.CharField(choices=[("exam", "4択問題")], max_length=10),
        ),
    ]
