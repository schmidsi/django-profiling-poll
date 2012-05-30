from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import truncatechars


class TimestampMixin(object):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Poll(models.Model, TimestampMixin):
    description = models.TextField(_('description'), blank=True, null=True)


class Question(models.Model, TimestampMixin):
    poll = models.ForeignKey(Poll, related_name='questions')
    text = models.TextField(_('text'))

    def __unicode__(self):
        return truncatechars(self.text, 15)


class Answer(models.Model, TimestampMixin):
    question = models.ForeignKey(Question, related_name='answers')
    text = models.TextField(_('text'))


class Profile(models.Model, TimestampMixin):
    text = models.TextField(_('text'))
    answers = models.ManyToManyField(Answer, through='AnswerProfile', related_name='profiles')

    def __unicode__(self):
        return truncatechars(self.text, 15)


class AnswerProfile(models.Model, TimestampMixin):
    answer = models.ForeignKey(Answer, related_name='answerprofiles')
    profile = models.ForeignKey(Profile, related_name='answerprofiles')
    quantifier = models.IntegerField(_('quantifier'), default=1)


class Walkthrough(models.Model, TimestampMixin):
    poll = models.ForeignKey(Poll, related_name='walkthroughs')
    answers = models.ManyToManyField(Answer, blank=True, null=True)

    _completed = models.DateTimeField(blank=True, null=True)

    @property
    def completed(self):
        questions = set(self.poll.questions.all().select_related('answers'))
        answers = set(self.answers.all())
        answered_questions = set()

        for question in questions:
            for answer in answers:
                if answer in question.answers.all():
                    answered_questions.add(question)

        if answered_questions == questions:
            self._completed = datetime.now()
            self.save()
            return self._completed

        else:
            self._completed = None
            self.save()
            return self._completed

    def get_quantified_profiles(self):
        quantified_profiles = {}

        for answer in self.answers.all().select_related('answerprofiles'):
            for answer_profile in answer.answerprofiles.all():
                if answer_profile.profile in quantified_profiles:
                    quantified_profiles[answer_profile.profile] =+ answer_profile.quantifier
                else:
                    quantified_profiles[answer_profile.profile] = answer_profile.quantifier

        return quantified_profiles

    def get_most_matching_profile(self):
        quantified_profiles = self.get_quantified_profiles()
        highest_quantifing = 0
        candidate = None

        for profile in quantified_profiles:
            if quantified_profiles[profile] > highest_quantifing:
                highest_quantifing = quantified_profiles[profile]
                candidate = profile

        return candidate
