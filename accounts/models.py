
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class Manager(BaseUserManager):
    def create_user(self,email,password=None,**extra):
        email=self.normalize_email(email)
        u=self.model(email=email,**extra)
        u.set_password(password)
        u.save()
        return u
    def create_superuser(self,email,password=None,**extra):
        extra.setdefault('is_staff',True)
        extra.setdefault('is_superuser',True)
        return self.create_user(email,password,**extra)

class CustomUser(AbstractBaseUser,PermissionsMixin):
    email=models.EmailField(unique=True)
    phone=models.CharField(max_length=20,blank=True)
    address=models.CharField(max_length=255,blank=True)

    is_active=models.BooleanField(default=True)
    is_staff=models.BooleanField(default=False)
    is_hr=models.BooleanField(default=False)
    is_employee=models.BooleanField(default=False)

    objects=Manager()
    USERNAME_FIELD='email'
