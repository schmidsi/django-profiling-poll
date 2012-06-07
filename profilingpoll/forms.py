from django import forms
from django.core.exceptions import ImproperlyConfigured

class AnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        try:
            self.question = kwargs.pop('question')
        except KeyError:
            raise ImproperlyConfigured('AnswerForm need "question" as kwarg')
        super(AnswerForm, self).__init__(*args, **kwargs)

        self.fields['answer'] = forms.ChoiceField(
            widget=forms.RadioSelect,
            choices=self.question.answers.all().values_list('id', 'text')
        )


class EmailForm(forms.Form):
    email = forms.EmailField(required=False, label="Mail eintragen")
