from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ('username',)


class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, related_name='following',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, related_name='followers',
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription')
        ]
        ordering = ('user',)
