# Generated by Django 4.1.3 on 2022-11-08 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0008_chat_trivia_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='trivia_questions',
            field=models.JSONField(default={}),
        ),
    ]
