from datetime import datetime

from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
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

    # Denormalizations
    _completed = models.DateTimeField(blank=True, null=True)
    _answered_questions = models.ManyToManyField(Question)
    _profiles = models.ManyToManyField(Profile, through='WalkthroughProfile', blank=True, null=True,
        related_name='walkthrough_set')

    @property
    def answered_questions(self):
        return self._answered_questions.all()

    @property
    def completed(self):
        return self._completed

    def get_matching_profile(self):
        return self.walkthroughprofiles.order_by('-quantifier')[0].profile


class WalkthroughProfile(models.Model, TimestampMixin):
    walkthrough = models.ForeignKey(Walkthrough, related_name='walkthroughprofiles')
    profile = models.ForeignKey(Profile, related_name='walkthroughprofiles')
    quantifier = models.IntegerField(_('quantifier'), default=1)


@receiver(m2m_changed, sender=Walkthrough.answers.through)
def denormalize_walkthrough(signal, sender, instance, action, reverse, model, pk_set, using):
    if 'post' in action and pk_set and len(pk_set):

        answer = model.objects.get(pk=pk_set.pop())

        if 'add' in action:
            instance._answered_questions.add(answer.question)

            for answer_profile in answer.answerprofiles.all():
                if not answer_profile.profile in instance._profiles.all():
                    WalkthroughProfile.objects.create(
                        walkthrough = instance,
                        profile = answer_profile.profile,
                        quantifier = answer_profile.quantifier
                    )
                else:
                    walkthroughprofile = instance.walkthroughprofiles.get(profile=answer_profile.profile)
                    walkthroughprofile.quantifier += answer_profile.quantifier
                    walkthroughprofile.save()
        elif 'remove' in action:
            instance._answered_questions.remove(answer.question)

            for answer_profile in answer.answerprofiles.all():
                if answer_profile.profile in instance._profiles.all():
                    walkthroughprofile = instance.walkthroughprofiles.get(profile=answer_profile.profile)
                    walkthroughprofile.quantifier -= answer_profile.quantifier
                    walkthroughprofile.save()

        if instance._answered_questions.all().count() == instance.poll.questions.all().count():
            instance._completed = datetime.now()
        else:
            instance._completed = None

    elif 'post_clear' in action:
        instance._answered_questions.clear()
        instance._profiles.clear()
