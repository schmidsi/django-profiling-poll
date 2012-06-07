from django.db import models

from ..models import Poll


class FirstPollDescription(models.Model):
    class Meta:
        abstract = True

    def render(self, **kwargs):
        try:
            return Poll.objects.filter(active=True)[0].description
        except IndexError:
            return None

