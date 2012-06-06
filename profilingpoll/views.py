from django.core import signing
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, RedirectView, FormView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin

from .forms import AnswerForm
from .models import Poll, Question, Walkthrough, Answer


class SingleRedirectToDetailListView(ListView):
    def render_to_response(self, context, **response_kwargs):
        if Poll.objects.filter(active=True).count() == 1:
            return redirect(Poll.objects.filter(active=True)[0])
        else:
            return super(ListView, self).render_to_response(self, context, **response_kwargs)


class RedirectToFirstQuestion(RedirectView):
    def get_redirect_url(self, **kwargs):
        poll = get_object_or_404(Poll, slug=kwargs['slug'])
        return poll.questions.all()[0].get_absolute_url()


class QuestionView(FormView, SingleObjectTemplateResponseMixin, SingleObjectMixin):
    form_class = AnswerForm
    model = Question

    @property
    def object(self):
        return self.get_object()

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return queryset.get(**self.kwargs)

    def get_form_kwargs(self):
        kwargs = super(QuestionView, self).get_form_kwargs()
        kwargs['question'] = self.get_object()
        return kwargs

    def get_initial(self):
        initial = self.initial.copy()
        walkthrough = self.request.session.get('current_walkthrough', None)

        if walkthrough and self.object in walkthrough.answered_questions:
            try:
                given_answer = walkthrough.answers.filter(question=self.object).get()
                initial.update({'answer' : given_answer.id})
            except Answer.DoesNotExist:
                pass

        return initial

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.get_object()
        kwargs['walkthrough'] = self.request.session.get('current_walkthrough', None)
        return kwargs

    def form_valid(self, form):
        if not self.request.session.get('current_walkthrough', None):
            self.request.session['current_walkthrough'] = Walkthrough.objects.create(poll=self.object.poll)

        answer = self.object.answers.get(id=form.cleaned_data['answer'])
        self.request.session['current_walkthrough'].answers.add(answer)

        return super(QuestionView, self).form_valid(form)

    def get_success_url(self):
        next = self.get_object().next()

        if next != None:
            return next.get_absolute_url()
        else:
            walkthrough = self.request.session.get('current_walkthrough')
            return reverse('profilingpoll_result', kwargs={'hash' : signing.dumps(walkthrough.id) })

    def render_to_response(self, context, **response_kwargs):
        """
        Redirect, if this question can not be answered now. E.g. outside workflow.
        """
        walkthrough = self.request.session.get('current_walkthrough', None)
        first_question = self.object.poll.get_first_question()

        # first case: if there is no walkthrough in the session, this has to be the first question
        if not walkthrough:
            if self.object != first_question:
                return redirect(first_question)
        else:
            next_question = walkthrough.get_next_question()

            # second case, the answer isn't answered and not the next answer
            if next_question and not self.object.question_answered(walkthrough) and not self.object == next_question:
                return redirect(next_question)

        # else: Do it
        return super(QuestionView, self).render_to_response(context, **response_kwargs)


class ResultView(DetailView):
    model = Walkthrough

    def get(self, request, *args, **kwargs):
        if not self.request.session.get('current_walkthrough', None):
            return redirect(self.get_object().poll.get_first_question())

        if not self.request.session.get('completed_walkthroughs', None):
            self.request.session['completed_walkthroughs'] = []
        self.request.session['completed_walkthroughs'].append(self.request.session['current_walkthrough'])
        self.request.session['current_walkthrough'] = None

        return super(DetailView, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        return get_object_or_404(queryset, id=signing.loads(self.kwargs['hash']))


poll_list = SingleRedirectToDetailListView.as_view(
    queryset = Poll.objects.filter(active=True)
)

poll_detail = RedirectToFirstQuestion.as_view()
question = QuestionView.as_view()
result = ResultView.as_view()