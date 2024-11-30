from django.db import models
from django.contrib.auth.models import AbstractUser

class Uploaded_img(models.Model):

    img = models.ImageField(upload_to='photo', null=False, blank=True)

class User(AbstractUser):
    email = models.EmailField(max_length=128, unique=True)
    address = models.CharField(max_length=100, default=u"")
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta(AbstractUser.Meta):
        pass



class Analysed_img(models.Model):

    imgpath = models.CharField(max_length=200)
    useremail = models.EmailField(max_length=128, unique=True)
    analysisdate = models.DateTimeField(auto_now_add=True)
    originalid = models.IntegerField