from django.conf.urls import patterns, url

urlpatterns = patterns('canonicalizer.views',
    url(
        r'^process_captured_statement/',
        'process_captured_statement',
        name='canonicalizer_process_captured_statement'),

    url(r'^last_statements/(?P<window_length>\d+)/',
        'last_statements',
        name='canonicalizer_last_statements'),

    url(r'^sparkline/(?P<data>.+)/$',
        'sparkline',
        name='canonicalizer_sparkline'),
)
