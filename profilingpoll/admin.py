from django.contrib import admin

from .models import Poll, Question, Answer, Profile, AnswerProfile, Walkthrough, WalkthroughProfile


def inline(model, inline_class=admin.StackedInline, **kwargs):
    kwargs['model'] = model
    return type(model.__class__.__name__ + 'Inline', (inline_class,), kwargs)


admin.site.register(Poll,
    list_display = ('title', 'active', 'created', 'modified'),
    list_filter = ('active',),
    prepopulated_fields = {'slug': ('title',)},
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

#admin.site.register(Answer,
#    list_display = ('__unicode__', 'question', 'created', 'modified'),
#    list_filter = ('question','question__poll'),
#    inlines = [
#        inline(AnswerProfile, extra=0)
#    ]
#)

class ProfileAdmin(admin.ModelAdmin):
    class Media:
        js = ('lib/tiny_mce/tiny_mce.js', 'js/tinymce_init.js')

    list_display = ('__unicode__',)
    list_filter = ('answers__question__poll', 'answers__question', 'answers',)
    inlines = [
        inline(AnswerProfile, extra=0)
    ]

admin.site.register(Profile, ProfileAdmin)

admin.site.register(Walkthrough,
    list_display = ('poll', 'email', 'get_matching_profile', '_progress', '_completed', 'created', 'modified', 'ip',
                    'user_agent'),
    list_filter = ('poll',),
    fields = ('poll', '_progress', '_completed', 'email', 'user_agent', 'ip'),
    readonly_fields = ('poll', 'answers', '_answered_questions', '_completed', '_profiles', '_progress', 'email',
                       'ip', 'user_agent'),
    inlines = [
        inline(Walkthrough.answers.through,
            extra=0,
            max_num=0,
            readonly_fields = ('answer',)
        ),
        inline(WalkthroughProfile,
            extra=0,
            max_num=0,
            readonly_fields = ('walkthrough', 'profile', 'quantifier')
        )
    ]
)