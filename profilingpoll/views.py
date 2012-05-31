from django.shortcuts import redirect
from django.views.generic import DetailView, ListView


from .models import Poll


class SingleRedirectToDetailListView(ListView):
    def render_to_response(self, context, **response_kwargs):
        if Poll.objects.filter(active=True).count() == 1:
            return redirect(Poll.objects.filter(active=True)[0])
        else:
            return super(ListView, self).render_to_response(self, context, **response_kwargs)

poll_list = SingleRedirectToDetailListView.as_view(
    queryset = Poll.objects.filter(active=True)
)

poll_detail = DetailView.as_view()
question = DetailView.as_view()