from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class Login(models.Model):
    userid = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=255, blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.id) + '_' + self.userid
    

class Token(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(default=timezone.now() + timedelta(minutes=60), blank=True, null=True)

    def __str__(self):
        return 'of userid: ' + str(self.user.id)


class Shop(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)