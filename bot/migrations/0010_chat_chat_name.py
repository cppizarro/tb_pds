# Generated by Django 4.1.3 on 2022-11-08 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0009_alter_chat_trivia_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='chat_name',
            field=models.TextField(default='no name'),
        ),
    ]
