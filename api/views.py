from django.shortcuts import HttpResponse
from models import User
from django.core import serializers
from django.http import Http404


class ApiController:
    def __init__(self, model, fields):
        self.model = model
        self.fields = fields

    def list(self):
        data = serializers.serialize('json', User.objects.all(), fields=self.fields)
        return self.serialize(data)

    def create(self, request):
        try:
            record = self.model(**self.to_dict(request.POST))
            record.save()
            return self.serialize(record)
        except Exception as error:
            raise Http404(error)

    def update(self, request, record_id):
        try:
            record = self.model.objects.filter(pk=record_id).update(**self.to_dict(request.POST))
            return self.serialize(record)
        except Exception as error:
            raise Http404(error)

    def destroy(self, record_id):
        try:
            record = self.model.objects.get(pk=record_id)
            record.delete()
            return self.serialize(record)
        except Exception as error:
            raise Http404(error)

    def show(self, record_id):
        try:
            record = self.model.objects.get(pk=record_id)
            return self.serialize(record)
        except Exception as error:
            raise Http404(error)

    def to_dict(self, req):
        args = {}
        for i in self.fields:
            args[self.fields[i]] = req[self.fields[i]]
        return args

    def serialize(self, record):
        data = serializers.serialize('json', record, fields=self.fields)
        return HttpResponse(data, mimetype='application/json')