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


class WalkthroughTest(unittest.TestCase):
    def setUp(self):
        Poll.objects.all().delete()
        self.poll1 = Poll.objects.create()
        self.profile1 = Profile.objects.create(text='Superlover')
        self.profile2 = Profile.objects.create(text='Virgin')

        self.question1 = self.poll1.questions.create(text='How many lovers did you have')
        self.answer1_1 = self.question1.answers.create(text='10')
        self.answer1_1.answerprofiles.create(profile=self.profile1, quantifier=10)
        self.answer1_2 = self.question1.answers.create(text='0')
        self.answer1_2.answerprofiles.create(profile=self.profile2, quantifier=20)

        self.question2 = self.poll1.questions.create(text='At which age did you have your first time')
        self.answer2_1 = self.question2.answers.create(text='16')
        self.answer2_1.answerprofiles.create(profile=self.profile1, quantifier=10)
        self.answer2_2 = self.question2.answers.create(text='Never')
        self.answer2_2.answerprofiles.create(profile=self.profile2, quantifier=25)

    def test_simplewalkthrough(self):
        walkthrough = self.poll1.walkthroughs.create()
        walkthrough.answers.add(self.answer1_1)
        self.assertFalse(walkthrough.completed)
        self.assertEqual(walkthrough.get_matching_profile(), self.profile1)
        walkthrough.answers.add(self.answer2_2)
        self.assertTrue(walkthrough.completed)
        self.assertEqual(walkthrough.get_matching_profile(), self.profile2)
        self.assertEqual(walkthrough.walkthroughprofiles.get(profile=self.profile2).quantifier, 25)
        walkthrough.answers.remove(self.answer1_1)
        self.assertEqual(walkthrough.walkthroughprofiles.get(profile=self.profile1).quantifier, 0)
        walkthrough.answers.add(self.answer1_1)
        self.assertEqual(walkthrough.walkthroughprofiles.get(profile=self.profile1).quantifier, 10)
        walkthrough.answers.add(self.answer1_1)
        self.assertEqual(walkthrough.walkthroughprofiles.get(profile=self.profile1).quantifier, 10)
        walkthrough.answers.clear()
        self.assertEqual(walkthrough.answers.all().count(), 0)
        self.assertEqual(walkthrough._profiles.all().count(), 0)
        self.assertEqual(walkthrough._answered_questions.all().count(), 0)

