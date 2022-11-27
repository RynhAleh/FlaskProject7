from django.db import models


# Create your models here.
class City (models.Model):
    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=30, unique=True)

    def __str__(self):
        return self.name
