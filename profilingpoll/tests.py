from django.test import TestCase

from .models import Poll, Question, Answer, Profile, AnswerProfile, Walkthrough
from .forms import AnswerForm


class CreationTest(TestCase):
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


class WalkthroughTest(TestCase):
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

    def test_double_answer(self):
        walkthrough = self.poll1.walkthroughs.create()
        walkthrough.answers.add(self.answer1_1)
        self.assertTrue(self.question1 in walkthrough._answered_questions.all())
        walkthrough.answers.add(self.answer1_2)
        self.assertTrue(self.question1 in walkthrough._answered_questions.all())
        self.assertEqual(walkthrough.answers.all().count(), 1)
        self.assertTrue(self.answer1_2 in walkthrough.answers.all())
        self.assertFalse(self.answer1_1 in walkthrough.answers.all())
        walkthrough.answers.remove(self.answer1_2)
        self.assertFalse(self.question1 in walkthrough._answered_questions.all())


class FormTest(TestCase):
    fixtures = ['test.json',]

    def test_save_one_answer(self):
        self.question = Question.objects.get(id=1)
        self.form = AnswerForm({'answer' : 1}, question=self.question)
        self.assertEqual(len(self.form.fields['answer'].choices),
                         len(self.question.answers.all())
        )
        self.assertTrue(self.form.is_valid())


class RequestWalkthroughTest(TestCase):
    fixtures = ['test.json',]
    urls = 'profilingpoll.urls'

    def test_redirect_to_first_active_poll(self):
        response = self.client.get('/', follow=True)

        # request to / should redirect to the first acitve poll and then to the first question in this poll
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.request['PATH_INFO'], '/bester-kurs/1/')

        # only show the first question should not create a walkthrough
        self.assertEqual(response.context['walkthrough'], None)

    def test_answer_the_questions(self):
        # send the form empty; should display errors and also not create a walkthrough
        response = self.client.post('/bester-kurs/1/', {})
        self.assertEqual(response.context['object'].id, 1)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(response.context['walkthrough'], None)

        # really answer the question
        response = self.client.post('/bester-kurs/1/', {'answer' : 1})
        self.assertEqual(response.status_code, 302)
        self.assertIsInstance(self.client.session['current_walkthrough'], Walkthrough)

    def test_answer_a_question_2times(self):
        self.client.post('/bester-kurs/1/', {'answer' : 1})
        self.client.post('/bester-kurs/1/', {'answer' : 2})
        self.assertIsInstance(self.client.session['current_walkthrough'], Walkthrough)

        # be sure, only the last answer is in the walkthrough
        walkthrough = self.client.session['current_walkthrough']
        self.assertEqual(walkthrough.answers.all().count(), 1)

        # as long as the walkthrough is active, it should prefill the question form
        response = self.client.get('/bester-kurs/1/')
        self.assertEqual(response.context['form'].initial, {'answer' : 2})

    def test_walkthrough_and_restart(self):
        """
        a full walkthrough will show the results page with the matching profile
        and moves the completed walkthrough to session['completed_walkthroughs']
        """
        self.client.post('/bester-kurs/1/', {'answer' : 1})
        response = self.client.post('/bester-kurs/3/', {'answer' : 10}, follow=True)

        # The current walkthrough is sent as context
        self.assertTrue(response.context['walkthrough'])
        #self.assertTrue(response.context['walkthrough'].completed)

        # But removed from the session.
        self.assertEqual(self.client.session['current_walkthrough'], None)

        # A restart is empty
        response = self.client.get('/bester-kurs/1/')
        self.assertEqual(response.context['form'].initial, {'answer' : 2})

    def test_enforce_workflow(self):
        """
        A poll has to start with the first question in it. If a question is opened, with unanswered
        preceding questions, redirect to the first unanswered question
        """
        self.assertNotIn('current_walkthrough', self.client.session)
        response = self.client.get('/bester-kurs/3/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/bester-kurs/1/')

        # directly open finish also

        # TODO: Really test this behaviour




