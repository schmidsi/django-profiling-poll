from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, RedirectView, FormView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin

from .forms import AnswerForm
from .models import Poll, Question, Walkthrough


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
            given_answer = walkthrough.answers.filter(question=self.object)[0]
            initial.update({'answer' : given_answer.id})

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
            return super(QuestionView, self).get_success_url()


poll_list = SingleRedirectToDetailListView.as_view(
    queryset = Poll.objects.filter(active=True)
)

poll_detail = RedirectToFirstQuestion.as_view()
question = QuestionView.as_view()