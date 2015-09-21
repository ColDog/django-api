from django.db import models
from django.contrib.postgres.fields import ArrayField
import bcrypt
import redis
import json

Redis = redis.Redis(host='localhost', port=6379, db=0)


class ModelDictionary:
    def __init__(self, base, **kwargs):
        self.base = base
        self.filter = kwargs.get('filter', [])
        self.field_names = [field.name for field in self.base._meta.local_fields]
        self.relation_names = [rel.get_accessor_name() for rel in self.base._meta.get_all_related_objects()]

    def to_dict(self):
        return {key: getattr(self.base, key) for key in self.field_names if not key == 'password'}

    def relations_to_dict(self):
        return {key: [model._data.to_dict for model in getattr(self.base, key).all()] for key in self.relation_names}

    def to_dict_with_relations(self):
        dic = self.to_dict()
        dic.update(self.base.relations_to_dict())
        return dic

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_json_with_relations(self):
        return json.dumps(self.to_dict_with_relations())


class User(models.Model):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    def __str__(self):
        return self.username

    username = models.CharField(max_length=50, unique=True, blank=False)
    displayName = models.CharField(max_length=50, blank=False)
    tagLine = models.CharField(max_length=200, blank=True)
    label = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    tags = ArrayField(ArrayField(models.CharField(max_length=50)), default=list)
    email = models.CharField(max_length=100, unique=True, blank=False)
    password = models.CharField(max_length=100, blank=False)

    def save(self):
        raw = self.password.encode('utf-8')
        self.password = bcrypt.hashpw(raw, bcrypt.gensalt(10))
        super(User, self).save()


class Track(models.Model):
    def __init__(self, *args, **kwargs):
        super(Track, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=False)
    public = models.BooleanField(default=False)
    song = models.CharField(max_length=100)
    tags = ArrayField(ArrayField(models.CharField(max_length=50)), default=list)

    def save(self, *args, **kwargs):
        key = 'entry:' + 'track_updated:' + str(self.id)
        Redis.hmset(key, {'type': 'track', 'id': self.id, 'description': self.description,
                          'link': self.song, 'user_id': self.user_id
                          })
        Redis.publish('new-entry', key + '.' + self.user_id)
        super(Track, self).save(*args, **kwargs)


class Collaborator(models.Model):
    def __init__(self, *args, **kwargs):
        super(Collaborator, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    track = models.ForeignKey(Track)
    user = models.ForeignKey(User)
    role = models.TextField()

    def save(self, *args, **kwargs):
        key = 'entry:' + 'collaborator_added:' + str(self.id)
        Redis.hmset(key, {'type': 'collaborator', 'id': self.id, 'description': 'collaborator added to track',
                          'link': self.song, 'user_id': self.user_id
                          })
        Redis.publish('new-entry', key + '.' + self.user_id)
        super(Collaborator, self).save(*args, **kwargs)


class File(models.Model):
    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    track = models.ForeignKey(Track)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)


class Agreement(models.Model):
    def __init__(self, *args, **kwargs):
        super(Agreement, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    track = models.ForeignKey(Track)
    remixer = models.ForeignKey(User)
    info = models.TextField()


class Comment(models.Model):
    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
        self._data = ModelDictionary(self)

    track = models.ForeignKey(Track)
    content = models.TextField()

    def save(self, *args, **kwargs):
        key = 'entry:' + 'commented:' + str(self.id)
        Redis.hmset(key, {'type': 'comment', 'id': self.id, 'description': 'comment added',
                          'link': self.track_id, 'user_id': self.user_id
                          })
        Redis.publish('new-entry', key + '.' + self.user_id)
        super(Comment, self).save(*args, **kwargs)

