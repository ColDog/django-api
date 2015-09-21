import json


class Serializer:
    def __init__(self, fields):
        self.fields = fields

    def to_dict(self, req):
        args = {}
        for field in self.fields:
            if field in req:
                args[field] = req[field]
        return args

    def model_to_dict(self, record):
        obj = {}
        for field in record._meta.fields:
            if field.name in self.fields:
                if not field.name == 'password':
                    obj[field.name] = record.__getattribute__(field.name)
        return obj

    def model(self, record, related=False):
        obj = self.model_to_dict(record)
        if related:
            obj.update(related)
        for key in obj:
            try:
                obj[key] = Serializer(obj[key]._meta.get_all_field_names()).model_to_dict(obj[key])
            except AttributeError:
                None
        return json.dumps(obj)

    def list_to_dict(self, models):
        lis = []
        for record in models:
            obj = {}

            for field in record._meta.fields:
                if field.name in self.fields and not field.name == 'password':
                    obj[field.name] = record.__getattribute__(field.name)

            lis.append(obj)
        return lis

    def list(self, models):
        lis = self.list_to_dict(models)
        return json.dumps(lis)
