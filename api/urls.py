from django.conf.urls import url
from views import ApiController
from models import User

user_controller = ApiController(User, ['username', 'displayName', 'tagLine', 'label', 'description', 'tags'])
urlpatterns = [
    url(r'^users/$', user_controller.list(), name='user_list'),
    url(r'^users/(?P<user_id>[0-9]+)$', user_controller.list(), name='user_show'),
]
