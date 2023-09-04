from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,
                              null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)


class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, related_name='following',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, related_name='followers',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'author')
