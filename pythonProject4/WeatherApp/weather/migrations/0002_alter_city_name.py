# Generated by Django 4.1.2 on 2022-10-23 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='name',
            field=models.SlugField(max_length=30),
        ),
    ]
