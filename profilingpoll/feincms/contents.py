from django.db import models
from django.template.loader import render_to_string

from ..models import Poll


class FirstPoll(models.Model):
    class Meta:
        abstract = True

    def render(self, request, **kwargs):
        try:
            #Poll.objects.filter(active=True)[0].description
            firstpoll = Poll.objects.filter(active=True)[0]
        except IndexError:
            firstpoll = None

        return render_to_string('content/profilingpoll/firstpoll.html',
                {'content': self, 'firstpoll' : firstpoll} )

