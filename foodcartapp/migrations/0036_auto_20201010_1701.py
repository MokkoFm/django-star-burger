# Generated by Django 3.0.7 on 2020-10-10 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0035_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, verbose_name='комментарий'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('NO', 'Необработанный'), ('YES', 'Обработанный')], default='NO', max_length=3, verbose_name='статус'),
        ),
    ]
