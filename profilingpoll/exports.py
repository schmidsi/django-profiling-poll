# export functions for use with django-excel-export
# https://bitbucket.org/ljean/django-excel-export/overview

from models import Walkthrough

def export_walkthroughs(*args):
    for walkthrough in Walkthrough.objects.filter(email__isnull=False):
        yield [walkthrough.poll,
               walkthrough.email,
               walkthrough.ip,
               walkthrough.user_agent,
               walkthrough._completed,
               walkthrough.created,
               walkthrough._progress,
               walkthrough.get_matching_profile()]