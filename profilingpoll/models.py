from django.db import models
from django.utils.translation import ugettext_lazy as _


class TimestampMixin(object):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Poll(models.Model, TimestampMixin):
    description = models.TextField(_('description'), blank=True, null=True)


class Question(models.Model, TimestampMixin):
    poll = models.ForeignKey(Poll, related_name='questions')
    text = models.TextField(_('text'))


class Answer(models.Model, TimestampMixin):
    question = models.ForeignKey(Question, related_name='answers')
    text = models.TextField(_('text'))


class Profile(models.Model, TimestampMixin):
    text = models.TextField(_('text'))
    answers = models.ManyToManyField(Answer, through='AnswerProfile', related_name='profiles')


class AnswerProfile(models.Model, TimestampMixin):
    answer = models.ForeignKey(Answer, related_name='answerprofiles')
    profile = models.ForeignKey(Profile, related_name='answerprofiles')
    quantifier = models.IntegerField(_('quantifier'), default=1)