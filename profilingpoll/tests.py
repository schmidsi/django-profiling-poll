from django.utils import unittest

from .models import Poll, Question, Answer, Profile, AnswerProfile


class CreationTest(unittest.TestCase):
    def test_creation_unprofiled(self):
        Poll.objects.all().delete()
        poll = Poll.objects.create()
        question1 = poll.questions.create(text='How many lovers did you have')
        answer1_1 = question1.answers.create(text='10')
        answer1_2 = question1.answers.create(text='20')
        self.assertEqual(Poll.objects.all().count(), 1)
        self.assertEqual(question1.answers.all().count(), 2)

    def test_creation_profiled(self):
        Poll.objects.all().delete()
        poll = Poll.objects.create()
        profile1 = Profile.objects.create(text='Superlover')
        profile2 = Profile.objects.create(text='Virgin')
        question1 = poll.questions.create(text='How many lovers did you have')
        answer1_1 = question1.answers.create(text='10')
        answerprofile1_1 = answer1_1.answerprofiles.create(profile=profile1, quantifier=10)
        answer1_2 = question1.answers.create(text='0')
        answerprofile1_2 = answer1_2.answerprofiles.create(profile=profile2, quantifier=20)
        self.assertEqual(Poll.objects.all().count(), 1)
        self.assertEqual(question1.answers.all().count(), 2)
        self.assertEqual(answerprofile1_1.quantifier, 10)
        self.assertEqual(answerprofile1_2.quantifier, 20)