from django.conf.urls import url
from views import ApiController
from models import User, Track, Collaborator, File, Agreement, Comment


user_controller = ApiController(User, name='user_id')
track_controller = ApiController(Track, name='track_id', parent_name='user_id', fields=['description', 'song', 'tags', 'id', 'public', 'name'])
get_tracks_controller = ApiController(Track, name='track_id', parent_name='user_id', fields=['description', 'song', 'tags', 'id', 'public', 'name'], get_only=True)
collaborator_controller = ApiController(Collaborator, name='track_id')
file_controller = ApiController(File, name='track_id')
agreement_controller = ApiController(Agreement, name='track_id')
comment_controller = ApiController(Comment, name='track_id')

urlpatterns = [
    url(r'^users/?$', user_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)$', user_controller.single),

    url(r'^tracks/?$', get_tracks_controller.all),
    url(r'^tracks/(?P<track_id>[0-9]+)$', get_tracks_controller.single),

    url(r'^users/(?P<user_id>[0-9]+)/tracks/?$', track_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)$', track_controller.single),

    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/collaborators/?$', collaborator_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/collaborators/(?P<collaborator_id>[0-9]+)/?$', collaborator_controller.single),

    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/files/?$', file_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/files/(?P<file_id>[0-9]+)/?$', file_controller.single),

    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/agreements$', agreement_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/agreements/(?P<file_id>[0-9]+)/?$', agreement_controller.single),

    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/comments/?$', comment_controller.all),
    url(r'^users/(?P<user_id>[0-9]+)/tracks/(?P<track_id>[0-9]+)/comments/(?P<file_id>[0-9]+)/?$', comment_controller.single),
]
