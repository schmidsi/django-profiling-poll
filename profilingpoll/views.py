from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, RedirectView, FormView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin

from .forms import AnswerForm
from .models import Poll, Question


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

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.get_object()
        return kwargs


poll_list = SingleRedirectToDetailListView.as_view(
    queryset = Poll.objects.filter(active=True)
)

poll_detail = RedirectToFirstQuestion.as_view()
question = QuestionView.as_view()