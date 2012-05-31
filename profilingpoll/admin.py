from django.contrib import admin

from .models import Poll, Question, Answer, Profile, AnswerProfile, Walkthrough, WalkthroughProfile


def inline(model, inline_class=admin.StackedInline, **kwargs):
    kwargs['model'] = model
    return type(model.__class__.__name__ + 'Inline', (inline_class,), kwargs)


admin.site.register(Poll,
    list_display = ('description', 'created', 'modified'),
    inlines = [
        inline(Question, extra=0),
    ]
)

admin.site.register(Question,
    list_display = ('__unicode__', 'poll', 'created', 'modified'),
    list_filter = ('poll',),
    inlines = [
        inline(Answer, extra=4, max_num=4)
    ]
)

admin.site.register(Answer,
    list_display = ('__unicode__', 'question', 'created', 'modified'),
    list_filter = ('question','question__poll'),
    inlines = [
        inline(AnswerProfile, extra=0)
    ]
)

admin.site.register(Profile,
    list_display = ('__unicode__',),
    list_filter = ('answers', 'answers__question', 'answers__question__poll',)
)

admin.site.register(Walkthrough,
    list_display = ('poll', '_completed'),
    list_filter = ('poll',),
    readonly_fields = ('_answered_questions', '_completed', '_profiles'),
    inlines = [
        inline(WalkthroughProfile,
            extra=0,
            max_num=0,
            readonly_fields = ('walkthrough', 'profile', 'quantifier')
        )
    ]
)