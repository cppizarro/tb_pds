# Generated by Django 4.1.3 on 2022-11-09 19:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0012_member_answered_trivia'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='actual_question',
            new_name='actual_question_number',
        ),
    ]
