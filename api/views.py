from django.http import HttpResponse
import json
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
import bcrypt
import jwt
from skio.settings import SECRET_KEY
from serializer import Serializer
import sys


class AuthenticationFailed(Exception):
    pass


def json_response(message, status):
    if isinstance(message, dict):
        serialized = json.dumps(message)
    else:
        serialized = message
    return HttpResponse(serialized, status=status, content_type='application/json')


def run_response(method, request, kwargs):
    try:
        return json_response(method(request, kwargs), 200)
    except ObjectDoesNotExist as error:
        message = {'message': error.message, 'success': False}
        return json_response(message, 404)
    except ValidationError as error:
        message = {'message': error.message, 'success': False}
        return json_response(message, 400)
    except IntegrityError as error:
        message = {'message': error.message, 'success': False}
        return json_response(message, 400)
    except AuthenticationFailed as error:
        message = {'message': error.message, 'success': False}
        return json_response(message, 401)
    # except Exception as error:
    #     message = {'message': error.message, 'success': False}
    #     return json_response(message, 500)


class ApiAuthenticationController:
    def __init__(self, user_model):
        self.user_model = user_model

    @csrf_exempt
    def authenticate(self, request, **params):
        return run_response(self.check_password, request, params)

    def check_password(self, request, params):
        email = request.data.get('email', False)
        password = request.data.get('password', False)
        if email and password:
            user = self.user_model.objects.get(email=email)
            encoded_pass = password.encode('utf-8')
            encoded_hash = user.password.encode('utf-8')
            if bcrypt.hashpw(encoded_pass, encoded_hash):
                token = jwt.encode({'user_id': user.id}, SECRET_KEY)
                message = {'token': token, 'success': True, 'message': 'Authentication successful.', 'user': Serializer(user._meta.get_all_field_names()).model_to_dict(user)}
                return message
            else:
                raise AuthenticationFailed('Authentication failed.')
        else:
            raise AuthenticationFailed('Authentication failed. No email or password provided.')


class ApiController:
    def __init__(self, model, **kwargs):
        self.model = model
        self.fields = kwargs.get('fields') or self.model._meta.get_all_field_names()
        self.name = kwargs.get('name')
        self.parent_name = kwargs.get('parent_name', False)
        if self.parent_name:
            self.parent_id = self.parent_name + '_id'
        else:
            self.parent_id = ''
        self.id = self.name + '_id'
        self.set_name = self.name + '_set'
        self.relations = kwargs.get('relations') or [rel.get_accessor_name() for rel in model._meta.get_all_related_objects()]
        self.parent_model = kwargs.get('parent_model')
        self.serialize = Serializer(self.fields)

    @csrf_exempt
    def nested_all(self, request, **kwargs):
        if request.method == 'POST':
            return run_response(self.create, request, kwargs)
        else:
            return run_response(self.nested_list, request, kwargs)

    @csrf_exempt
    def all(self, request, **kwargs):
        if request.method == 'POST':
            return run_response(self.create, request, kwargs)
        else:
            return run_response(self.list, request, kwargs)

    @csrf_exempt
    def all_or_authenticate(self, request, **kwargs):
        if request.method == 'POST':
            return run_response(self.create_user, request, kwargs)
        else:
            return run_response(self.list, request, kwargs)

    @csrf_exempt
    def single(self, request, **kwargs):
        if request.method == 'POST' or request.method == 'PATCH' or request.method == 'PUT':
            return run_response(self.update, request, kwargs)
        elif request.method == 'DELETE':
            return run_response(self.destroy, request, kwargs)
        else:
            return run_response(self.show, request, kwargs)

    def create_user(self, request, params):
        attrs = self.serialize.to_dict(request.data)
        if params.get(self.parent_id):
            attrs[self.parent_id] = params[self.parent_id]
        user = self.model(**attrs)
        user.save()
        token = jwt.encode({'user_id': user.id}, SECRET_KEY)
        return {'success': True, 'token': token, 'user': self.serialize.model_to_dict(user)}

    def create(self, request, params):
        attrs = self.serialize.to_dict(request.data)
        if params.get(self.parent_id):
            attrs[self.parent_id] = params[self.parent_id]
        record = self.model(**attrs)
        record.save()
        return self.serialize.model(record)

    def update(self, request, params):
        filtered = self.model.objects.filter(pk=params[self.id])
        filtered.update(**self.serialize.to_dict(request.data))
        return self.serialize.model(filtered[0])

    def destroy(self, request, params):
        record = self.model.objects.get(pk=params[self.id])
        record.delete()
        return {'status': 'success', 'message': 'Record deleted.'}

    def list(self, request, params):
        records = self.model.objects.all()
        return self.serialize.list(records)

    def nested_list(self, request, params):
        getattr(self.parent_model, self.set_name)
        parent = self.parent_model.objects.get(pk=params.get(self.parent_id))
        records = getattr(parent, self.set_name).all()
        return self.serialize.list(records)

    def show(self, request, params):
        record = self.model.objects.get(pk=params[self.id])
        relations = self.add_relations(record)
        return self.serialize.model(record, relations)

    def add_relations(self, record):
        relations = {}
        print >>sys.stderr, 'relations', self.relations
        if self.relations:
            for name in self.relations:
                relations[name] = self.serialize.list_to_dict(getattr(record, name).all())
                print >>sys.stderr, 'DATA:', 'add relations', getattr(record, name).all()
        print >>sys.stderr, 'relations', relations
        return relations
