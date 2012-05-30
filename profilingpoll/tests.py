from django.utils import unittest

from .models import Poll, Question, Answer


class CreationTest(unittest.TestCase):
    def test_creation_unprofiled(self):
        poll = Poll.objects.create()
        question1 = poll.questions.create(text='How many lovers did you have')
        answer1_1 = question1.answers.create(text='10')
        answer1_2 = question1.answers.create(text='20')
        self.assertEqual(Poll.objects.all().count(), 1)
        self.assertEqual(question1.answers.all().count(), 2)

    def test_creation_profiled(self):
        