from django.core import signing
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, RedirectView, FormView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin

from .forms import AnswerForm, EmailForm
from .models import Poll, Question, Walkthrough


class SingleRedirectToDetailListView(ListView):
    def render_to_response(self, context, **response_kwargs):
        if Poll.objects.filter(active=True).count() == 1:
            return redirect(Poll.objects.filter(active=True)[0])
        else:
            return super(ListView, self).render_to_response(context, **response_kwargs)


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

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()

        try:
            form = self.get_form(form_class)
            return self.render_to_response(self.get_context_data(form=form))
        except Question.DoesNotExist:
            return redirect('profilingpoll_poll_list')

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
                given_answer = walkthrough.answers.filter(question=self.object)[0]
                initial.update({'answer': given_answer.id})
            except IndexError:
                pass

        return initial

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.get_object()
        kwargs['walkthrough'] = self.request.session.get('current_walkthrough', None)
        return kwargs

    def form_valid(self, form):
        if not self.request.session.get('current_walkthrough', None):
            self.request.session['current_walkthrough'] = Walkthrough.objects.create(
                poll=self.object.poll,
                ip=self.request.META['REMOTE_ADDR'] or None,
                user_agent=self.request.META['HTTP_USER_AGENT'] or None
            )

        answer = self.object.answers.get(id=form.cleaned_data['answer'])
        self.request.session['current_walkthrough'].answers.add(answer)
        self.request.session.modified = True

        return super(QuestionView, self).form_valid(form)

    def get_success_url(self):
        next = self.get_object().next()

        if next != None:
            return next.get_absolute_url()
        else:
            return reverse('profilingpoll_get_email', kwargs={'slug': self.object.poll.slug})

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
        if self.request.session.get('current_walkthrough', None):
            if not self.request.session.get('completed_walkthroughs', None):
                self.request.session['completed_walkthroughs'] = []
            self.request.session['completed_walkthroughs'].append(self.request.session['current_walkthrough'])
            self.request.session['current_walkthrough'] = None
            self.request.session.modified = True

        return super(DetailView, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        return get_object_or_404(queryset, id=signing.loads(self.kwargs['hash']))


class EmailView(FormView, SingleObjectTemplateResponseMixin, SingleObjectMixin):
    form_class = EmailForm
    model = Poll
    template_name = 'profilingpoll/poll_finished.html'

    @property
    def object(self):
        return self.get_object()

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return queryset.get(**self.kwargs)

    def form_valid(self, form):
        walkthrough = self.request.session.get('current_walkthrough', None)
        first_question = self.get_object().get_first_question()

        if not walkthrough:
            return redirect(first_question)

        # somehow, the session walkthrough differs from the database walkthrough. so get it proper
        walkthrough = Walkthrough.objects.get(id=walkthrough.id)

        if not walkthrough.completed:
            return redirect(walkthrough.get_next_question())

        if form.cleaned_data['email']:
            walkthrough.email = form.cleaned_data['email']
            walkthrough.save()
        self.request.session['current_walkthrough'] = walkthrough

        return super(EmailView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.get_object()
        kwargs['walkthrough'] = self.request.session.get('current_walkthrough', None)
        return kwargs

    def get_success_url(self):
        walkthrough = self.request.session.get('current_walkthrough')
        return walkthrough.get_absolute_url()

    def render_to_response(self, context, **response_kwargs):
        walkthrough = self.request.session.get('current_walkthrough', None)
        first_question = self.get_object().get_first_question()

        if not walkthrough:
            return redirect(first_question)

        # somehow, the session walkthrough differs from the database walkthrough. so get it proper
        walkthrough = Walkthrough.objects.get(id=walkthrough.id)

        if not walkthrough.completed:
            next = walkthrough.get_next_question()
            
            # get_next_question double tests, if the walkthrough is completed and sets it, if needed.
            if next:
                return redirect(next)

        return super(EmailView, self).render_to_response(context, **response_kwargs)


poll_list = SingleRedirectToDetailListView.as_view(
    queryset=Poll.objects.filter(active=True)
)

get_email = EmailView.as_view()
poll_detail = RedirectToFirstQuestion.as_view()
question = QuestionView.as_view()
result = ResultView.as_view()