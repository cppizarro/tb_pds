# Generated by Django 4.1.3 on 2022-11-11 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0013_rename_actual_question_chat_actual_question_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='tivia_correct_answer',
            field=models.TextField(default=''),
        ),
    ]
