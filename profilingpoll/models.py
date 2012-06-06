from datetime import datetime

from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import truncatechars


class TimestampMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Poll(TimestampMixin):
    active = models.BooleanField(default=False)
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'), blank=True, null=True)

    def __unicode__(self):
        return truncatechars(self.description, 50)

    @models.permalink
    def get_absolute_url(self):
        return ('profilingpoll_poll_detail', (), {'slug' : self.slug})

    def get_first_question(self):
        return self.questions.all()[0]


class Question(TimestampMixin):
    poll = models.ForeignKey(Poll, related_name='questions')
    text = models.TextField(_('text'))
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('ordering', 'created', 'id')

    def __unicode__(self):
        return truncatechars(self.text, 50)

    @models.permalink
    def get_absolute_url(self):
        return ('profilingpoll_question', (), {'poll__slug' : self.poll.slug, 'id' : self.id})

    def next(self):
        questionlist = list(self.poll.questions.all())
        selfindex = questionlist.index(self)

        try:
            return questionlist[selfindex + 1]
        except IndexError:
            return None

    @property
    def multiple_answers(self):
        # TODO: change this to a real feature
        return False

    def question_answered(self, walkthrough):
        answers_to_self = walkthrough.answers.filter(question=self)

        if answers_to_self.count() >= 1:
            return True
        else:
            return False


class Answer(TimestampMixin):
    question = models.ForeignKey(Question, related_name='answers')
    text = models.TextField(_('text'))
    ordering = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return truncatechars(self.text, 50)


class Profile(TimestampMixin):
    text = models.TextField(_('text'))
    answers = models.ManyToManyField(Answer, through='AnswerProfile', related_name='profiles')

    def __unicode__(self):
        return truncatechars(self.text, 50)


class AnswerProfile(TimestampMixin):
    answer = models.ForeignKey(Answer, related_name='answerprofiles')
    profile = models.ForeignKey(Profile, related_name='answerprofiles')
    quantifier = models.IntegerField(_('quantifier'), default=1)


class Walkthrough(TimestampMixin):
    poll = models.ForeignKey(Poll, related_name='walkthroughs')
    answers = models.ManyToManyField(Answer, blank=True, null=True)

    # Denormalizations:
    _completed = models.DateTimeField(blank=True, null=True)
    _answered_questions = models.ManyToManyField(Question)
    _progress = models.FloatField(blank=True, null=True) # between 0 and 1
    _profiles = models.ManyToManyField(Profile, through='WalkthroughProfile', blank=True, null=True,
        related_name='walkthrough_set')

    @property
    def answered_questions(self):
        return self._answered_questions.all()

    @property
    def completed(self):
        return self._completed

    @property
    def progress(self):
        return self._progress

    def get_matching_profile(self):
        return self.walkthroughprofiles.order_by('-quantifier')[0].profile

    def get_next_question(self):
        return self.poll.questions.all().exclude(id__in=self._answered_questions.all().values_list('id', flat=True))[0]


class WalkthroughProfile(TimestampMixin):
    walkthrough = models.ForeignKey(Walkthrough, related_name='walkthroughprofiles')
    profile = models.ForeignKey(Profile, related_name='walkthroughprofiles')
    quantifier = models.IntegerField(_('quantifier'), default=1)


@receiver(m2m_changed, sender=Walkthrough.answers.through)
def denormalize_walkthrough(signal, sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if 'post' in action and pk_set and len(pk_set):

        answer = model.objects.get(pk=pk_set.pop())
        question = answer.question

        if 'add' in action:
            # question already answered -> keep last answer
            if question in instance._answered_questions.all():
                if not question.multiple_answers:
                    instance.answers.exclude(id=answer.id).delete()
            else:
                instance._answered_questions.add(question)

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
            instance._answered_questions.remove(question)

            for answer_profile in answer.answerprofiles.all():
                if answer_profile.profile in instance._profiles.all():
                    walkthroughprofile = instance.walkthroughprofiles.get(profile=answer_profile.profile)
                    walkthroughprofile.quantifier -= answer_profile.quantifier
                    walkthroughprofile.save()

        all_questions_count = instance.poll.questions.all().count()
        answered_questions_count = instance._answered_questions.all().count()

        instance._progress = float(answered_questions_count) / float(all_questions_count)

        if answered_questions_count == all_questions_count:
            instance._completed = datetime.now()
        else:
            instance._completed = None

        instance.save()

    elif 'post_clear' in action:
        instance._answered_questions.clear()
        instance._profiles.clear()
        instance._completed = None
        instance._progress = None
        instance.save()

