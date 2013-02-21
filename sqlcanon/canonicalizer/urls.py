from django.conf.urls import patterns, url

urlpatterns = patterns('canonicalizer.views',
    url(r'^last_statements/(?P<window_length>\d+)/',
        'last_statements',
        name='canonicalizer_last_statements'),

    url(r'^top_queries/(?P<n>\d+)/',
        'top_queries',
        name='canonicalizer_top_queries'),

    url(r'^sparkline/(?P<data>.+)/$',
        'sparkline',
        name='canonicalizer_sparkline'),
)
