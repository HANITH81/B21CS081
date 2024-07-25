from django.db import models

class Number(models.Model):
    value = models.IntegerField()

    class Meta:
        ordering = ['id']
