from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView, ListView, RedirectView


from .models import Poll


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


poll_list = SingleRedirectToDetailListView.as_view(
    queryset = Poll.objects.filter(active=True)
)

poll_detail = RedirectToFirstQuestion.as_view()
question = DetailView.as_view()