from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    displayName = models.CharField(max_length=50)
    tagLine = models.CharField(max_length=200)
    label = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    tags = ArrayField(ArrayField(models.CharField(max_length=50)), default=list)


class Track(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    description = models.TextField()
    public = models.BooleanField(default=False)
    song = models.CharField(max_length=100)
    tags = ArrayField(ArrayField(models.CharField(max_length=50)), default=list)


class Collaborator(models.Model):
    track = models.ForeignKey(Track)
    user = models.ForeignKey(User)
    role = models.TextField()


class File(models.Model):
    track = models.ForeignKey(Track)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)


class Agreement(models.Model):
    track = models.ForeignKey(Track)
    remixer = models.ForeignKey(User)
    info = models.TextField()


class Comment(models.Model):
    track = models.ForeignKey(Track)
    content = models.TextField()
