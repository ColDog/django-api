from django.http import HttpResponse
import json
import sys
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.decorators.csrf import csrf_exempt


class ApiController:
    def __init__(self, model, **kwargs):
        self.model = model
        self.fields = kwargs.get('fields') or self.model._meta.get_all_field_names()
        self.name = kwargs.get('name')
        self.parent_name = kwargs.get('parent_name')
        self.relations = kwargs.get('relations') or [rel.get_accessor_name() for rel in model._meta.get_all_related_objects()]
        self.get_only = kwargs.get('get_only') or False
        self.parent_model = kwargs.get('parent_model')
        self.set_name = kwargs.get('set_name')

    def run_response(self, method, request, kwargs):
        try:
            return HttpResponse(method(request, kwargs), status=200)
        except ObjectDoesNotExist as error:
            return HttpResponse(self.serialize_dict({'message': error.message}), status=404)
        except ValidationError as error:
            return HttpResponse(self.serialize_dict({'message': error.message}), status=400)
        # except Exception as error:
        #     return HttpResponse(self.serialize_dict({'message': error.message}), status=500)

    @csrf_exempt
    def nested_all(self, request, **kwargs):
        if request.method == 'POST' and not self.get_only:
            return self.run_response(self.create, request, kwargs)
        else:
            return self.run_response(self.list, request, kwargs)

    @csrf_exempt
    def all(self, request, **kwargs):
        if request.method == 'POST' and not self.get_only:
            return self.run_response(self.create, request, kwargs)
        else:
            return self.run_response(self.list, request, kwargs)

    @csrf_exempt
    def single(self, request, **kwargs):
        if request.method == 'POST' or request.method == 'PATCH' or request.method == 'POST' and not self.get_only:
            return self.run_response(self.update, request, kwargs)
        elif request.method == 'DELETE' and not self.get_only:
            return self.run_response(self.destroy, request, kwargs)
        else:
            return self.run_response(self.show, request, kwargs)

    def create(self, request, params):
        rec = self.to_dict(request.POST)
        if params.get(self.parent_name):
            rec[self.parent_name] = params[self.parent_name]
        record = self.model(**rec)
        record.save()
        return self.serialize_model(record)

    def update(self, request, params):
        filtered = self.model.objects.filter(pk=params[self.name])
        filtered.update(**self.to_dict(request.POST))
        return self.serialize_model(filtered[0])

    def destroy(self, request, params):
        record = self.model.objects.get(pk=params[self.name])
        record.delete()
        return self.serialize_dict({'status': 'success', 'message': 'Record deleted.'})

    def list(self, request, params):
        records = self.model.objects.all()
        return self.serialize_list(records)

    def nested_list(self, request, params):
        getattr(self.parent_model, self.set_name)
        parent = self.parent_model.objects.get(pk=params.get(self.parent_name))
        records = getattr(parent, self.set_name).all()
        return self.serialize_list(records)

    def show(self, request, params):
        record = self.model.objects.get(pk=params[self.name])
        related_objects = []
        if self.relations:
            for name in self.relations:
                relation = {name: self.serialize_list(getattr(record, name).all())}
                related_objects.append(relation)
        return self.serialize_model(record, related_objects)

    def to_dict(self, req):
        args = {}
        for field in self.fields:
            if field in req:
                args[field] = req[field]
        return args

    def serialize_dict(self, dictionary):
        return json.dumps(dictionary)

    def serialize_model(self, record, related='None'):
        obj = {}
        for field in record._meta.fields:
            if field.name in self.fields:
                obj[field.name] = record.__getattribute__(field.name)
        obj['relations'] = related
        print >>sys.stderr, obj
        return json.dumps(obj)

    def serialize_list(self, models):
        lis = []
        for record in models:
            obj = {}

            for field in record._meta.fields:
                if field.name in self.fields:
                    obj[field.name] = record.__getattribute__(field.name)

            lis.append(obj)

        return json.dumps(lis)
