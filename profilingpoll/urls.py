from django.conf.urls import patterns, url

from .views import poll_list, poll_detail, question


urlpatterns = patterns('',
    url(r'^$', poll_list, name='profilingpoll_poll_list'),
    url(r'^(?P<poll_slug>[\w-]+)/$', poll_detail, name='profilingpoll_poll_detail'),
    url(r'^(?P<poll_slug>[\w-]+)/(?P<question_id>\d+)/$', question, name='profilingpoll_question'),
)