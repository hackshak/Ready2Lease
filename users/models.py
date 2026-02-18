from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    username = None  # remove username
    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
